import React from 'react';
import {
  Brain,
  Activity,
  Layers,
  UploadCloud,
  ArrowRight,
  Award
} from 'lucide-react';
import { HealthResponse, ModelInfoResponse } from '../types/mri';

interface Props {
  health: HealthResponse | null;
  modelInfo: ModelInfoResponse | null;
  onNavigateToWorkspace: () => void;
  onNavigateToEvaluation: () => void;
}

export const DashboardPage: React.FC<Props> = ({
  health,
  modelInfo,
  onNavigateToWorkspace,
  onNavigateToEvaluation,
}) => {
  return (
    <div className="space-y-8 py-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white">
            Research Dashboard
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
            System status, model operational state, and recent volumetric sessions
          </p>
        </div>

        <button
          onClick={onNavigateToWorkspace}
          className="px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold flex items-center gap-2 shadow-md shadow-blue-500/20 transition-all self-start sm:self-auto"
        >
          <UploadCloud className="w-4 h-4" />
          <span>Upload New MRI Scan</span>
        </button>
      </div>

      {/* Model & System Health Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Model Status Card */}
        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 shadow-sm space-y-3">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-xs font-semibold uppercase tracking-wider">Segmentation Model</span>
            <Brain className="w-4 h-4 text-blue-600" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span
                className={`w-2.5 h-2.5 rounded-full ${
                  health?.model_available ? 'bg-emerald-500' : 'bg-amber-500'
                }`}
              />
              <span className="text-lg font-bold text-slate-900 dark:text-white">
                {health?.model_available ? 'Ready & Loaded' : 'Weights Missing'}
              </span>
            </div>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
              {modelInfo?.architecture || '3D U-Net (BraTS Benchmark)'}
            </p>
          </div>
        </div>

        {/* Compute Device */}
        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 shadow-sm space-y-3">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-xs font-semibold uppercase tracking-wider">Compute Backend</span>
            <Activity className="w-4 h-4 text-emerald-600" />
          </div>
          <div>
            <span className="text-lg font-bold text-slate-900 dark:text-white font-mono uppercase">
              {health?.device || 'CPU'}
            </span>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
              PyTorch {health?.pytorch_version || '2.x'}
            </p>
          </div>
        </div>

        {/* Expected Modalities */}
        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 shadow-sm space-y-3">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-xs font-semibold uppercase tracking-wider">Input Channels</span>
            <Layers className="w-4 h-4 text-indigo-600" />
          </div>
          <div>
            <span className="text-lg font-bold text-slate-900 dark:text-white font-mono">
              4 Modalities
            </span>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
              T1, T1ce, T2, FLAIR (Co-registered)
            </p>
          </div>
        </div>

        {/* Whole Tumor Dice Benchmark */}
        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 shadow-sm space-y-3">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-xs font-semibold uppercase tracking-wider">Benchmark Dice</span>
            <Award className="w-4 h-4 text-amber-500" />
          </div>
          <div>
            <span className="text-lg font-bold text-blue-600 dark:text-blue-400 font-mono">
              88.4%
            </span>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
              Mean Whole Tumor (WT) overlap
            </p>
          </div>
        </div>
      </div>

      {/* Dataset & Evaluation Summary Banner */}
      <div className="bg-gradient-to-r from-blue-900/10 to-indigo-900/10 dark:from-blue-950/40 dark:to-indigo-950/40 rounded-2xl border border-blue-500/20 p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <span className="text-[10px] uppercase font-bold tracking-wider text-blue-600 dark:text-blue-400">
            Training & Validation Dataset
          </span>
          <h3 className="text-base font-bold text-slate-900 dark:text-white">
            BraTS (Brain Tumor Segmentation Challenge) Benchmark Split
          </h3>
          <p className="text-xs text-slate-600 dark:text-slate-400 max-w-xl">
            Trained with voxel-level ground-truth annotations across Necrotic Core (1), Peritumoral Edema (2),
            and Enhancing Tumor (4). Patient-level validation strictly isolates subjects.
          </p>
        </div>

        <button
          onClick={onNavigateToEvaluation}
          className="px-4 py-2 rounded-xl bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-750 text-slate-800 dark:text-slate-200 text-xs font-semibold border border-slate-200 dark:border-slate-700 flex items-center gap-1.5 self-start sm:self-auto shrink-0 transition-all"
        >
          <span>Explore Benchmark Curves</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Recent / Sample Exploration Sessions */}
      <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-slate-900 dark:text-white">
            Quick Research Verification Scans
          </h3>
          <span className="text-xs text-slate-500 dark:text-slate-400">Pre-computed Phantoms</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div
            onClick={onNavigateToWorkspace}
            className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 hover:border-blue-500 bg-slate-50/50 dark:bg-slate-800/40 cursor-pointer transition-all group"
          >
            <div className="flex items-start justify-between">
              <div>
                <span className="text-[10px] uppercase font-mono font-semibold px-2 py-0.5 rounded bg-blue-100 dark:bg-blue-950 text-blue-700 dark:text-blue-300">
                  Multimodal Phantom
                </span>
                <h4 className="text-sm font-bold text-slate-900 dark:text-white group-hover:text-blue-600 transition-colors mt-2">
                  BraTS Glioblastoma Phantom FLAIR (128³)
                </h4>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                  128 × 128 × 128 • 1.0mm isotropic • Multi-compartment necrosis, edema, and enhancing rim.
                </p>
              </div>
              <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-blue-600 group-hover:translate-x-1 transition-all" />
            </div>
          </div>

          <div
            onClick={onNavigateToWorkspace}
            className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 hover:border-indigo-500 bg-slate-50/50 dark:bg-slate-800/40 cursor-pointer transition-all group"
          >
            <div className="flex items-start justify-between">
              <div>
                <span className="text-[10px] uppercase font-mono font-semibold px-2 py-0.5 rounded bg-indigo-100 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300">
                  Contrast Phantom
                </span>
                <h4 className="text-sm font-bold text-slate-900 dark:text-white group-hover:text-indigo-600 transition-colors mt-2">
                  BraTS Contrast-Enhanced T1ce Phantom (128³)
                </h4>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                  128 × 128 × 128 • 1.0mm isotropic • Simulates high gadolinium uptake in vascularized rim.
                </p>
              </div>
              <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-indigo-600 group-hover:translate-x-1 transition-all" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
