import pytest
import numpy as np
from app.utils.geometry import (
    calculate_voxel_volume_mm3,
    calculate_volume_cm3,
    get_slice_extents,
    analyze_subregions
)

def test_voxel_volume_calculation():
    """Verify physical voxel volume calculation in mm³."""
    spacing = [1.0, 1.0, 2.0]
    v_mm3 = calculate_voxel_volume_mm3(spacing)
    assert v_mm3 == 2.0

def test_volume_cm3_conversion():
    """Verify conversion from voxel count to cm³ (1000 mm³ = 1 cm³)."""
    # 1000 voxels with 1.0x1.0x1.0mm spacing = 1.0 cm³
    vol_cm3 = calculate_volume_cm3(1000, [1.0, 1.0, 1.0])
    assert vol_cm3 == 1.0

    # 5000 voxels with 2.0x2.0x2.0mm spacing (8mm³ per voxel) = 5000 * 8 / 1000 = 40.0 cm³
    vol_cm3_2 = calculate_volume_cm3(5000, [2.0, 2.0, 2.0])
    assert vol_cm3_2 == 40.0

def test_slice_extents():
    """Verify slice extent [min, max] identification."""
    mask = np.zeros((30, 30, 30), dtype=np.uint8)
    mask[5:15, 8:20, 12:25] = 1

    sag, cor, ax = get_slice_extents(mask)
    assert sag == [5, 14]
    assert cor == [8, 19]
    assert ax == [12, 24]

def test_subregion_analysis_hierarchies():
    """Verify that Whole Tumor (WT) volume correctly aggregates labels 1, 2, and 4."""
    mask = np.zeros((20, 20, 20), dtype=np.uint8)
    mask[0:2, 0:2, 0:2] = 1  # 8 voxels NCR/NET
    mask[2:4, 2:4, 2:4] = 2  # 8 voxels ED
    mask[4:6, 4:6, 4:6] = 4  # 8 voxels ET

    res = analyze_subregions(mask, [1.0, 1.0, 1.0])
    regions_dict = {r["region_id"]: r for r in res["regions"]}

    # WT should have 8 + 8 + 8 = 24 voxels
    assert regions_dict["WT"]["voxel_count"] == 24
    # TC should have 8 + 8 = 16 voxels
    assert regions_dict["TC"]["voxel_count"] == 16
    # ET should have 8 voxels
    assert regions_dict["ET"]["voxel_count"] == 8
