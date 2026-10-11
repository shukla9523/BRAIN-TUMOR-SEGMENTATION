import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)

def test_api_health():
    """Verify health endpoint returns 200 and operational status."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "disclaimer" in data
    assert "device" in data

def test_model_info():
    """Verify model-info endpoint returns architecture and BraTS modalities."""
    response = client.get("/api/model-info")
    assert response.status_code == 200
    data = response.json()
    assert "3D U-Net" in data["architecture"]
    assert "FLAIR" in data["expected_modalities"]
    assert "label_mapping" in data

def test_get_metrics():
    """Verify metrics endpoint returns evaluation benchmark data."""
    response = client.get("/api/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "metrics_summary" in data
    assert "WT" in data["metrics_summary"]

def test_list_and_load_sample_scan():
    """Verify sample scans discovery and one-click loading endpoint."""
    response = client.get("/api/sample-scans")
    assert response.status_code == 200
    samples = response.json()["samples"]
    assert len(samples) > 0, "Expected at least 1 generated sample scan"

    sample_id = samples[0]["sample_id"]
    load_res = client.post(f"/api/sample-scans/load/{sample_id}")
    assert load_res.status_code == 200
    upload_data = load_res.json()
    assert "upload_id" in upload_data
    assert upload_data["total_slices_axial"] > 0

    # Test slice preview endpoint
    upload_id = upload_data["upload_id"]
    slice_res = client.get(f"/api/uploads/{upload_id}/slice/32?plane=axial")
    assert slice_res.status_code == 200
    slice_data = slice_res.json()
    assert slice_data["image_base64"].startswith("data:image/png;base64,")

def test_upload_invalid_file_extension():
    """Verify unsupported file formats are rejected with HTTP 415."""
    response = client.post(
        "/api/upload",
        files={"file": ("unsupported_scan.txt", b"plain text data", "text/plain")}
    )
    assert response.status_code in [415, 422]

def test_upload_image_photo_format():
    """Verify MRI image photos (.jpg, .png) are accepted and converted to 3D volume."""
    import io
    from PIL import Image
    import numpy as np

    # Generate synthetic 2D MRI photo
    pixels = np.zeros((128, 128), dtype=np.uint8)
    y, x = np.ogrid[:128, :128]
    pixels[(x - 64)**2 + (y - 64)**2 <= 40**2] = 180
    img = Image.fromarray(pixels)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    response = client.post(
        "/api/upload",
        files={"file": ("patient_brain_mri.jpg", buf.getvalue(), "image/jpeg")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["dimensions"] == [128, 128, 128]
    assert data["total_slices_axial"] == 128
    assert any("2D MRI scan photo" in w for w in data["warnings"])
