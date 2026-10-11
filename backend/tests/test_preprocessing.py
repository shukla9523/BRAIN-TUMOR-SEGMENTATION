import pytest
import numpy as np
from app.ml.preprocessing import (
    normalize_brain_intensities,
    extract_brain_bounding_box,
    resample_volume,
    restore_mask_to_original,
    convert_brats_labels_to_standard
)

def test_normalize_brain_intensities():
    """Verify non-zero foreground voxels have zero mean and unit variance after z-score."""
    import torch
    volume = np.zeros((30, 30, 30), dtype=np.float32)
    volume[5:25, 5:25, 5:25] = (torch.rand(20, 20, 20) * 400.0 + 100.0).numpy()

    norm = normalize_brain_intensities(volume)

    # Background must remain exactly 0
    assert norm[0, 0, 0] == 0.0

    # Foreground should have mean close to 0 and std close to 1
    fg = norm[norm != 0]
    assert np.isclose(fg.mean(), 0.0, atol=0.1)
    assert np.isclose(fg.std(), 1.0, atol=0.1)

def test_extract_brain_bounding_box():
    """Verify bounding box tightly encloses non-zero tissue with margin."""
    volume = np.zeros((50, 50, 50), dtype=np.float32)
    volume[10:30, 15:35, 20:40] = 1.0

    bbox = extract_brain_bounding_box(volume, margin=2)
    assert bbox[0].start <= 10
    assert bbox[0].stop >= 30
    assert bbox[1].start <= 15
    assert bbox[1].stop >= 35

def test_resample_volume_discrete_labels():
    """Verify discrete mask labels {0, 1, 2, 4} are preserved during nearest-neighbor resampling."""
    mask = np.zeros((32, 32, 32), dtype=np.uint8)
    mask[10:20, 10:20, 10:20] = 4
    mask[12:18, 12:18, 12:18] = 1

    resampled = resample_volume(mask, (16, 16, 16), is_mask=True)
    unique_labels = set(np.unique(resampled))
    assert unique_labels.issubset({0, 1, 4}), f"Non-discrete values introduced: {unique_labels}"

def test_restore_mask_geometry():
    """Verify mask can be restored to full original dimensions."""
    orig_shape = (40, 40, 40)
    pred_resampled = np.ones((20, 20, 20), dtype=np.uint8)
    restored = restore_mask_to_original(pred_resampled, orig_shape)
    assert restored.shape == orig_shape
