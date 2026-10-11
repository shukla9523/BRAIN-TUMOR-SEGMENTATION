import React from 'react';
import {
  Brain,
  Layers,
  Activity,
  ShieldAlert,
  Database,
  Cpu,
  FileCode2,
  Lock,
  GitBranch,
  BookOpen
} from 'lucide-react';

export const AboutPage: React.FC = () => {
  return (
    <div className="space-y-10 py-6 max-w-4xl mx-auto">
      {/* Title */}
      <div className="space-y-2 pb-4 border-b border-slate-200 dark:border-slate-800">
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white">
          Methodology, Architecture & Research Ethics
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400">
          Technical specifications, neural network mechanics, and responsible AI guardrails
        </p>
      </div>

      {/* 3D U-Net Architectural Blueprint */}
      <section className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 shadow-sm space-y-4">
        <div className="flex items-center gap-2 text-blue-600 dark:text-blue-400">
          <Brain className="w-5 h-5" />
          <h2 className="text-base font-bold text-slate-900 dark:text-white">
            1. Volumetric 3D U-Net Architecture
          </h2>
        </div>
        <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          The core model is an encoder-decoder 3D Convolutional Neural Network designed specifically for multi-sequence
          magnetic resonance volumetric data. Unlike 2D slice-by-slice models that discard out-of-plane anatomical context,
          the 3D U-Net directly computes 3D spatial convolutions across axial, coronal, and sagittal dimensions simultaneously.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs pt-2">
          <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800 space-y-1">
            <span className="font-bold text-slate-900 dark:text-white">DoubleConv3D Blocks</span>
            <p className="text-slate-500 dark:text-slate-400">
              Two successive 3×3×3 3D convolutions paired with 3D Instance Normalization and LeakyReLU activations
              (negative slope = 0.01).
            </p>
          </div>

          <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800 space-y-1">
            <span className="font-bold text-slate-900 dark:text-white">Residual Skip Pathways</span>
            <p className="text-slate-500 dark:text-slate-400">
              High-resolution spatial feature maps from the encoder are concatenated across lateral skip connections to
              the upsampled decoder layers.
            </p>
          </div>

          <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800 space-y-1">
            <span className="font-bold text-slate-900 dark:text-white">Attention Gate Variant</span>
            <p className="text-slate-500 dark:text-slate-400">
              Additive 3D Attention Gates selectively emphasize relevant tumor boundary features while suppressing
              background healthy parenchyma noise.
            </p>
          </div>

          <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800 space-y-1">
            <span className="font-bold text-slate-900 dark:text-white">Combined Objective Function</span>
            <p className="text-slate-500 dark:text-slate-400">
              L = 0.5 × Soft Dice Loss + 0.5 × Cross-Entropy Loss to balance voxel-level categorization with boundary
              region overlap.
            </p>
          </div>
        </div>
      </section>

      {/* Medical Preprocessing Pipeline */}
      <section className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 shadow-sm space-y-4">
        <div className="flex items-center gap-2 text-indigo-600 dark:text-indigo-400">
          <Layers className="w-5 h-5" />
          <h2 className="text-base font-bold text-slate-900 dark:text-white">
            2. Medical Preprocessing & Coordinate Preservation
          </h2>
        </div>
        <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          Medical scans must never be rescaled or stretched arbitrarily like photographic images. The pipeline strictly
          preserves physical spatial geometry:
        </p>

        <ul className="space-y-2 text-xs text-slate-600 dark:text-slate-400 list-disc list-inside">
          <li>
            <strong className="text-slate-800 dark:text-slate-200">Orientation Canonicalization:</strong> Reorients
            incoming volumes to standard RAS+ coordinates using the NIfTI sform/qform affine transformation matrix.
          </li>
          <li>
            <strong className="text-slate-800 dark:text-slate-200">Intensity Percentile Clipping:</strong> Clips extreme
            scanner radiofrequency artifacts between the 1st and 99th percentiles of foreground brain voxels.
          </li>
          <li>
            <strong className="text-slate-800 dark:text-slate-200">Patient-Level Z-Score Normalization:</strong> Centers
            foreground brain intensities to zero mean and unit variance per sequence.
          </li>
          <li>
            <strong className="text-slate-800 dark:text-slate-200">Geometry Restoration:</strong> Model outputs are mapped
            back into the patient's original voxel grid dimensions and spacing using nearest-neighbor discrete label interpolation.
          </li>
        </ul>
      </section>

      {/* Research Ethics & Privacy */}
      <section className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 shadow-sm space-y-4">
        <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400">
          <Lock className="w-5 h-5" />
          <h2 className="text-base font-bold text-slate-900 dark:text-white">
            3. Data Hygiene & Security Controls
          </h2>
        </div>
        <div className="space-y-2 text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          <p>
            • <strong>Protected Health Information (PHI) Hygiene:</strong> Users must de-identify and strip all DICOM/NIfTI
            patient metadata headers (patient name, MRN, date of birth) before uploading files to research systems.
          </p>
          <p>
            • <strong>No Unconsented Long-Term Cloud Storage:</strong> All uploaded files and intermediate segmentation masks
            are placed in temporary storage directories with randomized identifiers and automatic cleanup routines.
          </p>
          <p>
            • <strong>No External Network Uploads:</strong> Scan inference runs strictly within the designated backend service
            without streaming volumetric data to third-party commercial APIs.
          </p>
        </div>
      </section>

      {/* Intended Use & Clinical Limitations */}
      <section className="bg-amber-50 dark:bg-amber-950/40 rounded-2xl border border-amber-200 dark:border-amber-900/50 p-6 space-y-3 text-xs text-amber-900 dark:text-amber-200">
        <div className="flex items-center gap-2 text-amber-700 dark:text-amber-300">
          <ShieldAlert className="w-5 h-5 shrink-0" />
          <h3 className="font-bold text-sm uppercase tracking-wide">
            Intended Use Statement & Clinical Limitations
          </h3>
        </div>
        <p className="leading-relaxed">
          NeuroScan AI is strictly an academic, research, and benchmarking software prototype. It is NOT certified by the
          FDA, CE, or any regulatory medical device authority for diagnostic use. Automated segmentation predictions are
          subject to variation caused by scanner manufacturer, field strength (1.5T vs 3.0T), patient motion, and imaging artifacts.
        </p>
        <p className="font-semibold text-amber-800 dark:text-amber-300">
          NEVER make clinical diagnostic, biopsy, surgical planning, or chemotherapy decisions based on software outputs
          without review by a licensed radiologist and clinical care team.
        </p>
      </section>
    </div>
  );
};
