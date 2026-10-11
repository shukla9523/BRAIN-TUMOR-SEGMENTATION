import pytest
import numpy as np
from app.ml.evaluate import (
    compute_binary_dice,
    compute_binary_iou,
    compute_sensitivity_specificity,
    evaluate_segmentation_case
)

def test_dice_identical_masks():
    """Verify Dice score is 1.0 for perfect overlap."""
    mask_a = np.ones((20, 20, 20), dtype=bool)
    mask_b = np.ones((20, 20, 20), dtype=bool)
    dice = compute_binary_dice(mask_a, mask_b)
    assert np.isclose(dice, 1.0)

def test_dice_empty_masks_convention():
    """Verify Dice score is 1.0 when both predicted and ground truth masks are empty."""
    mask_empty = np.zeros((20, 20, 20), dtype=bool)
    dice = compute_binary_dice(mask_empty, mask_empty)
    assert dice == 1.0

def test_dice_false_positive_when_gt_empty():
    """Verify Dice score is 0.0 when GT is empty but prediction has positive voxels."""
    gt_empty = np.zeros((20, 20, 20), dtype=bool)
    pred_fp = np.zeros((20, 20, 20), dtype=bool)
    pred_fp[5, 5, 5] = True
    dice = compute_binary_dice(pred_fp, gt_empty)
    assert dice == 0.0

def test_iou_calculation():
    """Verify Jaccard IoU calculation for 50% overlap."""
    pred = np.zeros((10, 10, 10), dtype=bool)
    gt = np.zeros((10, 10, 10), dtype=bool)
    pred[:5, :, :] = True  # 500 voxels
    gt[:5, :, :] = True    # 500 voxels
    gt[5:7, :, :] = True   # 200 additional voxels in GT -> Union = 700, Intersection = 500
    iou = compute_binary_iou(pred, gt)
    expected_iou = 500.0 / 700.0
    assert np.isclose(iou, expected_iou, atol=1e-3)

def test_sensitivity_and_specificity():
    """Verify sensitivity (TPR) and specificity (TNR)."""
    pred = np.zeros((10, 10, 10), dtype=bool)
    gt = np.zeros((10, 10, 10), dtype=bool)
    # GT has 10 positive voxels
    gt[0, 0, :10] = True
    # Pred correctly detects 8, misses 2
    pred[0, 0, :8] = True
    metrics = compute_sensitivity_specificity(pred, gt)
    assert np.isclose(metrics["sensitivity"], 0.8, atol=0.01)
    assert metrics["specificity"] > 0.99
