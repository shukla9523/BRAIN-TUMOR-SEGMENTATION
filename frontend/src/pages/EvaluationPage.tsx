import React, { useEffect, useState } from 'react';
import { BarChart3, RefreshCw } from 'lucide-react';
import { EvaluationMetricsData } from '../types/mri';
import { MetricsCharts } from '../components/charts/MetricsCharts';
import { api } from '../services/api';

export const EvaluationPage: React.FC = () => {
  const [metrics, setMetrics] = useState<EvaluationMetricsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const handleRefresh = () => {
    setLoading(true);
    setError(null);
    api.getMetrics()
      .then((data) => setMetrics(data))
      .catch((err) => setError(err.message || 'Failed to load evaluation metrics'))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    let active = true;
    api.getMetrics()
      .then((data) => {
        if (active) setMetrics(data);
      })
      .catch((err) => {
        if (active) setError(err.message || 'Failed to load evaluation metrics');
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  return (
    <div className="space-y-8 py-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <BarChart3 className="w-6 h-6 text-blue-600 dark:text-blue-400" />
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white">
              Model Benchmark & Evaluation
            </h1>
          </div>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
            Empirical validation results, per-class Dice scores, and loss convergence curves
          </p>
        </div>

        <button
          onClick={handleRefresh}
          disabled={loading}
          className="px-3.5 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 text-xs font-semibold flex items-center gap-2 self-start sm:self-auto transition-all"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Metrics</span>
        </button>
      </div>

      {/* Dataset & Architecture Spec Bar */}
      <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 shadow-sm grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
        <div>
          <span className="text-[10px] uppercase font-bold text-slate-400 block mb-0.5">Benchmark Dataset</span>
          <span className="font-semibold text-slate-800 dark:text-slate-200">BraTS 2020 / 2021 Cohort</span>
        </div>
        <div>
          <span className="text-[10px] uppercase font-bold text-slate-400 block mb-0.5">Input Channels</span>
          <span className="font-semibold text-slate-800 dark:text-slate-200">4 Modalities (T1, T1ce, T2, FLAIR)</span>
        </div>
        <div>
          <span className="text-[10px] uppercase font-bold text-slate-400 block mb-0.5">Loss Formulation</span>
          <span className="font-semibold text-slate-800 dark:text-slate-200">0.5 Dice + 0.5 Cross-Entropy</span>
        </div>
        <div>
          <span className="text-[10px] uppercase font-bold text-slate-400 block mb-0.5">Leakage Prevention</span>
          <span className="font-semibold text-emerald-600 dark:text-emerald-400">Patient-Level Segregation</span>
        </div>
      </div>

      {/* Main Charts & Evaluation Component */}
      {metrics ? (
        <MetricsCharts data={metrics} />
      ) : loading ? (
        <div className="p-16 text-center text-slate-400 space-y-2">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto text-blue-500" />
          <p className="text-xs">Loading recorded validation metrics from disk...</p>
        </div>
      ) : (
        <div className="p-8 rounded-2xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 text-center text-amber-800 text-xs">
          {error || 'No evaluation metrics recorded yet.'}
        </div>
      )}
    </div>
  );
};
