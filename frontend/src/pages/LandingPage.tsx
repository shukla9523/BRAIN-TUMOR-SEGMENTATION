import React from 'react';
import {
  ShieldAlert,
  ArrowRight,
  BarChart3,
  Sparkles
} from 'lucide-react';

interface Props {
  onStartAnalysis: () => void;
  onExploreEvaluation: () => void;
  modelAvailable: boolean;
}

export const LandingPage: React.FC<Props> = ({
  onStartAnalysis,
  onExploreEvaluation,
  modelAvailable,
}) => {
  return (
    <div className="space-y-16 py-8">
      {/* Hero Section */}
      <section className="relative overflow-hidden rounded-3xl bg-gradient-to-b from-blue-900/10 via-slate-900/5 to-transparent dark:from-blue-950/40 p-8 sm:p-14 border border-blue-500/20">
        <div className="max-w-4xl mx-auto text-center space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-blue-100 dark:bg-blue-950 text-blue-700 dark:text-blue-300 text-xs font-semibold border border-blue-200 dark:border-blue-800">
            <Sparkles className="w-3.5 h-3.5 text-blue-500" />
            <span>Deep Learning 3D U-Net Volumetric Platform</span>
          </div>

          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black text-slate-900 dark:text-white tracking-tight leading-tight">
            NeuroScan <span className="text-blue-600 dark:text-blue-400">AI</span>
          </h1>

          <p className="text-base sm:text-lg text-slate-600 dark:text-slate-300 max-w-2xl mx-auto leading-relaxed">
            An open research prototype for automated volumetric brain tumor segmentation on multimodal MRI scans
            (T1, T1ce, T2, FLAIR). Provides quantitative subregion volumetrics with strict clinical transparency.
          </p>

          {/* Action CTAs */}
          <div className="flex flex-wrap items-center justify-center gap-4 pt-4">
            <button
              onClick={onStartAnalysis}
              className="px-6 py-3.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm shadow-lg shadow-blue-500/25 flex items-center gap-2 hover:gap-3 transition-all"
            >
              <span>Launch MRI Workspace</span>
              <ArrowRight className="w-4 h-4" />
            </button>

            <button
              onClick={onExploreEvaluation}
              className="px-6 py-3.5 rounded-xl bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-750 text-slate-800 dark:text-slate-200 font-semibold text-sm border border-slate-200 dark:border-slate-700 flex items-center gap-2 transition-all"
            >
              <BarChart3 className="w-4 h-4 text-blue-500" />
              <span>View Benchmark Metrics</span>
            </button>
          </div>

          {/* Model Status Pill */}
          <div className="pt-4 flex items-center justify-center gap-2 text-xs text-slate-500 dark:text-slate-400">
            <span
              className={`w-2 h-2 rounded-full ${
                modelAvailable ? 'bg-emerald-500' : 'bg-amber-500'
              }`}
            />
            <span>
              {modelAvailable
                ? 'Model Checkpoint Loaded and Ready'
                : 'Checkpoint Offline: Train in Colab or load research sample phantom'}
            </span>
          </div>
        </div>
      </section>

      {/* How the System Works */}
      <section className="space-y-8">
        <div className="text-center space-y-2 max-w-2xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white">
            End-to-End Medical Imaging Pipeline
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Engineered adhering to medical imaging best practices and the BraTS segmentation protocol.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 shadow-sm space-y-3">
            <div className="w-10 h-10 rounded-xl bg-blue-50 dark:bg-blue-950 text-blue-600 dark:text-blue-400 flex items-center justify-center font-bold">
              1
            </div>
            <h3 className="text-base font-bold text-slate-900 dark:text-white">
              NIfTI Ingestion & Preprocessing
            </h3>
            <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
              Validates 3D voxel dimensions, spacing, and spatial orientation. Reorients to RAS+ canonical axes,
              performs foreground intensity percentile clipping (1%–99%), and patient-level z-score normalization.
            </p>
          </div>

          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 shadow-sm space-y-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-50 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-400 flex items-center justify-center font-bold">
              2
            </div>
            <h3 className="text-base font-bold text-slate-900 dark:text-white">
              3D U-Net Deep Learning
            </h3>
            <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
              Processes volumetric image patches through a 3D U-Net with Instance Normalization and LeakyReLU.
              Predicts 4 output classes: Background (0), Necrotic Core (1), Edema (2), and Enhancing Tumor (4).
            </p>
          </div>

          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 shadow-sm space-y-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-50 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400 flex items-center justify-center font-bold">
              3
            </div>
            <h3 className="text-base font-bold text-slate-900 dark:text-white">
              Volumetrics & PDF Report
            </h3>
            <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
              Restores predictions back into original patient geometry without spatial distortion.
              Computes physical volumes in cm³, multi-planar slice overlays, and generates formal research PDF summaries.
            </p>
          </div>
        </div>
      </section>

      {/* BraTS Subregions Breakdown */}
      <section className="bg-slate-50 dark:bg-slate-900/40 rounded-3xl border border-slate-200 dark:border-slate-800 p-8 space-y-6">
        <h3 className="text-lg font-bold text-slate-900 dark:text-white">
          BraTS Tumor Subregion Definitions
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800 space-y-2">
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-blue-600" />
              <span className="text-xs font-bold text-slate-900 dark:text-white">Whole Tumor (WT)</span>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Labels 1 + 2 + 4. Complete pathological extent including peritumoral edema, necrotic core, and enhancing tissue.
            </p>
          </div>

          <div className="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800 space-y-2">
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-red-600" />
              <span className="text-xs font-bold text-slate-900 dark:text-white">Tumor Core (TC)</span>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Labels 1 + 4. The gross tumor bulk consisting of necrotic non-enhancing core and gadolinium-enhancing tissue.
            </p>
          </div>

          <div className="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800 space-y-2">
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-amber-500" />
              <span className="text-xs font-bold text-slate-900 dark:text-white">Enhancing Tumor (ET)</span>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Label 4. Hyperintense active rim on post-contrast T1-weighted images with disrupted blood-brain barrier.
            </p>
          </div>
        </div>
      </section>

      {/* Prominent Research Notice Callout */}
      <section className="bg-amber-50 dark:bg-amber-950/30 rounded-2xl border border-amber-200 dark:border-amber-900/50 p-6 flex items-start gap-4 text-xs text-amber-900 dark:text-amber-200">
        <ShieldAlert className="w-6 h-6 text-amber-600 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <h4 className="font-bold text-amber-800 dark:text-amber-300 uppercase tracking-wide">
            Clinical Investigation Notice & Limitations
          </h4>
          <p className="leading-relaxed">
            NeuroScan AI is created strictly for academic research and educational evaluation. It is never intended
            to replace professional radiological evaluation. Histological diagnosis, cancer grade, and treatment
            pathways cannot and should never be determined from segmentation masks alone.
          </p>
        </div>
      </section>
    </div>
  );
};
