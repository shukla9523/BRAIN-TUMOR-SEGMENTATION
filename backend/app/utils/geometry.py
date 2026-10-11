import numpy as np
from typing import Dict, List, Tuple, Any, Optional

try:
    from scipy import ndimage
    HAS_SCIPY = True
except Exception:
    HAS_SCIPY = False

def calculate_voxel_volume_mm3(voxel_spacing: List[float]) -> float:
    """Calculates the physical volume of a single voxel in mm³."""
    if not voxel_spacing or len(voxel_spacing) < 3:
        return 1.0
    vx = abs(float(voxel_spacing[0]))
    vy = abs(float(voxel_spacing[1]))
    vz = abs(float(voxel_spacing[2]))
    if vx <= 0 or vy <= 0 or vz <= 0:
        return 1.0
    return vx * vy * vz

def calculate_volume_cm3(voxel_count: int, voxel_spacing: List[float]) -> float:
    """
    Converts voxel count to cubic centimeters (cm³) given physical voxel spacing (in mm).
    1 cm³ = 1000 mm³.
    """
    v_mm3 = calculate_voxel_volume_mm3(voxel_spacing)
    return float(round((voxel_count * v_mm3) / 1000.0, 3))

def get_slice_extents(mask_3d: np.ndarray) -> Tuple[List[int], List[int], List[int]]:
    """
    Returns [start, end] slice indices (0-indexed) where mask > 0 exists
    along Sagittal (X, axis 0), Coronal (Y, axis 1), and Axial (Z, axis 2).
    """
    if mask_3d.sum() == 0:
        return [0, 0], [0, 0], [0, 0]
    
    indices = np.where(mask_3d > 0)
    sag_min, sag_max = int(indices[0].min()), int(indices[0].max())
    cor_min, cor_max = int(indices[1].min()), int(indices[1].max())
    ax_min, ax_max = int(indices[2].min()), int(indices[2].max())
    
    return [sag_min, sag_max], [cor_min, cor_max], [ax_min, ax_max]

def count_connected_components(binary_mask: np.ndarray) -> int:
    """
    Computes number of connected components in 3D.
    Uses scipy.ndimage if available, with robust fallback.
    """
    if binary_mask.sum() == 0:
        return 0
    if HAS_SCIPY:
        try:
            structure = ndimage.generate_binary_structure(3, 2)
            _, num_features = ndimage.label(binary_mask, structure=structure)
            return int(num_features)
        except Exception:
            pass
    return 1

def analyze_subregions(
    pred_mask: np.ndarray,
    voxel_spacing: List[float],
    brain_mask: Optional[np.ndarray] = None
) -> Dict[str, Any]:
    """
    Extracts quantitative metrics for BraTS subregions:
    - WT (Whole Tumor): labels 1, 2, 4
    - TC (Tumor Core): labels 1, 4
    - ET (Enhancing Tumor): label 4
    - NCR/NET: label 1
    - ED: label 2
    """
    spacing = voxel_spacing if (voxel_spacing and len(voxel_spacing) >= 3) else [1.0, 1.0, 1.0]
    total_brain_voxels = int((brain_mask > 0).sum()) if brain_mask is not None else int((pred_mask >= 0).sum())
    
    subregions_def = [
        {
            "id": "WT",
            "name": "Whole Tumor (WT)",
            "labels": [1, 2, 4],
            "color_hex": "#2563EB"
        },
        {
            "id": "TC",
            "name": "Tumor Core (TC)",
            "labels": [1, 4],
            "color_hex": "#DC2626"
        },
        {
            "id": "ET",
            "name": "Enhancing Tumor (ET)",
            "labels": [4],
            "color_hex": "#F59E0B"
        },
        {
            "id": "ED",
            "name": "Peritumoral Edema (ED)",
            "labels": [2],
            "color_hex": "#10B981"
        },
        {
            "id": "NCR_NET",
            "name": "Necrotic & Non-Enhancing Core (NCR/NET)",
            "labels": [1],
            "color_hex": "#8B5CF6"
        }
    ]
    
    results = []
    quality_warnings = []
    
    if any(s <= 0 for s in spacing):
        quality_warnings.append("Invalid or non-positive voxel spacing in NIfTI header; assumed 1.0 mm isotropic spacing.")
    elif max(spacing) / min(spacing) > 3.0:
        quality_warnings.append(f"Highly anisotropic voxel spacing detected ({spacing[0]:.2f} x {spacing[1]:.2f} x {spacing[2]:.2f} mm). Volumetric estimates should be interpreted with caution.")

    for region in subregions_def:
        binary = np.isin(pred_mask, region["labels"])
        voxel_count = int(binary.sum())
        volume_cm3 = calculate_volume_cm3(voxel_count, spacing)
        
        sag, cor, ax = get_slice_extents(binary)
        conn_comp = count_connected_components(binary)
        
        pct_brain = round((voxel_count / total_brain_voxels) * 100.0, 2) if total_brain_voxels > 0 else 0.0
        
        results.append({
            "region_id": region["id"],
            "region_name": region["name"],
            "labels_included": region["labels"],
            "volume_cm3": volume_cm3,
            "voxel_count": voxel_count,
            "percentage_of_brain": pct_brain,
            "slice_extent_sagittal": sag,
            "slice_extent_coronal": cor,
            "slice_extent_axial": ax,
            "connected_components": conn_comp,
            "color_hex": region["color_hex"]
        })

    wt_metric = next((r for r in results if r["region_id"] == "WT"), None)
    total_tumor_cm3 = wt_metric["volume_cm3"] if wt_metric else 0.0

    return {
        "total_tumor_volume_cm3": total_tumor_cm3,
        "regions": results,
        "voxel_spacing_mm": [round(float(s), 3) for s in spacing],
        "dimensions": list(pred_mask.shape),
        "quality_warnings": quality_warnings
    }
