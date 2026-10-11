import os
import io
import base64
import gzip
import struct
import numpy as np
from pathlib import Path
from typing import Tuple, Dict, Any, Optional
from PIL import Image

try:
    import nibabel as nib
    HAS_NIBABEL = True
except ImportError:
    HAS_NIBABEL = False

from app.core.errors import MriValidationError

def load_nifti_volume(file_path: str) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
    """
    Loads a .nii or .nii.gz volume.
    Returns:
        data: 3D or 4D numpy array float32
        affine: 4x4 affine matrix
        metadata: Dict with dimensions, voxel_spacing, orientation, etc.
    """
    path = Path(file_path)
    if not path.exists():
        raise MriValidationError(f"File not found: {file_path}")

    lower_name = path.name.lower()

    # 1. Image photo formats (PNG, JPG, JPEG, WEBP, BMP, TIFF)
    image_exts = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff")
    if lower_name.endswith(image_exts):
        return _load_2d_image_as_3d_volume(path)

    # 2. DICOM format (.dcm)
    if lower_name.endswith(".dcm"):
        return _load_dicom_as_3d_volume(path)

    if HAS_NIBABEL:
        try:
            nii = nib.load(str(path))
            # canonical reorientation
            try:
                nii_canon = nib.as_closest_canonical(nii)
                data = nii_canon.get_fdata(dtype=np.float32)
                affine = nii_canon.affine
                header = nii_canon.header
            except Exception:
                data = nii.get_fdata(dtype=np.float32)
                affine = nii.affine
                header = nii.header

            zooms = [float(z) for z in header.get_zooms()[:3]]
            shape = list(data.shape)

            orientation = "".join(nib.aff2axcodes(affine))
            
            # Check 4D vs 3D
            if len(shape) == 4:
                # If shape is (X, Y, Z, 1), squeeze
                if shape[3] == 1:
                    data = data[..., 0]
                    shape = list(data.shape)

            metadata = {
                "dimensions": shape,
                "voxel_spacing": zooms,
                "orientation": orientation,
                "data_min": float(data.min()),
                "data_max": float(data.max()),
                "data_mean": float(data.mean()),
                "data_std": float(data.std())
            }
            return data, affine, metadata
        except Exception as e:
            raise MriValidationError(f"Failed to parse NIfTI volume with NiBabel: {str(e)}")

    # Pure Python NIfTI-1 fallback reader if nibabel is not installed
    return _fallback_read_nifti(path)

def _load_2d_image_as_3d_volume(path: Path) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
    """
    Converts 2D MRI photo (PNG, JPG, JPEG, WEBP, BMP, TIFF) into a 3D volumetric stack (128x128x128).
    Places the MRI slice in the center (axial slice 64) with continuous 3D contextual attenuation
    so that 3D U-Net deep learning segmentation can execute seamlessly.
    """
    try:
        pil_img = Image.open(str(path)).convert("L")
        w, h = pil_img.size

        # Preserve aspect ratio by placing into square canvas
        max_side = max(w, h)
        square_img = Image.new("L", (max_side, max_side), 0)
        paste_x = (max_side - w) // 2
        paste_y = (max_side - h) // 2
        square_img.paste(pil_img, (paste_x, paste_y))

        # Resize to standard spatial dimensions 128x128
        resized_img = square_img.resize((128, 128), Image.Resampling.LANCZOS)
        arr_2d = np.array(resized_img, dtype=np.float32)

        # Clean background noise (compression artifacts / text margins)
        v_max = float(arr_2d.max())
        v_min = float(arr_2d.min())
        if v_max > v_min:
            arr_2d = (arr_2d - v_min) / (v_max - v_min + 1e-8) * 100.0
            threshold = 0.04 * arr_2d.max()
            arr_2d[arr_2d < threshold] = 0.0

        # Axial slice extraction in get_2d_slice rotates by +90 degrees (rot90(..., 1)).
        # Pre-rotate by -1 so that extracting axial slice 64 directly displays the upright photo!
        unrot_slice = np.rot90(arr_2d, -1)

        # Construct 3D volume (128, 128, 128)
        vol_3d = np.zeros((128, 128, 128), dtype=np.float32)
        for z in range(128):
            dz = abs(z - 64)
            if dz <= 18:
                weight = float(np.exp(-(dz ** 2) / (2.0 * (8.0 ** 2))))
                vol_3d[:, :, z] = unrot_slice * weight

        affine = np.eye(4, dtype=np.float32)
        metadata = {
            "dimensions": [128, 128, 128],
            "voxel_spacing": [1.0, 1.0, 1.0],
            "orientation": "RAS",
            "data_min": float(vol_3d.min()),
            "data_max": float(vol_3d.max()),
            "data_mean": float(vol_3d.mean()),
            "data_std": float(vol_3d.std()),
            "is_2d_photo": True,
            "default_slice_index": 64,
            "format": path.suffix.lower()
        }
        return vol_3d, affine, metadata
    except Exception as e:
        raise MriValidationError(f"Failed to process MRI image photo '{path.name}': {str(e)}")

def _load_dicom_as_3d_volume(path: Path) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
    """
    Parses DICOM (.dcm) file using pydicom, extracting 2D slice or 3D series.
    """
    try:
        import pydicom
        ds = pydicom.dcmread(str(path))
        pixel_array = ds.pixel_array.astype(np.float32)

        slope = float(getattr(ds, "RescaleSlope", 1.0))
        intercept = float(getattr(ds, "RescaleIntercept", 0.0))
        pixel_array = pixel_array * slope + intercept

        if pixel_array.ndim == 2:
            p_min, p_max = float(pixel_array.min()), float(pixel_array.max())
            if p_max > p_min:
                norm_img = ((pixel_array - p_min) / (p_max - p_min) * 255.0).astype(np.uint8)
            else:
                norm_img = np.zeros_like(pixel_array, dtype=np.uint8)

            pil_img = Image.fromarray(norm_img)
            w, h = pil_img.size
            max_side = max(w, h)
            square_img = Image.new("L", (max_side, max_side), 0)
            square_img.paste(pil_img, ((max_side - w) // 2, (max_side - h) // 2))

            resized_img = square_img.resize((128, 128), Image.Resampling.LANCZOS)
            arr_2d = np.array(resized_img, dtype=np.float32)
            if arr_2d.max() > arr_2d.min():
                arr_2d = (arr_2d - arr_2d.min()) / (arr_2d.max() - arr_2d.min() + 1e-8) * 100.0

            unrot_slice = np.rot90(arr_2d, -1)
            vol_3d = np.zeros((128, 128, 128), dtype=np.float32)
            for z in range(128):
                dz = abs(z - 64)
                if dz <= 18:
                    weight = float(np.exp(-(dz ** 2) / (2.0 * (8.0 ** 2))))
                    vol_3d[:, :, z] = unrot_slice * weight

            affine = np.eye(4, dtype=np.float32)
            metadata = {
                "dimensions": [128, 128, 128],
                "voxel_spacing": [1.0, 1.0, 1.0],
                "orientation": "RAS",
                "data_min": float(vol_3d.min()),
                "data_max": float(vol_3d.max()),
                "data_mean": float(vol_3d.mean()),
                "data_std": float(vol_3d.std()),
                "is_dicom": True,
                "default_slice_index": 64
            }
            return vol_3d, affine, metadata
        elif pixel_array.ndim >= 3:
            vol_3d = pixel_array
            affine = np.eye(4, dtype=np.float32)
            metadata = {
                "dimensions": list(vol_3d.shape),
                "voxel_spacing": [1.0, 1.0, 1.0],
                "orientation": "RAS",
                "data_min": float(vol_3d.min()),
                "data_max": float(vol_3d.max()),
                "data_mean": float(vol_3d.mean()),
                "data_std": float(vol_3d.std()),
                "is_dicom": True
            }
            return vol_3d, affine, metadata
        else:
            raise ValueError(f"Unexpected pixel array dimensions: {pixel_array.ndim}")
    except Exception as e:
        raise MriValidationError(f"Failed to process DICOM file '{path.name}': {str(e)}")

def _fallback_read_nifti(path: Path) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
    """Fallback reader for standard uncompressed or gzip NIfTI-1 files."""
    try:
        raw_bytes = gzip.decompress(path.read_bytes()) if str(path).endswith(".gz") else path.read_bytes()
        if len(raw_bytes) < 348:
            raise ValueError("File too small to be a valid NIfTI-1 header.")
        
        # Read sizeof_hdr (int32 at offset 0)
        sizeof_hdr = struct.unpack("<i", raw_bytes[:4])[0]
        endian = "<"
        if sizeof_hdr != 348:
            sizeof_hdr = struct.unpack(">i", raw_bytes[:4])[0]
            endian = ">"
            if sizeof_hdr != 348:
                raise ValueError("Invalid NIfTI-1 header size.")

        # Read dimensions at offset 40 (dim[8]: short)
        dims = struct.unpack(f"{endian}8h", raw_bytes[40:56])
        ndim = dims[0]
        dim_x, dim_y, dim_z = dims[1], dims[2], dims[3]

        # Read voxel spacing at offset 76 (pixdim[8]: float)
        pixdims = struct.unpack(f"{endian}8f", raw_bytes[76:108])
        zooms = [float(pixdims[1]), float(pixdims[2]), float(pixdims[3])]

        # Read datatype at offset 70 (short)
        datatype = struct.unpack(f"{endian}h", raw_bytes[70:72])[0]
        vox_offset = int(struct.unpack(f"{endian}f", raw_bytes[108:112])[0])

        # Map basic datatypes
        dtype_map = {
            2: np.uint8,
            4: np.int16,
            8: np.int32,
            16: np.float32,
            64: np.float64
        }
        np_dtype = dtype_map.get(datatype, np.float32)

        raw_array = np.frombuffer(raw_bytes[vox_offset:], dtype=np_dtype)
        expected_len = dim_x * dim_y * dim_z
        if len(raw_array) >= expected_len:
            data = raw_array[:expected_len].reshape((dim_x, dim_y, dim_z), order="F").astype(np.float32)
        else:
            raise ValueError("Data buffer shorter than header dimensions.")

        affine = np.diag([zooms[0], zooms[1], zooms[2], 1.0])
        metadata = {
            "dimensions": [dim_x, dim_y, dim_z],
            "voxel_spacing": zooms,
            "orientation": "RAS",
            "data_min": float(data.min()),
            "data_max": float(data.max()),
            "data_mean": float(data.mean()),
            "data_std": float(data.std())
        }
        return data, affine, metadata
    except Exception as e:
        raise MriValidationError(f"Fallback NIfTI reader error: {str(e)}")

def save_nifti_mask(mask_data: np.ndarray, affine: np.ndarray, output_path: str):
    """Saves a 3D segmentation mask as a compressed NIfTI (.nii.gz) file."""
    output_path = str(output_path)
    if HAS_NIBABEL:
        nii = nib.Nifti1Image(mask_data.astype(np.uint8), affine)
        nib.save(nii, output_path)
    else:
        # Fallback numpy save if nibabel unavailable
        np.save(output_path.replace(".nii.gz", ".npy"), mask_data.astype(np.uint8))

def get_2d_slice(volume_3d: np.ndarray, plane: str, slice_index: int) -> np.ndarray:
    """
    Extracts a 2D slice from 3D volume along requested plane.
    Planes:
        - 'axial': Z axis (axis 2) -> (X, Y)
        - 'coronal': Y axis (axis 1) -> (X, Z)
        - 'sagittal': X axis (axis 0) -> (Y, Z)
    """
    nx, ny, nz = volume_3d.shape
    plane = plane.lower()

    if plane == "axial":
        idx = max(0, min(slice_index, nz - 1))
        slice_2d = volume_3d[:, :, idx]
        # Transpose/flip for standard medical radiology orientation
        slice_2d = np.rot90(slice_2d, 1)
    elif plane == "coronal":
        idx = max(0, min(slice_index, ny - 1))
        slice_2d = volume_3d[:, idx, :]
        slice_2d = np.rot90(slice_2d, 1)
    elif plane == "sagittal":
        idx = max(0, min(slice_index, nx - 1))
        slice_2d = volume_3d[idx, :, :]
        slice_2d = np.rot90(slice_2d, 1)
    else:
        raise ValueError(f"Unknown plane: {plane}. Must be axial, coronal, or sagittal.")

    return slice_2d

def render_slice_visualization(
    mri_slice: np.ndarray,
    mask_slice: Optional[np.ndarray] = None,
    contrast_window: Optional[Tuple[float, float]] = None,
    alpha: float = 0.65
) -> Dict[str, Any]:
    """
    Renders base MRI slice and colorized segmentation overlay as Base64 PNGs.
    Subregions color palette:
    - Label 1 (NCR/NET): Purple [139, 92, 246]
    - Label 2 (ED): Green [16, 185, 129]
    - Label 4 (ET): Amber/Yellow [245, 158, 11]
    """
    # 1. Windowing and intensity scaling
    mri_clean = np.nan_to_num(mri_slice)
    if contrast_window:
        c_min, c_max = contrast_window
    else:
        # Robust 1st - 99th percentile windowing
        valid_voxels = mri_clean[mri_clean > 0]
        if len(valid_voxels) > 0:
            c_min = float(np.percentile(valid_voxels, 1.0))
            c_max = float(np.percentile(valid_voxels, 99.0))
        else:
            c_min = float(mri_clean.min())
            c_max = float(mri_clean.max())

    if c_max <= c_min:
        c_max = c_min + 1e-5

    norm_mri = np.clip((mri_clean - c_min) / (c_max - c_min), 0.0, 1.0)
    gray_img = (norm_mri * 255).astype(np.uint8)
    
    # Base grayscale image (RGB)
    rgb_mri = np.stack([gray_img, gray_img, gray_img], axis=-1)

    # 2. Base MRI to base64 PNG
    pil_mri = Image.fromarray(rgb_mri)
    buf_mri = io.BytesIO()
    pil_mri.save(buf_mri, format="PNG")
    mri_b64 = "data:image/png;base64," + base64.b64encode(buf_mri.getvalue()).decode("utf-8")

    mask_b64 = None
    overlay_b64 = None
    has_tumor = False
    subregion_counts = {"NCR_NET": 0, "ED": 0, "ET": 0}

    # 3. If mask slice exists, render mask and composite overlay
    if mask_slice is not None:
        h, w = mask_slice.shape
        rgba_mask = np.zeros((h, w, 4), dtype=np.uint8)
        rgba_overlay = np.dstack([rgb_mri, np.full((h, w), 255, dtype=np.uint8)])

        label_colors = {
            1: (139, 92, 246),  # NCR/NET - Violet
            2: (16, 185, 129),   # ED - Emerald Green
            4: (245, 158, 11)   # ET - Amber / Yellow
        }

        has_tumor = bool((mask_slice > 0).any())
        subregion_counts["NCR_NET"] = int((mask_slice == 1).sum())
        subregion_counts["ED"] = int((mask_slice == 2).sum())
        subregion_counts["ET"] = int((mask_slice == 4).sum())

        for lbl, (r, g, b) in label_colors.items():
            loc = (mask_slice == lbl)
            if np.any(loc):
                rgba_mask[loc] = [r, g, b, int(alpha * 255)]
                # Composite on overlay (vectorized across all matching voxels)
                rgba_overlay[loc, 0] = ((1 - alpha) * rgba_overlay[loc, 0] + alpha * r).astype(np.uint8)
                rgba_overlay[loc, 1] = ((1 - alpha) * rgba_overlay[loc, 1] + alpha * g).astype(np.uint8)
                rgba_overlay[loc, 2] = ((1 - alpha) * rgba_overlay[loc, 2] + alpha * b).astype(np.uint8)

        pil_mask = Image.fromarray(rgba_mask, mode="RGBA")
        buf_mask = io.BytesIO()
        pil_mask.save(buf_mask, format="PNG")
        mask_b64 = "data:image/png;base64," + base64.b64encode(buf_mask.getvalue()).decode("utf-8")

        pil_overlay = Image.fromarray(rgba_overlay[:, :, :3], mode="RGB")
        buf_overlay = io.BytesIO()
        pil_overlay.save(buf_overlay, format="PNG")
        overlay_b64 = "data:image/png;base64," + base64.b64encode(buf_overlay.getvalue()).decode("utf-8")

    return {
        "width": int(gray_img.shape[1]),
        "height": int(gray_img.shape[0]),
        "image_base64": mri_b64,
        "mask_base64": mask_b64,
        "overlay_base64": overlay_b64 or mri_b64,
        "has_tumor": has_tumor,
        "subregion_counts": subregion_counts
    }
