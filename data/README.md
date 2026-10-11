# NeuroScan AI — MRI Data & Samples

This directory contains research dataset guidelines and pre-computed synthetic phantom volumes.

## Directory Structure

```
data/
  samples/
    sample_phantom_brats_flair.nii.gz
    sample_phantom_brats_t1ce.nii.gz
    sample_phantom_brats_seg.nii.gz
  BraTS2020/ (Optional: User-imported full dataset)
```

## BraTS Protocol Conventions

BraTS (Brain Tumor Segmentation Challenge) provides 4 co-registered, skull-stripped MRI volumes for each patient:
1. `*_flair.nii.gz`: T2-weighted Fluid Attenuated Inversion Recovery
2. `*_t1.nii.gz`: T1-weighted native
3. `*_t1ce.nii.gz`: T1-weighted contrast-enhanced (Gadolinium)
4. `*_t2.nii.gz`: T2-weighted native
5. `*_seg.nii.gz`: Voxel ground truth with discrete integer annotations:
   - **Label 0**: Background / Healthy Brain Parenchyma
   - **Label 1**: Necrotic Core & Non-Enhancing Tumor (NCR/NET)
   - **Label 2**: Peritumoral Edema (ED)
   - **Label 4**: GD-Enhancing Tumor (ET)

## Synthetic Phantoms

For offline verification without downloading the ~20GB BraTS dataset, pre-generated 128×128×128 synthetic multi-compartment glioblastoma phantoms are stored in `data/samples/`. Users can load them via the UI dropzone with a single click.
