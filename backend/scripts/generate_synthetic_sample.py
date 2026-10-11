import sys
from pathlib import Path
import numpy as np

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.ml.dataset import generate_synthetic_brain_scan
from app.utils.nifti_io import save_nifti_mask

def main():
    print("[*] Generating synthetic BraTS phantom sample scans...")
    samples_dir = backend_dir.parent / "data" / "samples"
    samples_dir.mkdir(parents=True, exist_ok=True)

    # Generate 128x128x128 phantom
    img_4d, mask_3d = generate_synthetic_brain_scan(shape=(128, 128, 128), has_tumor=True, seed=101)

    # 1.0mm isotropic affine
    affine = np.diag([1.0, 1.0, 1.0, 1.0])

    # Save FLAIR modality (index 3)
    flair_path = samples_dir / "sample_phantom_brats_flair.nii.gz"
    save_nifti_mask(img_4d[3] * 1000.0, affine, str(flair_path))
    print(f"[OK] Saved sample FLAIR: {flair_path}")

    # Save T1ce modality (index 1)
    t1ce_path = samples_dir / "sample_phantom_brats_t1ce.nii.gz"
    save_nifti_mask(img_4d[1] * 1000.0, affine, str(t1ce_path))
    print(f"[OK] Saved sample T1ce: {t1ce_path}")

    # Save Ground Truth Segmentation mask
    seg_path = samples_dir / "sample_phantom_brats_seg.nii.gz"
    save_nifti_mask(mask_3d, affine, str(seg_path))
    print(f"[OK] Saved sample Ground Truth Mask: {seg_path}")

if __name__ == "__main__":
    main()
