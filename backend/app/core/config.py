import os
from pathlib import Path
from typing import List
from pydantic import ConfigDict
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseModel as BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "NeuroScan AI"
    PROJECT_DESCRIPTION: str = "Research & Educational Brain Tumor Segmentation Platform"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"

    # Base directories
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    STORAGE_DIR: Path = BASE_DIR / "storage"
    UPLOAD_DIR: Path = STORAGE_DIR / "uploads"
    RESULT_DIR: Path = STORAGE_DIR / "results"
    REPORT_DIR: Path = STORAGE_DIR / "reports"
    MODEL_DIR: Path = BASE_DIR.parent / "models"
    SAMPLE_DIR: Path = BASE_DIR.parent / "data" / "samples"

    # Security & Upload constraints
    MAX_UPLOAD_SIZE_MB: int = 350
    ALLOWED_EXTENSIONS: List[str] = [".nii", ".nii.gz", ".dcm", ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"]
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"
    ]

    # Model parameters
    DEFAULT_MODEL_NAME: str = "3d_unet_brats"
    DEFAULT_CHECKPOINT_PATH: Path = MODEL_DIR / "unet3d_brats_best.pt"
    EVALUATION_METRICS_PATH: Path = MODEL_DIR / "evaluation_metrics.json"

    # BraTS conventions
    # Labels in BraTS: 0: Background, 1: Necrotic/Non-enhancing (NCR/NET), 2: Edema (ED), 4: Enhancing tumor (ET)
    # BraTS Evaluation subregions:
    # WT (Whole Tumor): labels 1 + 2 + 4
    # TC (Tumor Core): labels 1 + 4
    # ET (Enhancing Tumor): label 4
    LABEL_MAPPING: dict = {
        0: "Background / Non-tumor Brain Tissue",
        1: "Necrotic Core & Non-Enhancing Tumor (NCR/NET)",
        2: "Peritumoral Edema (ED)",
        4: "GD-Enhancing Tumor (ET)"
    }

    # Research notice
    RESEARCH_DISCLAIMER: str = (
        "NeuroScan AI is an educational and research prototype developed for evaluating "
        "3D deep learning architectures on brain MRI segmentation. It is NOT an FDA-approved "
        "or CE-marked medical device and MUST NOT be used as a primary diagnostic tool. "
        "All measurements are model-derived approximations subject to imaging artifacts "
        "and anatomical variability."
    )

    model_config = ConfigDict(case_sensitive=True, env_file=".env", extra="allow")

settings = Settings()

# Ensure directories exist
for directory in [settings.STORAGE_DIR, settings.UPLOAD_DIR, settings.RESULT_DIR, settings.REPORT_DIR, settings.MODEL_DIR, settings.SAMPLE_DIR]:
    directory.mkdir(parents=True, exist_ok=True)
