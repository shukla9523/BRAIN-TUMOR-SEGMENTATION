import pytest
from pathlib import Path
from app.services.mri_service import mri_service
from app.services.report_service import generate_pdf_report
from app.core.config import settings

def test_end_to_end_inference_and_report(tmp_path):
    """
    End-to-end pipeline test:
    Loads sample phantom -> executes 3D segmentation -> verifies volumetric metrics -> compiles PDF report.
    """
    # 1. Locate sample phantom
    flair_matches = list(settings.SAMPLE_DIR.glob("*flair*.nii*"))
    assert len(flair_matches) > 0, "Synthetic phantom sample not found."
    sample_file = flair_matches[0]

    # 2. Upload stream simulation
    content = sample_file.read_bytes()
    upload_info = mri_service.save_upload_stream(content, sample_file.name)
    assert "upload_id" in upload_info
    upload_id = upload_info["upload_id"]

    # 3. Execute 3D segmentation
    result_info = mri_service.run_segmentation(upload_id=upload_id, selected_modality="FLAIR")
    assert "result_id" in result_info
    result_id = result_info["result_id"]

    # 4. Verify quantitative measurements
    quant = result_info["quantitative_report"]
    assert "total_tumor_volume_cm3" in quant
    assert len(quant["regions"]) >= 3
    assert quant["total_tumor_volume_cm3"] >= 0.0

    # 5. Verify slice rendering
    slice_vis = mri_service.render_slice(result_id, plane="axial", slice_index=64)
    assert slice_vis["image_base64"].startswith("data:image/png;base64,")
    assert slice_vis["overlay_base64"].startswith("data:image/png;base64,")

    # 6. Verify PDF report generation
    pdf_out = tmp_path / f"report_{result_id}.pdf"
    pdf_file = generate_pdf_report(result_info, str(pdf_out))
    assert Path(pdf_file).exists()
    assert Path(pdf_file).stat().st_size > 1000
