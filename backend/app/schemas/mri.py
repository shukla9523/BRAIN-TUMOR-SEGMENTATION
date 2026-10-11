from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class HealthResponse(BaseModel):
    status: str = Field(..., description="Service status")
    model_available: bool = Field(..., description="Whether a trained model checkpoint is loaded")
    model_version: str = Field(..., description="Software version")
    device: str = Field(..., description="Compute backend device")
    pytorch_version: str
    monai_available: bool
    disclaimer: str

class ModelInfoResponse(BaseModel):
    architecture: str = Field(..., description="Model architecture")
    version: str = "1.0.0"
    expected_modalities: List[str] = Field(
        default=["T1", "T1ce", "T2", "FLAIR"],
        description="MRI modalities expected by the 4-channel input architecture"
    )
    input_spatial_shape: List[int] = Field(default=[128, 128, 128], description="Resampled patch or volume shape (D, H, W)")
    label_mapping: Dict[int, str]
    evaluation_subregions: Dict[str, str] = {
        "WT": "Whole Tumor (Labels 1 + 2 + 4)",
        "TC": "Tumor Core (Labels 1 + 4)",
        "ET": "Enhancing Tumor (Label 4)"
    }
    checkpoint_status: str
    checkpoint_path: Optional[str] = None
    parameters_count: Optional[int] = None
    training_dataset: str = "BraTS (Brain Tumor Segmentation Challenge)"
    intended_use: str = "Research & Academic Demonstration only. Not for clinical diagnosis."

class ModalityDetected(BaseModel):
    modality: str
    filename: str
    dimensions: List[int]
    voxel_spacing: List[float]

class UploadResponse(BaseModel):
    upload_id: str
    filename: str
    file_size_bytes: int
    dimensions: List[int]
    voxel_spacing: List[float]
    orientation: str
    modalities_detected: List[str]
    total_slices_axial: int
    total_slices_coronal: int
    total_slices_sagittal: int
    warnings: List[str] = []
    created_at: str

class QuantitativeRegionMetrics(BaseModel):
    region_id: str
    region_name: str
    labels_included: List[int]
    volume_cm3: float
    voxel_count: int
    percentage_of_brain: Optional[float] = None
    slice_extent_axial: List[int]
    slice_extent_coronal: List[int]
    slice_extent_sagittal: List[int]
    connected_components: int
    color_hex: str

class QuantitativeReport(BaseModel):
    total_tumor_volume_cm3: float
    regions: List[QuantitativeRegionMetrics]
    voxel_spacing_mm: List[float]
    dimensions: List[int]
    processing_time_seconds: float
    quality_warnings: List[str] = []
    disclaimer: str

class SegmentRequest(BaseModel):
    upload_id: str
    model_name: Optional[str] = "3d_unet_brats"
    selected_modality: Optional[str] = "FLAIR"
    run_quantitative_analysis: bool = True

class SegmentResponse(BaseModel):
    job_id: str
    result_id: str
    status: str
    message: str
    quantitative_report: Optional[QuantitativeReport] = None

class JobStatusResponse(BaseModel):
    job_id: str
    status: str  # pending, running, completed, failed
    progress: int  # 0 to 100
    message: str
    result_id: Optional[str] = None
    error: Optional[str] = None

class SliceVisualizationResponse(BaseModel):
    result_id: str
    slice_index: int
    plane: str  # axial, coronal, sagittal
    width: int
    height: int
    image_base64: str
    mask_base64: Optional[str] = None
    overlay_base64: Optional[str] = None
    has_tumor: bool
    subregion_counts: Dict[str, int]

class EvaluationMetricsData(BaseModel):
    dataset_name: str
    test_cases_count: int
    evaluation_date: str
    metrics_summary: Dict[str, Dict[str, float]] # e.g. "WT": {"dice": 0.88, "iou": 0.79, "sensitivity": 0.89, "specificity": 0.99, "hd95_mm": 5.4}
    epoch_history: List[Dict[str, Any]]
    held_out_comparison: Dict[str, Any]
    limitations_note: str
