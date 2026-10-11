import os
import sys
import json
import time
import argparse
import random
import numpy as np
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

try:
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader, TensorDataset
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

from app.ml.model import create_model
from app.ml.dataset import BraTSDataset, scan_dataset_directory, split_patients, generate_synthetic_brain_scan
from app.ml.evaluate import compute_binary_dice

class SimpleAdam:
    """Robust standalone Adam optimizer without torch._dynamo dependencies."""
    def __init__(self, params, lr: float = 1e-4, beta1: float = 0.9, beta2: float = 0.999, eps: float = 1e-8, weight_decay: float = 1e-5):
        self.params = [p for p in params if p.requires_grad]
        self.lr = lr
        self.beta1 = beta1
        self.beta2 = beta2
        self.eps = eps
        self.weight_decay = weight_decay
        self.m = [torch.zeros_like(p.data) for p in self.params]
        self.v = [torch.zeros_like(p.data) for p in self.params]
        self.t = 0

    def step(self):
        self.t += 1
        with torch.no_grad():
            for i, p in enumerate(self.params):
                if p.grad is None:
                    continue
                g = p.grad.data
                if self.weight_decay > 0:
                    g = g + self.weight_decay * p.data

                self.m[i] = self.beta1 * self.m[i] + (1.0 - self.beta1) * g
                self.v[i] = self.beta2 * self.v[i] + (1.0 - self.beta2) * (g * g)

                m_hat = self.m[i] / (1.0 - (self.beta1 ** self.t))
                v_hat = self.v[i] / (1.0 - (self.beta2 ** self.t))

                p.data -= self.lr * m_hat / (torch.sqrt(v_hat) + self.eps)

    def zero_grad(self):
        for p in self.params:
            if p.grad is not None:
                p.grad.zero_()

class DiceLoss(nn.Module if HAS_TORCH else object):
    """Soft Dice Loss for multi-class 3D segmentation."""
    def __init__(self, smooth: float = 1e-5):
        super().__init__()
        self.smooth = smooth

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        probs = torch.softmax(logits, dim=1)
        targets_one_hot = torch.zeros_like(logits)
        targets_one_hot.scatter_(1, targets.unsqueeze(1), 1)

        dims = (0, 2, 3, 4)
        intersection = torch.sum(probs * targets_one_hot, dims)
        cardinality = torch.sum(probs + targets_one_hot, dims)

        dice_score = (2.0 * intersection + self.smooth) / (cardinality + self.smooth)
        return 1.0 - torch.mean(dice_score)

class CombinedLoss(nn.Module if HAS_TORCH else object):
    """Combines Cross Entropy with Dice Loss to optimize both voxel accuracy and boundary overlap."""
    def __init__(self, weight_dice: float = 0.5, class_weights: Optional[torch.Tensor] = None):
        super().__init__()
        self.weight_dice = weight_dice
        self.dice_loss = DiceLoss()
        self.ce_loss = nn.CrossEntropyLoss(weight=class_weights)

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        loss_ce = self.ce_loss(logits, targets)
        loss_dice = self.dice_loss(logits, targets)
        return (1.0 - self.weight_dice) * loss_ce + self.weight_dice * loss_dice

def set_seed(seed: int = 42):
    random.seed(seed)
    if HAS_TORCH:
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)

def create_synthetic_dataloader(num_samples: int = 16, shape: Tuple[int, int, int] = (64, 64, 64), batch_size: int = 2):
    """Creates an in-memory synthetic dataset for training and verification."""
    images = []
    masks = []
    for i in range(num_samples):
        img, msk = generate_synthetic_brain_scan(shape=shape, has_tumor=(i % 4 != 0), seed=42 + i)
        msk_class = np.copy(msk)
        msk_class[msk == 4] = 3
        images.append(img)
        masks.append(msk_class)

    img_tensor = torch.from_numpy(np.stack(images, axis=0)).float()
    mask_tensor = torch.from_numpy(np.stack(masks, axis=0)).long()
    dataset = TensorDataset(img_tensor, mask_tensor)
    return DataLoader(dataset, batch_size=batch_size, shuffle=True)

def train_pipeline(
    data_dir: Optional[str] = None,
    output_dir: str = "models",
    epochs: int = 5,
    batch_size: int = 2,
    learning_rate: float = 1e-4,
    use_synthetic: bool = False,
    architecture: str = "3d_unet"
) -> Dict[str, Any]:
    """Runs end-to-end training pipeline and exports checkpoint and metrics."""
    if not HAS_TORCH:
        raise RuntimeError("PyTorch is required to run the training pipeline.")

    set_seed(42)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[*] Training on device: {device} | Architecture: {architecture}")

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # 1. Dataset loading
    if use_synthetic or not data_dir or not Path(data_dir).exists():
        print("[*] Using synthetic brain scan volume fixtures for training verification.")
        train_loader = create_synthetic_dataloader(num_samples=4, shape=(32, 32, 32), batch_size=batch_size)
        val_loader = create_synthetic_dataloader(num_samples=2, shape=(32, 32, 32), batch_size=batch_size)
    else:
        patient_dirs = scan_dataset_directory(data_dir)
        train_pts, val_pts, test_pts = split_patients(patient_dirs)
        print(f"[*] Patients split: Train={len(train_pts)}, Val={len(val_pts)}, Test={len(test_pts)}")
        train_ds = BraTSDataset(train_pts, target_shape=(128, 128, 128), is_training=True)
        val_ds = BraTSDataset(val_pts, target_shape=(128, 128, 128), is_training=False)
        train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False)

    # 2. Model initialization
    model = create_model(architecture=architecture, in_channels=4, out_channels=4, base_filters=16, device=device)
    optimizer = SimpleAdam(model.parameters(), lr=learning_rate)
    criterion = CombinedLoss()

    history = []
    best_dice = 0.0
    best_checkpoint_path = out_path / "unet3d_brats_best.pt"

    for epoch in range(1, epochs + 1):
        model.train()
        train_losses = []
        for batch in train_loader:
            if isinstance(batch, (list, tuple)):
                imgs, msks = batch[0].to(device), batch[1].to(device)
            else:
                imgs, msks = batch["image"].to(device), batch["mask"].to(device)

            optimizer.zero_grad()
            logits = model(imgs)
            loss = criterion(logits, msks)
            loss.backward()
            optimizer.step()
            train_losses.append(loss.item())

        epoch_loss = float(np.mean(train_losses))

        # Validation
        model.eval()
        val_dices = []
        with torch.no_grad():
            for batch in val_loader:
                if isinstance(batch, (list, tuple)):
                    imgs, msks = batch[0].to(device), batch[1].to(device)
                else:
                    imgs, msks = batch["image"].to(device), batch["mask"].to(device)
                logits = model(imgs)
                preds = torch.argmax(logits, dim=1)
                
                # Whole Tumor Dice (classes > 0)
                pred_wt = (preds > 0).cpu().numpy()
                gt_wt = (msks > 0).cpu().numpy()
                val_dices.append(compute_binary_dice(pred_wt, gt_wt))

        mean_val_dice = float(np.mean(val_dices))
        print(f"Epoch {epoch}/{epochs} | Train Loss: {epoch_loss:.4f} | Val WT Dice: {mean_val_dice:.4f}")

        history.append({
            "epoch": epoch,
            "train_loss": round(epoch_loss, 4),
            "val_dice": round(mean_val_dice, 4)
        })

        if mean_val_dice >= best_dice or epoch == 1:
            best_dice = mean_val_dice
            torch.save({
                "epoch": epoch,
                "architecture": architecture,
                "in_channels": 4,
                "out_channels": 4,
                "state_dict": model.state_dict(),
                "best_dice": best_dice
            }, str(best_checkpoint_path))

    metrics_file = out_path / "evaluation_metrics.json"
    metrics_summary = {
        "dataset_name": "Synthetic BraTS Phantom / Real BraTS Split",
        "training_epochs": epochs,
        "best_val_dice": round(best_dice, 4),
        "history": history,
        "export_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    metrics_file.write_text(json.dumps(metrics_summary, indent=2))
    print(f"[OK] Checkpoint saved: {best_checkpoint_path}")
    print(f"[OK] Metrics exported: {metrics_file}")
    return metrics_summary

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NeuroScan AI 3D U-Net Training Pipeline")
    parser.add_argument("--data_dir", type=str, default=None, help="Path to BraTS patient directories")
    parser.add_argument("--output_dir", type=str, default="models", help="Output directory for checkpoints")
    parser.add_argument("--epochs", type=int, default=2, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=2, help="Batch size")
    parser.add_argument("--lr", type=float, default=1e-4, help="Learning rate")
    parser.add_argument("--synthetic", action="store_true", help="Use synthetic dataset for verification")
    parser.add_argument("--arch", type=str, default="3d_unet", help="Architecture: 3d_unet or attention_unet")
    args = parser.parse_args()

    train_pipeline(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        use_synthetic=args.synthetic,
        architecture=args.arch
    )
