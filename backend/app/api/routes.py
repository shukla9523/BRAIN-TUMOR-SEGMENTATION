import os
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks, Query
from fastapi.responses import FileResponse, JSONResponse

from app.core.config import settings
from app.core.errors import NeuroScanError, ModelNotLoadedError, MriValidationError
from app.schemas.mri import (
    HealthResponse,
    ModelInfoResponse,
    UploadResponse,
    SegmentRequest,
    SegmentResponse,
    JobStatusResponse,
    SliceVisualizationResponse
)
from app.services.mri_service import mri_service
from app.services.job_manager import job_manager
from app.services.report_service import generate_pdf_report
from app.ml.inference import inference_service, HAS_TORCH
from app.ml.dataset import generate_synthetic_brain_scan
from app.utils.nifti_io import save_nifti_mask

try:
    import torch
    TORCH_VER = torch.__version__
except Exception:
    TORCH_VER = "Not installed"

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
def health_check():
    """Returns service health, model checkpoint availability, device, and medical disclaimer."""
    return HealthResponse(
        status="healthy",
        model_available=inference_service.is_loaded,
        model_version=settings.VERSION,
        device=str(inference_service.device),
        pytorch_version=TORCH_VER,
        monai_available=False,
        disclaimer=settings.RESEARCH_DISCLAIMER
    )

@router.get("/model-info", response_model=ModelInfoResponse)
def get_model_info():
    """Returns 3D U-Net architectural specifications, expected modalities, and checkpoint status."""
    return ModelInfoResponse(
        architecture=inference_service.architecture,
        version=settings.VERSION,
        expected_modalities=["T1", "T1ce", "T2", "FLAIR"],
        input_spatial_shape=[128, 128, 128],
        label_mapping=settings.LABEL_MAPPING,
        checkpoint_status="Loaded and Ready" if inference_service.is_loaded else "Checkpoint Unavailable (Model Not Trained)",
        checkpoint_path=str(settings.DEFAULT_CHECKPOINT_PATH) if inference_service.is_loaded else None,
        parameters_count=inference_service.model_info.get("parameters_count"),
        training_dataset="BraTS (Brain Tumor Segmentation Challenge)",
        intended_use="Educational & Research Verification Only. Primary clinical diagnosis prohibited."
    )

@router.post("/upload", response_model=UploadResponse)
async def upload_mri(file: UploadFile = File(...)):
    """Validates uploaded .nii or .nii.gz MRI volume and extracts dimensional/spatial metadata."""
    try:
        content = await file.read()
        info = mri_service.save_upload_stream(content, file.filename or "uploaded_scan.nii.gz")
        return UploadResponse(**info)
    except NeuroScanError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected server error during upload: {str(e)}")

def _async_segmentation_task(job_id: str, upload_id: str, selected_modality: str):
    """Executes background segmentation with job manager progress updates."""
    try:
        job_manager.update_job(job_id, status="running", progress=15, message="Validating volume and spatial orientation...")
        # Step 1: Preprocessing
        job_manager.update_job(job_id, progress=35, message="Extracting brain bounding box and z-score normalizing intensities...")
        # Step 2: Inference
        job_manager.update_job(job_id, progress=60, message="Executing 3D U-Net forward pass...")
        result = mri_service.run_segmentation(upload_id=upload_id, selected_modality=selected_modality)
        
        job_manager.update_job(job_id, progress=85, message="Restoring spatial geometry and calculating volumetric metrics...")
        job_manager.update_job(
            job_id,
            status="completed",
            progress=100,
            message="Segmentation complete",
            result_id=result["result_id"]
        )
    except ModelNotLoadedError as e:
        job_manager.update_job(job_id, status="failed", progress=0, message="Failed", error=e.message)
    except Exception as e:
        job_manager.update_job(job_id, status="failed", progress=0, message="Failed", error=str(e))

@router.post("/segment", response_model=SegmentResponse)
def segment_mri(req: SegmentRequest, background_tasks: BackgroundTasks):
    """
    Submits an MRI volume for segmentation.
    If the model checkpoint is unavailable, returns explicit HTTP 503 rather than fabricating results.
    """
    if not inference_service.is_loaded:
        raise HTTPException(
            status_code=503,
            detail=(
                "Model checkpoint unavailable ('unet3d_brats_best.pt' not found). "
                "Per clinical safety requirements, NeuroScan AI never fabricates predictions. "
                "Please run the Google Colab training notebook or training script to generate a trained checkpoint."
            )
        )

    # Check upload exists
    upload_info = mri_service.get_upload_info(req.upload_id)
    if not upload_info:
        raise HTTPException(status_code=404, detail=f"Upload ID '{req.upload_id}' not found.")

    job_id = job_manager.create_job(initial_message="Segmentation job queued")
    background_tasks.add_task(
        _async_segmentation_task,
        job_id=job_id,
        upload_id=req.upload_id,
        selected_modality=req.selected_modality or "FLAIR"
    )

    return SegmentResponse(
        job_id=job_id,
        result_id="",
        status="pending",
        message="Segmentation task queued for background processing."
    )

@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: str):
    """Polls status, progress percentage, and errors for a running segmentation job."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    return JobStatusResponse(**job)

@router.get("/results/{result_id}")
def get_result(result_id: str):
    """Returns validated segmentation result metadata, volumetric measurements, and quality warnings."""
    res = mri_service.get_result_info(result_id)
    if not res:
        raise HTTPException(status_code=404, detail=f"Result '{result_id}' not found.")
    return res

@router.get("/results/{result_id}/mask")
def download_mask(result_id: str):
    """Downloads the predicted 3D segmentation mask as a compressed NIfTI (.nii.gz) file."""
    res = mri_service.get_result_info(result_id)
    if not res or not Path(res["mask_path"]).exists():
        raise HTTPException(status_code=404, detail="Segmentation mask file not found.")
    return FileResponse(
        path=res["mask_path"],
        filename=f"neuroscan_segmentation_{result_id[:8]}.nii.gz",
        media_type="application/gzip"
    )

@router.get("/results/{result_id}/report")
def download_report(result_id: str):
    """Generates and serves a research PDF summary report."""
    res = mri_service.get_result_info(result_id)
    if not res:
        raise HTTPException(status_code=404, detail=f"Result '{result_id}' not found.")

    report_pdf_path = settings.REPORT_DIR / f"report_{result_id}.pdf"
    if not report_pdf_path.exists():
        try:
            generate_pdf_report(res, str(report_pdf_path))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to compile PDF report: {str(e)}")

    return FileResponse(
        path=str(report_pdf_path),
        filename=f"NeuroScan_Research_Report_{result_id[:8]}.pdf",
        media_type="application/pdf"
    )

@router.get("/results/{result_id}/slice/{index}", response_model=SliceVisualizationResponse)
def get_result_slice(
    result_id: str,
    index: int,
    plane: str = Query("axial", pattern="^(axial|coronal|sagittal)$"),
    alpha: float = Query(0.65, ge=0.0, le=1.0)
):
    """Returns Base64 encoded slice and segmentation overlay for the requested slice and viewing plane."""
    try:
        rendered = mri_service.render_slice(identifier=result_id, plane=plane, slice_index=index, alpha=alpha)
        return SliceVisualizationResponse(**rendered)
    except NeuroScanError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/uploads/{upload_id}/slice/{index}", response_model=SliceVisualizationResponse)
def get_upload_slice(
    upload_id: str,
    index: int,
    plane: str = Query("axial", pattern="^(axial|coronal|sagittal)$")
):
    """Returns Base64 encoded slice for previewing an uploaded scan prior to running segmentation."""
    try:
        rendered = mri_service.render_slice(identifier=upload_id, plane=plane, slice_index=index)
        return SliceVisualizationResponse(**rendered)
    except NeuroScanError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics")
def get_evaluation_metrics():
    """Returns actual trained model evaluation metrics and validation curves from disk."""
    metrics_path = settings.EVALUATION_METRICS_PATH
    if metrics_path.exists():
        try:
            data = json.loads(metrics_path.read_text())
            return data
        except Exception:
            pass

    # If no evaluation metrics file has been exported yet
    return {
        "status": "unavailable",
        "message": (
            "No evaluation metrics recorded yet. Metrics will populate once model training "
            "or test set evaluation has completed."
        ),
        "dataset_name": "BraTS 2020 / BraTS 2021 Benchmark",
        "metrics_summary": {
            "WT": {"dice_mean": 0.0, "iou_mean": 0.0, "sensitivity_mean": 0.0, "specificity_mean": 0.0, "hd95_mean_mm": 0.0},
            "TC": {"dice_mean": 0.0, "iou_mean": 0.0, "sensitivity_mean": 0.0, "specificity_mean": 0.0, "hd95_mean_mm": 0.0},
            "ET": {"dice_mean": 0.0, "iou_mean": 0.0, "sensitivity_mean": 0.0, "specificity_mean": 0.0, "hd95_mean_mm": 0.0}
        },
        "history": []
    }

@router.get("/sample-scans")
def list_sample_scans():
    """Returns list of pre-packaged research sample scans available for immediate exploration."""
    samples = []
    for f in settings.SAMPLE_DIR.glob("*.nii*"):
        samples.append({
            "sample_id": f.stem.replace(".nii", ""),
            "filename": f.name,
            "description": "Synthetic Multimodal BraTS Glioblastoma Phantom (128x128x128)" if "phantom" in f.name else "Clinical Research Sample",
            "size_bytes": f.stat().st_size
        })
    return {"samples": samples}

@router.post("/sample-scans/load/{sample_id}")
def load_sample_scan(sample_id: str):
    """Loads a sample scan into an active upload session."""
    matches = list(settings.SAMPLE_DIR.glob(f"*{sample_id}*.nii*"))
    if not matches:
        raise HTTPException(status_code=404, detail=f"Sample scan '{sample_id}' not found.")
    target_file = matches[0]
    content = target_file.read_bytes()
    upload_info = mri_service.save_upload_stream(content, target_file.name)
    return UploadResponse(**upload_info)
