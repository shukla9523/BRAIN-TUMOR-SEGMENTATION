import os
import uuid
import time
import json
import shutil
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

from app.core.config import settings
from app.core.errors import MriValidationError, UnsupportedFormatError, FileTooLargeError
from app.utils.nifti_io import load_nifti_volume, save_nifti_mask, get_2d_slice, render_slice_visualization
from app.utils.geometry import analyze_subregions
from app.ml.inference import inference_service

class MriService:
    def __init__(self):
        self._uploads: Dict[str, Dict[str, Any]] = {}
        self._results: Dict[str, Dict[str, Any]] = {}

    def save_upload_stream(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Validates and persists uploaded MRI file."""
        # 1. Extension check
        lower_name = filename.lower()
        if not any(lower_name.endswith(ext) for ext in settings.ALLOWED_EXTENSIONS):
            raise UnsupportedFormatError(f"Unsupported format '{filename}'. Allowed formats: {settings.ALLOWED_EXTENSIONS}")

        # 2. Size limit check
        size_bytes = len(file_content)
        if size_bytes > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
            raise FileTooLargeError(f"File size {size_bytes / (1024*1024):.1f}MB exceeds limit of {settings.MAX_UPLOAD_SIZE_MB}MB")

        upload_id = str(uuid.uuid4())
        upload_dir = settings.UPLOAD_DIR / upload_id
        upload_dir.mkdir(parents=True, exist_ok=True)
        file_path = upload_dir / filename

        with open(file_path, "wb") as f:
            f.write(file_content)

        # 3. Parse and extract metadata
        try:
            data, affine, meta = load_nifti_volume(str(file_path))
        except Exception as e:
            shutil.rmtree(upload_dir, ignore_errors=True)
            raise MriValidationError(f"Invalid MRI data structure: {str(e)}")

        dims = meta["dimensions"]
        zooms = meta["voxel_spacing"]
        warnings = []

        if len(dims) < 3:
            raise MriValidationError(f"Expected at least 3D volume, received shape {dims}")

        # Quality check warnings
        if meta.get("is_2d_photo"):
            warnings.append("2D MRI scan photo converted into 3D volumetric stack (128x128x128) for 3D deep learning segmentation.")
        elif meta.get("is_dicom"):
            warnings.append("DICOM scan converted into 3D volumetric stack for deep learning segmentation.")
        elif any(z <= 0 for z in zooms):
            warnings.append("Voxel spacing <= 0 in NIfTI header; 1.0mm isotropic assumed.")
        elif max(zooms) / min(zooms) > 3.0:
            warnings.append(f"Highly anisotropic spacing: {zooms[0]:.2f} x {zooms[1]:.2f} x {zooms[2]:.2f} mm")

        # Modality detection from filename
        detected_mods = []
        for mod in ["flair", "t1ce", "t1", "t2"]:
            if mod in lower_name:
                detected_mods.append(mod.upper())
        if not detected_mods:
            detected_mods = ["FLAIR (Assumed)"]

        upload_info = {
            "upload_id": upload_id,
            "filename": filename,
            "file_path": str(file_path),
            "file_size_bytes": size_bytes,
            "dimensions": dims,
            "voxel_spacing": zooms,
            "orientation": meta.get("orientation", "RAS"),
            "modalities_detected": detected_mods,
            "total_slices_axial": dims[2] if len(dims) >= 3 else 0,
            "total_slices_coronal": dims[1] if len(dims) >= 3 else 0,
            "total_slices_sagittal": dims[0] if len(dims) >= 3 else 0,
            "warnings": warnings,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        self._uploads[upload_id] = upload_info
        # Save metadata to disk
        (upload_dir / "meta.json").write_text(json.dumps(upload_info, indent=2))
        return upload_info

    def get_upload_info(self, upload_id: str) -> Optional[Dict[str, Any]]:
        if upload_id in self._uploads:
            return self._uploads[upload_id]
        meta_file = settings.UPLOAD_DIR / upload_id / "meta.json"
        if meta_file.exists():
            data = json.loads(meta_file.read_text())
            self._uploads[upload_id] = data
            return data
        return None

    def run_segmentation(self, upload_id: str, selected_modality: str = "FLAIR") -> Dict[str, Any]:
        """Runs the segmentation pipeline on the specified uploaded scan."""
        upload_info = self.get_upload_info(upload_id)
        if not upload_info:
            raise MriValidationError(f"Upload '{upload_id}' not found.")

        file_path = upload_info["file_path"]
        data, affine, meta = load_nifti_volume(file_path)

        # Run inference
        pred_mask, elapsed_sec, model_warnings = inference_service.predict(
            mri_volume=data,
            voxel_spacing=upload_info["voxel_spacing"]
        )

        result_id = str(uuid.uuid4())
        result_dir = settings.RESULT_DIR / result_id
        result_dir.mkdir(parents=True, exist_ok=True)

        mask_file = result_dir / "mask.nii.gz"
        save_nifti_mask(pred_mask, affine, str(mask_file))

        # Quantitative volumetric measurements
        quant_report = analyze_subregions(pred_mask, upload_info["voxel_spacing"])
        all_warnings = upload_info["warnings"] + model_warnings + quant_report["quality_warnings"]
        quant_report["quality_warnings"] = all_warnings
        quant_report["processing_time_seconds"] = elapsed_sec
        quant_report["disclaimer"] = settings.RESEARCH_DISCLAIMER

        result_info = {
            "result_id": result_id,
            "upload_id": upload_id,
            "mask_path": str(mask_file),
            "mri_path": file_path,
            "dimensions": upload_info["dimensions"],
            "voxel_spacing": upload_info["voxel_spacing"],
            "quantitative_report": quant_report,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        self._results[result_id] = result_info
        (result_dir / "report.json").write_text(json.dumps(result_info, indent=2))
        return result_info

    def get_result_info(self, result_id: str) -> Optional[Dict[str, Any]]:
        if result_id in self._results:
            return self._results[result_id]
        report_file = settings.RESULT_DIR / result_id / "report.json"
        if report_file.exists():
            data = json.loads(report_file.read_text())
            self._results[result_id] = data
            return data
        return None

    def render_slice(
        self,
        identifier: str, # upload_id or result_id
        plane: str,
        slice_index: int,
        alpha: float = 0.65
    ) -> Dict[str, Any]:
        """Extracts and renders base MRI slice and segmentation mask overlay."""
        res_info = self.get_result_info(identifier)
        if res_info:
            mri_path = res_info["mri_path"]
            mask_path = res_info["mask_path"]
            mri_data, _, _ = load_nifti_volume(mri_path)
            mask_data, _, _ = load_nifti_volume(mask_path)
            
            mri_2d = get_2d_slice(mri_data, plane, slice_index)
            mask_2d = get_2d_slice(mask_data, plane, slice_index)
            rendered = render_slice_visualization(mri_2d, mask_2d, alpha=alpha)
            rendered["result_id"] = identifier
            rendered["slice_index"] = slice_index
            rendered["plane"] = plane
            return rendered

        up_info = self.get_upload_info(identifier)
        if up_info:
            mri_data, _, _ = load_nifti_volume(up_info["file_path"])
            mri_2d = get_2d_slice(mri_data, plane, slice_index)
            rendered = render_slice_visualization(mri_2d, None, alpha=alpha)
            rendered["result_id"] = identifier
            rendered["slice_index"] = slice_index
            rendered["plane"] = plane
            return rendered

        raise MriValidationError(f"Scan or result not found for id '{identifier}'")

mri_service = MriService()
