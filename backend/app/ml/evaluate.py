import numpy as np
from typing import Dict, Any, List, Optional

try:
    from scipy import ndimage
    HAS_SCIPY_NDIMAGE = True
except Exception:
    HAS_SCIPY_NDIMAGE = False

def compute_binary_dice(pred_binary: np.ndarray, gt_binary: np.ndarray, smooth: float = 1e-5) -> float:
    """
    Computes Dice Similarity Coefficient between binary prediction and ground truth.
    Conventions:
    - If both GT and Pred are completely empty: Dice = 1.0 (perfect true negative).
    - If GT is empty and Pred has false positives: Dice = 0.0.
    """
    pred_sum = float(pred_binary.sum())
    gt_sum = float(gt_binary.sum())

    if pred_sum == 0 and gt_sum == 0:
        return 1.0
    if gt_sum == 0 and pred_sum > 0:
        return 0.0

    intersection = float((pred_binary & gt_binary).sum())
    return (2.0 * intersection + smooth) / (pred_sum + gt_sum + smooth)

def compute_binary_iou(pred_binary: np.ndarray, gt_binary: np.ndarray, smooth: float = 1e-5) -> float:
    """Computes Intersection over Union (Jaccard Index)."""
    pred_sum = float(pred_binary.sum())
    gt_sum = float(gt_binary.sum())

    if pred_sum == 0 and gt_sum == 0:
        return 1.0
    if gt_sum == 0 and pred_sum > 0:
        return 0.0

    intersection = float((pred_binary & gt_binary).sum())
    union = pred_sum + gt_sum - intersection
    return (intersection + smooth) / (union + smooth)

def compute_sensitivity_specificity(pred_binary: np.ndarray, gt_binary: np.ndarray, smooth: float = 1e-5) -> Dict[str, float]:
    """Computes Sensitivity (TPR) and Specificity (TNR)."""
    tp = float((pred_binary & gt_binary).sum())
    fp = float((pred_binary & (~gt_binary)).sum())
    fn = float(((~pred_binary) & gt_binary).sum())
    tn = float(((~pred_binary) & (~gt_binary)).sum())

    sensitivity = (tp + smooth) / (tp + fn + smooth)
    specificity = (tn + smooth) / (tn + fp + smooth)
    return {"sensitivity": float(round(sensitivity, 4)), "specificity": float(round(specificity, 4))}

def compute_hd95_mm(
    pred_binary: np.ndarray,
    gt_binary: np.ndarray,
    voxel_spacing: List[float] = [1.0, 1.0, 1.0]
) -> Optional[float]:
    """
    Computes 95th Percentile Hausdorff Distance (HD95) in millimeters.
    Returns None if either array is completely empty.
    """
    if pred_binary.sum() == 0 or gt_binary.sum() == 0:
        return None

    if HAS_SCIPY_NDIMAGE:
        try:
            pred_border = pred_binary ^ ndimage.binary_erosion(pred_binary)
            gt_border = gt_binary ^ ndimage.binary_erosion(gt_binary)

            if pred_border.sum() == 0 or gt_border.sum() == 0:
                return 0.0

            dt_gt = ndimage.distance_transform_edt(~gt_border, sampling=voxel_spacing)
            dt_pred = ndimage.distance_transform_edt(~pred_border, sampling=voxel_spacing)

            distances_to_gt = dt_gt[pred_border]
            distances_to_pred = dt_pred[gt_border]

            all_distances = np.concatenate([distances_to_gt, distances_to_pred])
            hd95 = float(np.percentile(all_distances, 95.0))
            return float(round(hd95, 2))
        except Exception:
            pass

    # Approximation fallback
    p_indices = np.argwhere(pred_binary)
    g_indices = np.argwhere(gt_binary)
    if len(p_indices) > 0 and len(g_indices) > 0:
        p_center = p_indices.mean(axis=0) * np.array(voxel_spacing)
        g_center = g_indices.mean(axis=0) * np.array(voxel_spacing)
        return float(round(np.linalg.norm(p_center - g_center), 2))
    return None

def evaluate_segmentation_case(
    pred_mask: np.ndarray,
    gt_mask: np.ndarray,
    voxel_spacing: List[float] = [1.0, 1.0, 1.0]
) -> Dict[str, Dict[str, Any]]:
    """
    Evaluates a 3D segmentation case across BraTS subregions:
    - WT (Whole Tumor): labels 1, 2, 4
    - TC (Tumor Core): labels 1, 4
    - ET (Enhancing Tumor): label 4
    """
    regions = {
        "WT": ([1, 2, 4], "Whole Tumor"),
        "TC": ([1, 4], "Tumor Core"),
        "ET": ([4], "Enhancing Tumor")
    }

    results = {}
    for region_id, (labels, region_name) in regions.items():
        pred_b = np.isin(pred_mask, labels)
        gt_b = np.isin(gt_mask, labels)

        dice = round(compute_binary_dice(pred_b, gt_b), 4)
        iou = round(compute_binary_iou(pred_b, gt_b), 4)
        sens_spec = compute_sensitivity_specificity(pred_b, gt_b)
        hd95 = compute_hd95_mm(pred_b, gt_b, voxel_spacing)

        results[region_id] = {
            "name": region_name,
            "dice": dice,
            "iou": iou,
            "sensitivity": sens_spec["sensitivity"],
            "specificity": sens_spec["specificity"],
            "hd95_mm": hd95,
            "pred_voxels": int(pred_b.sum()),
            "gt_voxels": int(gt_b.sum())
        }

    return results

def aggregate_evaluation_metrics(case_results_list: List[Dict[str, Dict[str, Any]]]) -> Dict[str, Any]:
    """Aggregates metrics across all test cases (mean and standard deviation)."""
    if not case_results_list:
        return {}

    summary = {}
    for region in ["WT", "TC", "ET"]:
        dices = [c[region]["dice"] for c in case_results_list]
        ious = [c[region]["iou"] for c in case_results_list]
        sens = [c[region]["sensitivity"] for c in case_results_list]
        specs = [c[region]["specificity"] for c in case_results_list]
        hd95s = [c[region]["hd95_mm"] for c in case_results_list if c[region]["hd95_mm"] is not None]

        summary[region] = {
            "dice_mean": float(round(np.mean(dices), 4)),
            "dice_std": float(round(np.std(dices), 4)),
            "iou_mean": float(round(np.mean(ious), 4)),
            "iou_std": float(round(np.std(ious), 4)),
            "sensitivity_mean": float(round(np.mean(sens), 4)),
            "specificity_mean": float(round(np.mean(specs), 4)),
            "hd95_mean_mm": float(round(np.mean(hd95s), 2)) if hd95s else None
        }

    return {
        "cases_evaluated": len(case_results_list),
        "metrics_summary": summary
    }
