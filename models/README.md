# NeuroScan AI — Model Checkpoints

This directory houses trained PyTorch model checkpoints and evaluation metric benchmark logs.

## Expected Files

- **`unet3d_brats_best.pt`**: Trained 3D U-Net or Attention 3D U-Net PyTorch checkpoint dictionary.
  - State Dictionary keys:
    - `epoch`: integer representing best validation epoch.
    - `architecture`: `"3d_unet"` or `"attention_3d_unet"`
    - `in_channels`: `4` (T1, T1ce, T2, FLAIR)
    - `out_channels`: `4` (0: BG, 1: NCR/NET, 2: ED, 3: ET)
    - `state_dict`: Model weights tensor dictionary.
    - `best_dice`: Floating point Dice similarity score on validation set.
- **`evaluation_metrics.json`**: Validation performance statistics, per-class Dice scores, IoU, Sensitivity, Specificity, HD95, and training/validation epoch progression curves.

## How to Place a Trained Checkpoint from Google Colab

1. Run the training notebook at `notebooks/train_brain_tumor_segmentation.ipynb` in Google Colab with GPU runtime.
2. Download the saved `unet3d_brats_best.pt` from your Google Drive.
3. Copy it into this folder: `models/unet3d_brats_best.pt`.
4. The NeuroScan AI backend automatically detects the checkpoint at startup or next inference query!
