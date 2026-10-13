import React from 'react';
import { Brain, ShieldAlert, BookOpen, ExternalLink, Code2 } from 'lucide-react';

const CURRENT_YEAR = new Date().getFullYear();

export const Footer: React.FC = () => {
  return (
    <footer className="border-t border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80 mt-auto py-8 transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          {/* Col 1 */}
          <div className="md:col-span-2">
            <div className="flex items-center gap-2 mb-3">
              <Brain className="w-5 h-5 text-blue-600 dark:text-blue-400" />
              <span className="font-bold text-slate-900 dark:text-white">NeuroScan AI</span>
              <span className="text-xs px-2 py-0.5 rounded bg-blue-100 dark:bg-blue-950 text-blue-700 dark:text-blue-300">
                Research Edition
              </span>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed max-w-md">
              An open-source deep learning platform for volumetric 3D brain tumor segmentation benchmarking on
              multimodal MRI datasets. Developed using PyTorch, 3D U-Net, and FastAPI.
            </p>
            <div className="mt-3 flex items-center gap-2 text-xs text-amber-700 dark:text-amber-400">
              <ShieldAlert className="w-3.5 h-3.5 shrink-0" />
              <span>Not evaluated or certified for clinical diagnostic decision-making.</span>
            </div>
          </div>

          {/* Col 2 */}
          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-900 dark:text-white mb-3">
              Medical Datasets
            </h4>
            <ul className="space-y-2 text-xs text-slate-600 dark:text-slate-400">
              <li>BraTS 2020 Challenge</li>
              <li>BraTS 2021 Adult Glioma</li>
              <li>T1, T1ce, T2, FLAIR Co-registration</li>
              <li>Label 1 (NCR/NET), 2 (ED), 4 (ET)</li>
            </ul>
          </div>

          {/* Col 3 */}
          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-900 dark:text-white mb-3">
              Technical Resources
            </h4>
            <ul className="space-y-2 text-xs text-slate-600 dark:text-slate-400">
              <li className="flex items-center gap-1.5 hover:text-blue-600 dark:hover:text-blue-400 cursor-pointer">
                <BookOpen className="w-3.5 h-3.5" />
                <span>Colab Training Notebook</span>
              </li>
              <li className="flex items-center gap-1.5 hover:text-blue-600 dark:hover:text-blue-400 cursor-pointer">
                <Code2 className="w-3.5 h-3.5" />
                <span>FastAPI OpenAPI Schema</span>
              </li>
              <li className="flex items-center gap-1.5 hover:text-blue-600 dark:hover:text-blue-400 cursor-pointer">
                <ExternalLink className="w-3.5 h-3.5" />
                <span>MICCAI BraTS Benchmark</span>
              </li>
            </ul>
          </div>
        </div>

        <div className="pt-6 border-t border-slate-200 dark:border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-400">
          <p>© {CURRENT_YEAR} NeuroScan AI Project. Academic & Research Verification.</p>
          <div className="flex items-center gap-4">
            <span>HIPAA/GDPR Data Hygiene Notice: Strip PHI prior to upload</span>
          </div>
        </div>
      </div>
    </footer>
  );
};
