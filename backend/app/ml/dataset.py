import os
import glob
import random
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

try:
    import torch
    from torch.utils.data import Dataset
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    class Dataset:
        pass

from app.utils.nifti_io import load_nifti_volume
from app.ml.preprocessing import normalize_brain_intensities, resample_volume, convert_brats_labels_to_standard

class BraTSDataset(Dataset):
    """
    Volumetric BraTS Dataset loader.
    Expects patient directories with *_flair.nii.gz, *_t1.nii.gz, *_t1ce.nii.gz, *_t2.nii.gz, and *_seg.nii.gz.
    """
    def __init__(
        self,
        patient_dirs: List[Path],
        target_shape: Tuple[int, int, int] = (128, 128, 128),
        is_training: bool = True,
        modalities: Tuple[str, ...] = ("t1", "t1ce", "t2", "flair"),
        transform: bool = True
    ):
        self.patient_dirs = patient_dirs
        self.target_shape = target_shape
        self.is_training = is_training
        self.modalities = modalities
        self.transform = transform and is_training

    def __len__(self) -> int:
        return len(self.patient_dirs)

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        pdir = self.patient_dirs[idx]
        mod_volumes = []

        # Load 4 MRI modalities
        for mod in self.modalities:
            file_match = list(pdir.glob(f"*{mod}.nii*")) or list(pdir.glob(f"*{mod.upper()}.nii*"))
            if not file_match:
                raise FileNotFoundError(f"Missing {mod} modality in {pdir}")
            vol, _, _ = load_nifti_volume(str(file_match[0]))
            vol_norm = normalize_brain_intensities(vol)
            vol_res = resample_volume(vol_norm, self.target_shape, is_mask=False)
            mod_volumes.append(vol_res)

        # Stack to 4 channels: (4, D, H, W)
        image_4d = np.stack(mod_volumes, axis=0).astype(np.float32)

        # Load segmentation ground truth if available
        seg_match = list(pdir.glob("*seg.nii*")) or list(pdir.glob("*SEG.nii*"))
        if seg_match:
            seg_vol, affine, meta = load_nifti_volume(str(seg_match[0]))
            seg_vol = convert_brats_labels_to_standard(seg_vol)
            seg_res = resample_volume(seg_vol, self.target_shape, is_mask=True).astype(np.int64)
        else:
            seg_res = np.zeros(self.target_shape, dtype=np.int64)

        # Data augmentation
        if self.transform:
            image_4d, seg_res = self._apply_augmentation(image_4d, seg_res)

        sample = {
            "image": torch.from_numpy(image_4d) if HAS_TORCH else image_4d,
            "mask": torch.from_numpy(seg_res) if HAS_TORCH else seg_res,
            "patient_id": pdir.name
        }
        return sample

    def _apply_augmentation(self, img: np.ndarray, mask: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        # Random 3D flips along spatial axes
        for axis in (1, 2, 3):
            if random.random() > 0.5:
                img = np.flip(img, axis=axis).copy()
                mask = np.flip(mask, axis=axis - 1).copy()
        
        # Intensity scaling
        if random.random() > 0.5:
            scale = random.uniform(0.9, 1.1)
            img = img * scale

        return img, mask

def scan_dataset_directory(dataset_dir: str) -> List[Path]:
    """Finds all valid patient directories containing MRI scans."""
    path = Path(dataset_dir)
    if not path.exists():
        return []
    patient_dirs = [p for p in path.iterdir() if p.is_dir() and not p.name.startswith(".")]
    return sorted(patient_dirs)

def split_patients(
    patient_dirs: List[Path],
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    seed: int = 42
) -> Tuple[List[Path], List[Path], List[Path]]:
    """Splits at patient level to strictly prevent data leakage."""
    rng = random.Random(seed)
    shuffled = list(patient_dirs)
    rng.shuffle(shuffled)

    n_total = len(shuffled)
    n_train = int(n_total * train_ratio)
    n_val = int(n_total * val_ratio)

    train_pts = shuffled[:n_train]
    val_pts = shuffled[n_train:n_train + n_val]
    test_pts = shuffled[n_train + n_val:]
    return train_pts, val_pts, test_pts

def generate_synthetic_brain_scan(
    shape: Tuple[int, int, int] = (128, 128, 128),
    has_tumor: bool = True,
    seed: Optional[int] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generates a realistic synthetic 3D brain MRI phantom with multi-contrast tissues
    and BraTS-style multi-class tumor regions:
    Labels:
    0: Background air
    1: Necrotic / Non-enhancing core
    2: Edema
    4: Enhancing tumor
    Returns:
        image: (4, D, H, W) with T1, T1ce, T2, FLAIR contrast simulation
        mask: (D, H, W) integer labels {0, 1, 2, 4}
    """
    if seed is not None:
        random.seed(seed)
        if HAS_TORCH:
            torch.manual_seed(seed)

    d, h, w = shape
    zz, yy, xx = np.ogrid[:d, :h, :w]
    cz, cy, cx = d // 2, h // 2, w // 2

    # Brain ellipsoid mask
    rz, ry, rx = d * 0.38, h * 0.42, w * 0.36
    brain_dist = ((zz - cz) / rz)**2 + ((yy - cy) / ry)**2 + ((xx - cx) / rx)**2
    brain_mask = brain_dist <= 1.0

    # Ventricles (central CSF)
    vz, vy, vx = d * 0.15, h * 0.10, w * 0.08
    csf_dist = ((zz - cz) / vz)**2 + ((yy - (cy - 5)) / vy)**2 + ((xx - cx) / vx)**2
    csf_mask = (csf_dist <= 1.0) & brain_mask

    # Modalities: [0: T1, 1: T1ce, 2: T2, 3: FLAIR]
    image = np.zeros((4, d, h, w), dtype=np.float32)

    # Brain parenchyma
    image[0][brain_mask] = 0.65  # T1
    image[1][brain_mask] = 0.65  # T1ce
    image[2][brain_mask] = 0.45  # T2
    image[3][brain_mask] = 0.50  # FLAIR

    # CSF / Ventricles
    image[0][csf_mask] = 0.15  # T1: dark
    image[1][csf_mask] = 0.15  # T1ce: dark
    image[2][csf_mask] = 0.95  # T2: bright
    image[3][csf_mask] = 0.10  # FLAIR: dark

    mask = np.zeros(shape, dtype=np.int64)

    if has_tumor:
        tz = cz + int(d * 0.08)
        ty = cy + int(h * 0.10)
        tx = cx + int(w * 0.14)

        # 1. Edema (Outer ring, label 2)
        ed_r = d * 0.16
        ed_dist = ((zz - tz)**2 + (yy - ty)**2 + (xx - tx)**2) / (ed_r**2)
        ed_mask = (ed_dist <= 1.0) & brain_mask & (~csf_mask)
        mask[ed_mask] = 2
        image[2][ed_mask] = 0.88
        image[3][ed_mask] = 0.92

        # 2. Enhancing tumor rim (label 4)
        et_r = d * 0.10
        et_dist = ((zz - tz)**2 + (yy - ty)**2 + (xx - tx)**2) / (et_r**2)
        et_mask = (et_dist <= 1.0) & brain_mask
        mask[et_mask] = 4
        image[1][et_mask] = 1.15
        image[0][et_mask] = 0.70
        image[2][et_mask] = 0.75
        image[3][et_mask] = 0.80

        # 3. Necrotic core (Central core, label 1)
        nc_r = d * 0.05
        nc_dist = ((zz - tz)**2 + (yy - ty)**2 + (xx - tx)**2) / (nc_r**2)
        nc_mask = (nc_dist <= 1.0) & brain_mask
        mask[nc_mask] = 1
        image[0][nc_mask] = 0.30
        image[1][nc_mask] = 0.35
        image[2][nc_mask] = 0.85
        image[3][nc_mask] = 0.70

    # Add realistic MRI noise using torch without numpy.random
    if HAS_TORCH:
        noise = (torch.randn(image.shape) * 0.03).numpy().astype(np.float32)
    else:
        noise = np.zeros_like(image)
        
    image = np.clip(image + noise, 0.0, None)
    image[:, ~brain_mask] = 0.0

    return image, mask
