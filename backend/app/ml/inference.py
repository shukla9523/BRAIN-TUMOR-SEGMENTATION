import time
import numpy as np
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List

try:
    import torch
    import torch.nn.functional as F
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

from app.core.config import settings
from app.core.errors import ModelNotLoadedError, InferenceError
from app.ml.model import create_model, count_parameters
from app.ml.preprocessing import (
    normalize_brain_intensities,
    extract_brain_bounding_box,
    resample_volume,
    restore_mask_to_original
)

class ModelInferenceService:
    """
    Manages loading the 3D U-Net checkpoint and running safe volumetric inference.
    """
    def __init__(self, checkpoint_path: Optional[Path] = None, device: Optional[str] = None):
        self.checkpoint_path = checkpoint_path or settings.DEFAULT_CHECKPOINT_PATH
        self.device = device or ("cuda" if (HAS_TORCH and torch.cuda.is_available()) else "cpu")
        self.model = None
        self.architecture = "3D U-Net (BraTS Configuration)"
        self.model_info = {}
        self.is_loaded = False

        self._try_load_model()

    def _try_load_model(self):
        """Attempts to load model weights from checkpoint if file exists."""
        if not HAS_TORCH:
            self.model_info = {"status": "PyTorch not installed in environment"}
            self.is_loaded = False
            return

        if not self.checkpoint_path.exists():
            self.model_info = {
                "status": "Checkpoint not found",
                "path": str(self.checkpoint_path),
                "message": "Model checkpoint unavailable. Please train the model using the provided Google Colab notebook."
            }
            self.is_loaded = False
            return

        try:
            try:
                checkpoint = torch.load(str(self.checkpoint_path), map_location=self.device, weights_only=False)
            except TypeError:
                checkpoint = torch.load(str(self.checkpoint_path), map_location=self.device)
            state_dict = checkpoint.get("state_dict", checkpoint)
            arch = checkpoint.get("architecture", "3d_unet")
            in_channels = checkpoint.get("in_channels", 4)
            out_channels = checkpoint.get("out_channels", 4)

            self.model = create_model(
                architecture=arch,
                in_channels=in_channels,
                out_channels=out_channels,
                device=self.device
            )
            self.model.load_state_dict(state_dict)
            self.model.eval()
            self.is_loaded = True
            self.architecture = "3D Attention U-Net" if "attention" in arch.lower() else "3D U-Net"
            self.model_info = {
                "status": "Loaded",
                "checkpoint_path": str(self.checkpoint_path),
                "device": self.device,
                "parameters_count": count_parameters(self.model),
                "epoch": checkpoint.get("epoch", "unknown"),
                "best_val_dice": checkpoint.get("best_dice", "unknown")
            }
        except Exception as e:
            self.is_loaded = False
            self.model_info = {
                "status": "Failed to load checkpoint",
                "error": str(e)
            }

    def predict(
        self,
        mri_volume: np.ndarray,
        voxel_spacing: List[float],
        modalities_data: Optional[Dict[str, np.ndarray]] = None
    ) -> Tuple[np.ndarray, float, List[str]]:
        """
        Runs 3D segmentation on input volume.
        If only 1 modality is supplied (e.g. FLAIR or T1ce), repeats across 4 channels or handles single-channel.
        Returns:
            (predicted_mask_3d, inference_time_sec, warnings)
        """
        if not self.is_loaded or self.model is None:
            raise ModelNotLoadedError(
                "Trained model checkpoint is unavailable. Please run training with Google Colab "
                "or place 'unet3d_brats_best.pt' inside the models/ directory."
            )

        start_time = time.time()
        warnings = []
        orig_shape = mri_volume.shape

        # 1. Prepare 4 channels: T1, T1ce, T2, FLAIR
        if modalities_data and len(modalities_data) >= 4:
            channels = [modalities_data[m] for m in ["T1", "T1ce", "T2", "FLAIR"]]
            img_4d = np.stack(channels, axis=0)
        else:
            warnings.append("Single modality provided; replicated across channels for 4-channel model inference.")
            img_4d = np.stack([mri_volume, mri_volume, mri_volume, mri_volume], axis=0)

        # 2. Preprocess: brain bounding box & normalize
        # Extract bbox based on primary modality
        bbox = extract_brain_bounding_box(img_4d[0], margin=4)
        cropped_channels = []
        for c in range(img_4d.shape[0]):
            c_cropped = img_4d[c][bbox]
            c_norm = normalize_brain_intensities(c_cropped)
            c_resampled = resample_volume(c_norm, (128, 128, 128), is_mask=False)
            cropped_channels.append(c_resampled)

        input_tensor = np.stack(cropped_channels, axis=0)[np.newaxis, ...]  # (1, 4, 128, 128, 128)
        input_torch = torch.from_numpy(input_tensor).to(self.device).float()

        # 3. Model forward pass
        with torch.no_grad():
            logits = self.model(input_torch)
            # Output shape: (1, 4, 128, 128, 128) -> classes [0: BG, 1: NCR/NET, 2: ED, 3: ET]
            probs = F.softmax(logits, dim=1)
            pred_classes = torch.argmax(probs, dim=1).squeeze(0).cpu().numpy().astype(np.uint8)

        # 4. Map class index 3 to BraTS label 4 (ET)
        pred_brats = np.copy(pred_classes)
        pred_brats[pred_classes == 3] = 4

        # 5. Restore back to original geometry
        restored_mask = restore_mask_to_original(
            pred_mask_resampled=pred_brats,
            original_shape=orig_shape,
            bbox=bbox
        )

        elapsed = float(round(time.time() - start_time, 2))
        return restored_mask, elapsed, warnings

# Singleton instance
inference_service = ModelInferenceService()
