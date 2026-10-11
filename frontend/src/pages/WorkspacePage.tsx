import React, { useState, useEffect } from 'react';
import {
  Brain,
  Activity,
  Play,
  CheckCircle2,
  AlertCircle,
  FileText,
  RotateCcw,
  Sparkles,
  Layers,
  ArrowRight
} from 'lucide-react';
import { UploadResponse, ResultInfo, JobStatusResponse } from '../types/mri';
import { MriDropzone } from '../components/upload/MriDropzone';
import { MriViewer } from '../components/viewer/MriViewer';
import { QuantitativePanel } from '../components/analysis/QuantitativePanel';
import { api } from '../services/api';

interface Props {
  modelAvailable: boolean;
  onNavigateToResults?: (resultId: string) => void;
}

export const WorkspacePage: React.FC<Props> = ({ modelAvailable }) => {
  const [activeUpload, setActiveUpload] = useState<UploadResponse | null>(null);
  const [selectedModality, setSelectedModality] = useState<string>('FLAIR');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [jobStatus, setJobStatus] = useState<JobStatusResponse | null>(null);
  const [result, setResult] = useState<ResultInfo | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Poll for background job progress
  useEffect(() => {
    if (!jobStatus || jobStatus.status === 'completed' || jobStatus.status === 'failed') return;

    const interval = setInterval(async () => {
      try {
        const update = await api.getJobStatus(jobStatus.job_id);
        setJobStatus(update);

        if (update.status === 'completed' && update.result_id) {
          const res = await api.getResult(update.result_id);
          setResult(res);
          setIsAnalyzing(false);
        } else if (update.status === 'failed') {
          setErrorMessage(update.error || 'Segmentation processing encountered an error.');
          setIsAnalyzing(false);
        }
      } catch (err: any) {
        setErrorMessage(err.message || 'Failed to poll job status.');
        setIsAnalyzing(false);
      }
    }, 800);

    return () => clearInterval(interval);
  }, [jobStatus]);

  const handleUploadSuccess = (upload: UploadResponse) => {
    setActiveUpload(upload);
    setResult(null);
    setJobStatus(null);
    setErrorMessage(null);
    if (upload.modalities_detected && upload.modalities_detected.length > 0) {
      const cleanMod = upload.modalities_detected[0].split(' ')[0];
      setSelectedModality(cleanMod);
    }
  };

  const handleClearUpload = () => {
    setActiveUpload(null);
    setResult(null);
    setJobStatus(null);
    setErrorMessage(null);
  };

  const handleStartAnalysis = async () => {
    if (!activeUpload) return;
    setErrorMessage(null);
    setIsAnalyzing(true);
    setResult(null);

    try {
      const segRes = await api.startSegmentation(activeUpload.upload_id, selectedModality);
      setJobStatus({
        job_id: segRes.job_id,
        status: 'pending',
        progress: 5,
        message: 'Submitting MRI to 3D U-Net pipeline...'
      });
    } catch (err: any) {
      setErrorMessage(err.message || 'Segmentation failed to initialize.');
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="space-y-8 py-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <Brain className="w-6 h-6 text-blue-600 dark:text-blue-400" />
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white">
              MRI Volumetric Analysis Workspace
            </h1>
          </div>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
            Three-plane volumetric viewer, neural segmentation, and quantitative measurements
          </p>
        </div>

        {/* Action Trigger Button */}
        {activeUpload && !result && (
          <button
            onClick={handleStartAnalysis}
            disabled={isAnalyzing}
            className={`px-6 py-3 rounded-xl font-bold text-xs uppercase tracking-wider flex items-center gap-2 shadow-lg transition-all ${
              isAnalyzing
                ? 'bg-slate-300 dark:bg-slate-700 text-slate-500 cursor-not-allowed'
                : 'bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white shadow-blue-500/25 scale-[1.02]'
            }`}
          >
            {isAnalyzing ? (
              <>
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                <span>Processing 3D Volume...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-white" />
                <span>Analyze MRI Scan</span>
              </>
            )}
          </button>
        )}
      </div>

      {/* Error Callout */}
      {errorMessage && (
        <div className="p-4 rounded-2xl bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900/50 text-red-800 dark:text-red-300 text-xs flex items-start gap-3">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5 text-red-600" />
          <div className="space-y-1">
            <h4 className="font-bold">Inference Error</h4>
            <p className="leading-relaxed">{errorMessage}</p>
          </div>
        </div>
      )}

      {/* Progress Bar during analysis */}
      {isAnalyzing && jobStatus && (
        <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-3">
          <div className="flex items-center justify-between text-xs">
            <span className="font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-blue-500 animate-ping" />
              {jobStatus.message}
            </span>
            <span className="font-mono font-bold text-blue-600 dark:text-blue-400">
              {jobStatus.progress}%
            </span>
          </div>

          <div className="w-full h-2.5 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
            <div
              style={{ width: `${jobStatus.progress}%` }}
              className="h-full bg-gradient-to-r from-blue-600 to-indigo-500 rounded-full transition-all duration-300"
            />
          </div>

          <p className="text-[11px] text-slate-400">
            Applying 3D U-Net neural inference with geometry restoration...
          </p>
        </div>
      )}

      {/* Main Workspace Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: Upload & Scan Details */}
        <div className="lg:col-span-5 space-y-6">
          <MriDropzone
            onUploadSuccess={handleUploadSuccess}
            activeUpload={activeUpload}
            onClearUpload={handleClearUpload}
            selectedModality={selectedModality}
            onSelectModality={setSelectedModality}
          />
        </div>

        {/* Right Column: 3-Plane Interactive Viewer */}
        <div className="lg:col-span-7 space-y-6">
          {activeUpload ? (
            <MriViewer
              activeId={result ? result.result_id : activeUpload.upload_id}
              isResult={!!result}
              totalSlices={{
                axial: activeUpload.total_slices_axial,
                coronal: activeUpload.total_slices_coronal,
                sagittal: activeUpload.total_slices_sagittal,
              }}
              dimensions={activeUpload.dimensions}
              voxelSpacing={activeUpload.voxel_spacing}
            />
          ) : (
            <div className="bg-slate-900 rounded-2xl border border-slate-800 p-12 text-center text-slate-500 flex flex-col items-center justify-center min-h-[460px] space-y-3">
              <Brain className="w-12 h-12 text-slate-700 animate-pulse" />
              <p className="text-sm font-semibold text-slate-400">
                No MRI volume loaded in workspace
              </p>
              <p className="text-xs text-slate-600 max-w-sm">
                Upload a NIfTI scan or load one of the pre-configured BraTS research phantoms on the left to begin
                exploration.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Quantitative Analysis Results Section */}
      {result && result.quantitative_report && (
        <section className="space-y-4 pt-4 border-t border-slate-200 dark:border-slate-800">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <Activity className="w-5 h-5 text-blue-600 dark:text-blue-400" />
              <span>Quantitative Volumetric Results</span>
            </h2>
          </div>

          <QuantitativePanel
            report={result.quantitative_report}
            resultId={result.result_id}
          />
        </section>
      )}
    </div>
  );
};
