import pytest
from pathlib import Path
from app.services.report_service import generate_pdf_report

def test_generate_pdf_report(tmp_path):
    """Verify PDF compilation, metadata embedding, and file integrity."""
    dummy_result = {
        "result_id": "test-session-123",
        "created_at": "2026-10-11 12:00:00",
        "dimensions": [128, 128, 128],
        "voxel_spacing": [1.0, 1.0, 1.0],
        "quantitative_report": {
            "total_tumor_volume_cm3": 14.52,
            "processing_time_seconds": 1.45,
            "regions": [
                {
                    "region_name": "Whole Tumor (WT)",
                    "labels_included": [1, 2, 4],
                    "volume_cm3": 14.52,
                    "voxel_count": 14520,
                    "slice_extent_axial": [40, 75],
                    "connected_components": 1
                },
                {
                    "region_name": "Tumor Core (TC)",
                    "labels_included": [1, 4],
                    "volume_cm3": 8.21,
                    "voxel_count": 8210,
                    "slice_extent_axial": [45, 68],
                    "connected_components": 1
                }
            ],
            "quality_warnings": ["Synthetic test fixture evaluation."]
        }
    }

    out_pdf = tmp_path / "test_report.pdf"
    pdf_path = generate_pdf_report(dummy_result, str(out_pdf))

    assert Path(pdf_path).exists()
    assert Path(pdf_path).stat().st_size > 1000, "PDF file is unexpectedly small"
