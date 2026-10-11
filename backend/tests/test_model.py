import pytest
import torch
from app.ml.model import UNet3D, AttentionUNet3D, create_model, count_parameters

def test_unet3d_forward_pass_dimensions():
    """Verify that 3D U-Net produces matching volumetric spatial output dimensions."""
    model = UNet3D(in_channels=4, out_channels=4, base_filters=8)
    model.eval()

    # Input: (Batch=1, Channels=4, D=32, H=32, W=32)
    x = torch.randn(1, 4, 32, 32, 32)
    with torch.no_grad():
        out = model(x)

    assert out.shape == (1, 4, 32, 32, 32), f"Expected shape (1, 4, 32, 32, 32), got {out.shape}"

def test_attention_unet3d_dimensions():
    """Verify that 3D Attention U-Net produces matching output dimensions."""
    model = AttentionUNet3D(in_channels=4, out_channels=4, base_filters=8)
    model.eval()

    x = torch.randn(1, 4, 32, 32, 32)
    with torch.no_grad():
        out = model(x)

    assert out.shape == (1, 4, 32, 32, 32)

def test_parameter_counting():
    """Verify parameter counter returns non-zero for initialized models."""
    model = create_model("3d_unet", in_channels=4, out_channels=4, base_filters=8)
    params = count_parameters(model)
    assert params > 10000, f"Expected >10k parameters, got {params}"
