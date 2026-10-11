import math
from typing import Dict, Any, Optional

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    # Mock class definitions if torch is not yet installed
    class nn:
        Module = object

if HAS_TORCH:
    class DoubleConv3D(nn.Module):
        """(Conv3D -> InstanceNorm3d -> LeakyReLU) * 2 with residual support."""
        def __init__(self, in_channels: int, out_channels: int, dropout: float = 0.0):
            super().__init__()
            self.conv1 = nn.Conv3d(in_channels, out_channels, kernel_size=3, padding=1, bias=False)
            self.norm1 = nn.InstanceNorm3d(out_channels)
            self.act1 = nn.LeakyReLU(negative_slope=0.01, inplace=True)
            
            self.conv2 = nn.Conv3d(out_channels, out_channels, kernel_size=3, padding=1, bias=False)
            self.norm2 = nn.InstanceNorm3d(out_channels)
            self.act2 = nn.LeakyReLU(negative_slope=0.01, inplace=True)
            self.dropout = nn.Dropout3d(dropout) if dropout > 0 else nn.Identity()

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            x = self.act1(self.norm1(self.conv1(x)))
            x = self.dropout(x)
            x = self.act2(self.norm2(self.conv2(x)))
            return x

    class DownBlock3D(nn.Module):
        """Downscaling with MaxPool3d then DoubleConv3D."""
        def __init__(self, in_channels: int, out_channels: int, dropout: float = 0.0):
            super().__init__()
            self.pool = nn.MaxPool3d(2)
            self.conv = DoubleConv3D(in_channels, out_channels, dropout=dropout)

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            return self.conv(self.pool(x))

    class AttentionGate3D(nn.Module):
        """3D Additive Attention Gate for Attention U-Net."""
        def __init__(self, f_g: int, f_l: int, f_int: int):
            super().__init__()
            self.w_g = nn.Sequential(
                nn.Conv3d(f_g, f_int, kernel_size=1, stride=1, padding=0, bias=True),
                nn.InstanceNorm3d(f_int)
            )
            self.w_x = nn.Sequential(
                nn.Conv3d(f_l, f_int, kernel_size=1, stride=1, padding=0, bias=True),
                nn.InstanceNorm3d(f_int)
            )
            self.psi = nn.Sequential(
                nn.Conv3d(f_int, 1, kernel_size=1, stride=1, padding=0, bias=True),
                nn.InstanceNorm3d(1),
                nn.Sigmoid()
            )
            self.relu = nn.ReLU(inplace=True)

        def forward(self, g: torch.Tensor, x: torch.Tensor) -> torch.Tensor:
            g1 = self.w_g(g)
            x1 = self.w_x(x)
            # Ensure spatial dimension match
            if g1.shape[2:] != x1.shape[2:]:
                g1 = F.interpolate(g1, size=x1.shape[2:], mode="trilinear", align_corners=True)
            psi = self.relu(g1 + x1)
            psi = self.psi(psi)
            return x * psi

    class UpBlock3D(nn.Module):
        """Upscaling then DoubleConv3D with optional Attention Gate."""
        def __init__(self, in_channels: int, out_channels: int, use_attention: bool = False, dropout: float = 0.0):
            super().__init__()
            self.up = nn.ConvTranspose3d(in_channels, in_channels // 2, kernel_size=2, stride=2)
            self.use_attention = use_attention
            if use_attention:
                self.attention = AttentionGate3D(f_g=in_channels // 2, f_l=in_channels // 2, f_int=in_channels // 4)
            else:
                self.attention = None
            self.conv = DoubleConv3D(in_channels, out_channels, dropout=dropout)

        def forward(self, x1: torch.Tensor, x2: torch.Tensor) -> torch.Tensor:
            # x1: from lower layer, x2: skip connection from encoder
            x1 = self.up(x1)
            
            # Handle possible padding discrepancies
            diffZ = x2.size(2) - x1.size(2)
            diffY = x2.size(3) - x1.size(3)
            diffX = x2.size(4) - x1.size(4)
            if diffZ != 0 or diffY != 0 or diffX != 0:
                x1 = F.pad(x1, [diffX // 2, diffX - diffX // 2,
                                diffY // 2, diffY - diffY // 2,
                                diffZ // 2, diffZ - diffZ // 2])

            if self.attention is not None:
                x2 = self.attention(g=x1, x=x2)

            x = torch.cat([x2, x1], dim=1)
            return self.conv(x)

    class UNet3D(nn.Module):
        """
        Standard 3D U-Net architecture for multi-modality volumetric brain tumor segmentation.
        Default: 4 input channels (T1, T1ce, T2, FLAIR) -> 4 output classes (BG, NCR/NET, ED, ET)
        """
        def __init__(
            self,
            in_channels: int = 4,
            out_channels: int = 4,
            base_filters: int = 16, # 16 for lightweight CPU/memory efficiency; scale to 32 on GPU
            use_attention: bool = False,
            dropout: float = 0.1
        ):
            super().__init__()
            self.in_channels = in_channels
            self.out_channels = out_channels
            self.use_attention = use_attention

            f = base_filters
            self.inc = DoubleConv3D(in_channels, f, dropout=dropout)
            self.down1 = DownBlock3D(f, f * 2, dropout=dropout)
            self.down2 = DownBlock3D(f * 2, f * 4, dropout=dropout)
            self.down3 = DownBlock3D(f * 4, f * 8, dropout=dropout)

            self.up1 = UpBlock3D(f * 8, f * 4, use_attention=use_attention, dropout=dropout)
            self.up2 = UpBlock3D(f * 4, f * 2, use_attention=use_attention, dropout=dropout)
            self.up3 = UpBlock3D(f * 2, f, use_attention=use_attention, dropout=dropout)

            self.outc = nn.Conv3d(f, out_channels, kernel_size=1)

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            x1 = self.inc(x)
            x2 = self.down1(x1)
            x3 = self.down2(x2)
            x4 = self.down3(x3)

            x = self.up1(x4, x3)
            x = self.up2(x, x2)
            x = self.up3(x, x1)
            logits = self.outc(x)
            return logits

    class AttentionUNet3D(UNet3D):
        """3D Attention U-Net variant with Attention Gates on skip connections."""
        def __init__(self, in_channels: int = 4, out_channels: int = 4, base_filters: int = 16, dropout: float = 0.1):
            super().__init__(
                in_channels=in_channels,
                out_channels=out_channels,
                base_filters=base_filters,
                use_attention=True,
                dropout=dropout
            )

else:
    class UNet3D:
        pass
    class AttentionUNet3D:
        pass

def create_model(
    architecture: str = "3d_unet",
    in_channels: int = 4,
    out_channels: int = 4,
    base_filters: int = 16,
    device: str = "cpu"
) -> Any:
    """Factory helper to construct model and move to target device."""
    if not HAS_TORCH:
        raise RuntimeError("PyTorch is required to instantiate NeuroScan models.")

    arch = architecture.lower()
    if "attention" in arch:
        model = AttentionUNet3D(in_channels=in_channels, out_channels=out_channels, base_filters=base_filters)
    else:
        model = UNet3D(in_channels=in_channels, out_channels=out_channels, base_filters=base_filters)

    return model.to(device)

def count_parameters(model: Any) -> int:
    """Calculates trainable parameter count."""
    if not HAS_TORCH or not hasattr(model, "parameters"):
        return 0
    return sum(p.numel() for p in model.parameters() if p.requires_grad)
