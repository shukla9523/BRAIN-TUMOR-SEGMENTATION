import numpy as np
from typing import Tuple, Dict, Any, Optional, List

try:
    import torch
    import torch.nn.functional as F
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

try:
    from scipy import ndimage
    HAS_SCIPY_NDIMAGE = True
except Exception:
    HAS_SCIPY_NDIMAGE = False

def normalize_brain_intensities(volume: np.ndarray, clip_percentiles: Tuple[float, float] = (1.0, 99.0)) -> np.ndarray:
    """
    Applies standard MRI brain intensity normalization:
    1. Extracts non-zero foreground brain voxels.
    2. Clips intensity to [p_low, p_high] percentiles to eliminate scanner spikes.
    3. Performs z-score normalization on the foreground voxels (zero mean, unit variance).
    4. Retains zero for background air.
    """
    vol = volume.astype(np.float32)
    mask = vol > 0

    if not np.any(mask):
        return vol

    fg_values = vol[mask]
    p_low, p_high = np.percentile(fg_values, clip_percentiles)
    clipped_fg = np.clip(fg_values, p_low, p_high)

    mean_val = float(np.mean(clipped_fg))
    std_val = float(np.std(clipped_fg))
    if std_val < 1e-6:
        std_val = 1.0

    normalized_vol = np.zeros_like(vol)
    normalized_vol[mask] = (clipped_fg - mean_val) / std_val
    return normalized_vol

def extract_brain_bounding_box(volume: np.ndarray, margin: int = 4) -> Tuple[slice, slice, slice]:
    """
    Computes 3D bounding box enclosing non-zero brain tissue with an optional padding margin.
    """
    mask = volume > 0
    if not np.any(mask):
        return slice(0, volume.shape[0]), slice(0, volume.shape[1]), slice(0, volume.shape[2])

    indices = np.where(mask)
    x_min = max(0, int(indices[0].min()) - margin)
    x_max = min(volume.shape[0], int(indices[0].max()) + 1 + margin)

    y_min = max(0, int(indices[1].min()) - margin)
    y_max = min(volume.shape[1], int(indices[1].max()) + 1 + margin)

    z_min = max(0, int(indices[2].min()) - margin)
    z_max = min(volume.shape[2], int(indices[2].max()) + 1 + margin)

    return slice(x_min, x_max), slice(y_min, y_max), slice(z_min, z_max)

def resample_volume(
    volume: np.ndarray,
    target_shape: Tuple[int, int, int],
    is_mask: bool = False
) -> np.ndarray:
    """
    Resamples a 3D volume to a target spatial grid size.
    Uses PyTorch 3D interpolation (trilinear for images, nearest-neighbor for masks)
    with fallback to scipy.ndimage.zoom if available.
    """
    current_shape = volume.shape
    if current_shape == target_shape:
        return volume

    if HAS_TORCH:
        mode = "nearest" if is_mask else "trilinear"
        align_corners = None if is_mask else True
        tensor = torch.from_numpy(volume.astype(np.float32)).unsqueeze(0).unsqueeze(0)
        resampled_tensor = F.interpolate(
            tensor,
            size=target_shape,
            mode=mode,
            align_corners=align_corners
        )
        resampled = resampled_tensor.squeeze(0).squeeze(0).numpy()
        return resampled.astype(volume.dtype)

    if HAS_SCIPY_NDIMAGE:
        zoom_factors = [target_shape[i] / current_shape[i] for i in range(3)]
        order = 0 if is_mask else 1
        return ndimage.zoom(volume, zoom_factors, order=order)

    # Simple slice subsampling fallback
    step_x = max(1, current_shape[0] // target_shape[0])
    step_y = max(1, current_shape[1] // target_shape[1])
    step_z = max(1, current_shape[2] // target_shape[2])
    return volume[::step_x, ::step_y, ::step_z][:target_shape[0], :target_shape[1], :target_shape[2]]

def restore_mask_to_original(
    pred_mask_resampled: np.ndarray,
    original_shape: Tuple[int, int, int],
    bbox: Optional[Tuple[slice, slice, slice]] = None
) -> np.ndarray:
    """
    Restores predicted mask from resampled/cropped grid back to original image geometry.
    Uses nearest-neighbor interpolation to ensure label integer integrity.
    """
    if bbox is not None:
        bbox_shape = (
            bbox[0].stop - bbox[0].start,
            bbox[1].stop - bbox[1].start,
            bbox[2].stop - bbox[2].start
        )
        pred_bbox = resample_volume(pred_mask_resampled, bbox_shape, is_mask=True)
        full_mask = np.zeros(original_shape, dtype=np.uint8)
        full_mask[bbox] = pred_bbox.astype(np.uint8)
        return full_mask
    else:
        restored = resample_volume(pred_mask_resampled, original_shape, is_mask=True)
        return restored.astype(np.uint8)

def convert_brats_labels_to_standard(mask: np.ndarray, dataset_version: str = "brats2020") -> np.ndarray:
    """
    Ensures mask labels conform to BraTS standard:
    0: Background
    1: Necrotic & Non-Enhancing (NCR/NET)
    2: Edema (ED)
    4: Enhancing Tumor (ET)
    """
    std_mask = np.copy(mask)
    if dataset_version.lower() == "brats2023":
        std_mask[mask == 3] = 4
    return std_mask.astype(np.uint8)

def convert_multiclass_to_brats_channels(pred_logits_or_mask: np.ndarray) -> Dict[str, np.ndarray]:
    """
    Extracts clinical evaluation binary masks:
    - WT (Whole Tumor): labels 1, 2, 4
    - TC (Tumor Core): labels 1, 4
    - ET (Enhancing Tumor): label 4
    """
    mask = pred_logits_or_mask
    wt = np.isin(mask, [1, 2, 4]).astype(np.uint8)
    tc = np.isin(mask, [1, 4]).astype(np.uint8)
    et = (mask == 4).astype(np.uint8)
    return {"WT": wt, "TC": tc, "ET": et}
