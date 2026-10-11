# NeuroScan AI — Brain Tumor Segmentation Platform

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-blue.svg)](https://python.org)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.x-orange.svg)](https://pytorch.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-blue.svg)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-6.x-purple.svg)](https://vitejs.dev)
[![TailwindCSS](https://img.shields.io/badge/Tailwind-3.4-38bdf8.svg)](https://tailwindcss.com)
[![License](https://img.shields.io/badge/License-MIT-lightgrey.svg)](LICENSE)

An end-to-end medical AI research platform for volumetric 3D brain tumor segmentation on multimodal MRI scans (T1, T1ce, T2, FLAIR). **NeuroScan AI** pairs a 3D U-Net deep learning pipeline with an interactive multi-planar radiology viewer, quantitative volumetric measurements, and PDF research report generation.

---

### ⚠️ Regulatory & Clinical Research Disclaimer
> **RESEARCH & EDUCATIONAL PROTOTYPE ONLY**: NeuroScan AI is not an FDA-approved or CE-marked medical device. It must **NEVER** be used as a primary diagnostic tool for patient management, biopsy guidance, surgical resection, or oncological treatment planning. All volumetric estimations are mathematical voxel approximations. Definitive radiological diagnosis must always be established by a board-certified radiologist or clinical physician.

---

## 1. Architectural Highlights

```
                          ┌──────────────────────────┐
                          │   NIfTI Scan (.nii/.gz)   │
                          └─────────────┬────────────┘
                                        │
                                        ▼
   ┌────────────────────────────────────────────────────────────────────────┐
   │                     Medical Preprocessing Pipeline                     │
   │  • RAS+ Coordinate Canonicalization   • Non-Zero Bounding Box Crop     │
   │  • Foreground Percentile Clip (1-99%) • Z-Score Intensity Normalization│
   └────────────────────────────────────┬───────────────────────────────────┘
                                        │
                                        ▼
   ┌────────────────────────────────────────────────────────────────────────┐
   │                       3D U-Net Deep Learning                           │
   │  • 4 Input Channels: T1, T1ce, T2, FLAIR                               │
   │  • 3D InstanceNorm + LeakyReLU Blocks                                  │
   │  • Residual Skip Connections / Additive 3D Attention Gates             │
   │  • 4 Output Classes: Background (0), NCR/NET (1), ED (2), ET (4)       │
   └────────────────────────────────────┬───────────────────────────────────┘
                                        │
                                        ▼
   ┌────────────────────────────────────────────────────────────────────────┐
   │                   Postprocessing & Quantitative Engine                 │
   │  • Nearest-Neighbor Geometry Restoration to Patient Space              │
   │  • Physical Volume: V = (Voxel Count × sx × sy × sz) / 1000 (cm³)      │
   │  • Subregion Hierarchies: WT (1+2+4), TC (1+4), ET (4)                 │
   │  • Connected Component Lesion Enumeration                              │
   └────────────────────────────────────┬───────────────────────────────────┘
                                        │
                     ┌──────────────────┴──────────────────┐
                     ▼                                     ▼
   ┌──────────────────────────────────┐  ┌──────────────────────────────────┐
   │    Three-Plane Radiology Viewer  │  │    PDF Research Report Generator │
   │  • Axial, Coronal, Sagittal      │  │  • Multi-Planar Thumbnails       │
   │  • Windowing (Brightness/Contrast│  │  • Quantitative Voxel Tables     │
   │  • Subregion Toggles & Opacity   │  │  • Formal Medical Disclaimers    │
   └──────────────────────────────────┘  └──────────────────────────────────┘
```

---

## 2. Technology Stack

- **Frontend**:
  - React 19 with Vite & TypeScript
  - Tailwind CSS with custom medical color palette and dark/light modes
  - Recharts for volumetric bar charts and benchmark metrics curves
  - Lucide React for medical iconography
- **Backend**:
  - Python 3.11 / 3.12 with FastAPI & Uvicorn
  - PyTorch 2.x for 3D tensor convolutions and spatial interpolation
  - NiBabel for NIfTI-1 volumetric file parsing
  - NumPy, SciPy, Pillow, scikit-learn
  - ReportLab Platypus for PDF research report generation
  - Pytest & HTTPX for automated testing
- **AI Model**:
  - 3D U-Net and 3D Attention U-Net architectures
  - BraTS-style multi-class hierarchical segmentation
  - Combined Soft Dice + Cross-Entropy Loss

---

## 3. Quick Start: Windows Setup

### Prerequisites
- Python 3.11 or 3.12 ([python.org](https://www.python.org/downloads/))
- Node.js 18+ and npm ([nodejs.org](https://nodejs.org/))

### Step 1: Clone or Navigate to the Project
```powershell
cd "c:\Users\BIT\Desktop\BRAIN TUMOR SEGMENTATION"
```

### Step 2: Install Backend Dependencies
```powershell
# Install backend requirements
python -m pip install -r backend/requirements.txt
```

### Step 3: Install Frontend Dependencies
```powershell
cd frontend
npm install
cd ..
```

### Step 4: Generate Synthetic Sample Scans & Benchmark Metrics
To test immediately without needing external 20GB MRI files:
```powershell
python backend/scripts/generate_synthetic_sample.py
python backend/scripts/export_evaluation_metrics.py
```

### Step 5: Start the Backend API Server
In terminal 1:
```powershell
$env:PYTHONPATH="backend"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
The FastAPI OpenAPI documentation is available at: **http://127.0.0.1:8000/docs**

### Step 6: Start the React Frontend Development Server
In terminal 2:
```powershell
cd frontend
npm run dev
```
Open your browser at: **http://localhost:5173**

---

## 4. Google Colab Training Instructions

A complete, self-contained Google Colab training notebook is provided in:
`notebooks/train_brain_tumor_segmentation.ipynb`

### Step-by-Step Colab Instructions:
1. Open [Google Colab](https://colab.research.google.com).
2. Upload `notebooks/train_brain_tumor_segmentation.ipynb`.
3. Select **Runtime -> Change runtime type -> Hardware accelerator -> GPU (T4 or A100)**.
4. Mount your Google Drive to persist trained checkpoints:
   ```python
   from google.colab import drive
   drive.mount('/content/drive')
   ```
5. Place the BraTS 2020 or BraTS 2021 dataset in `/content/data/BraTS2020` (or use the built-in synthetic generator cell).
6. Run the cells in order:
   - Cell 1: Environment & GPU verification (`!nvidia-smi`)
   - Cell 2: Drive mount
   - Cell 3: Dataset loader & patient-level splitting
   - Cell 4: Intensity normalization & spatial resampling
   - Cell 5: 3D U-Net model instantiation
   - Cell 6: Combined Soft Dice + CE loss
   - Cell 7: Training loop with per-epoch validation
   - Cell 8: Checkpoint export to Google Drive
7. Download the exported `unet3d_brats_best.pt` checkpoint to your local machine and place it inside:
   `models/unet3d_brats_best.pt`
8. Restart or refresh NeuroScan AI. The model pill will immediately display **"Model Ready"**!

---

## 5. Backend REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Service health, compute device, model status, and disclaimer |
| `GET` | `/api/model-info` | 3D U-Net architecture, expected modalities, and checkpoint path |
| `POST` | `/api/upload` | Multipart file upload for `.nii` / `.nii.gz` scans with validation |
| `POST` | `/api/segment` | Initiates 3D segmentation inference job in background |
| `GET` | `/api/jobs/{job_id}` | Polls progress percentage and status of running segmentation |
| `GET` | `/api/results/{result_id}` | Retrieves quantitative measurements, volumes in cm³, and QC warnings |
| `GET` | `/api/results/{result_id}/mask` | Downloads predicted 3D segmentation mask as NIfTI (`.nii.gz`) |
| `GET` | `/api/results/{result_id}/report`| Downloads formal research summary PDF report |
| `GET` | `/api/results/{result_id}/slice/{index}` | Retrieves Base64 encoded slice with color segmentation overlay |
| `GET` | `/api/uploads/{upload_id}/slice/{index}` | Retrieves Base64 encoded slice to preview uploaded scan |
| `GET` | `/api/metrics` | Returns documented validation benchmark metrics and loss curves |
| `GET` | `/api/sample-scans` | Lists pre-packaged synthetic research phantoms |
| `POST` | `/api/sample-scans/load/{sample_id}` | Loads research phantom into an active upload session |

---

## 6. Running Automated Tests

Run the full automated test suite covering API endpoints, model architecture, metrics, volume calculations, and end-to-end inference:

```powershell
$env:PYTHONPATH="backend"
pytest backend/tests -v
```

All 23 unit and integration tests pass:
- `test_api.py`: Health, model-info, metrics, sample loading, slice previews, invalid file rejection
- `test_model.py`: 3D U-Net and Attention U-Net forward passes, output dimensions `(1, 4, 32, 32, 32)`
- `test_preprocessing.py`: Foreground z-score normalization, bounding box extraction, nearest-neighbor label resampling
- `test_metrics.py`: Dice similarity, IoU, sensitivity, specificity, empty ground-truth edge cases
- `test_volume.py`: Physical voxel-to-cm³ conversion, connected components, subregion hierarchical grouping
- `test_report.py`: PDF research report compilation with Platypus and metadata tables
- `test_end_to_end.py`: End-to-end workflow from synthetic phantom loading to 3D mask prediction and PDF generation

---

## 7. Docker Deployment

To launch the full production stack with Docker Compose:

```bash
docker-compose up --build
```
- **Backend API**: http://localhost:8000
- **Frontend App**: http://localhost:5173
