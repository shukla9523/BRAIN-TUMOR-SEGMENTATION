import React, { useState, useRef, useEffect } from 'react';
import { UploadCloud, CheckCircle2, AlertCircle, RefreshCw, Sparkles, Layers, Box } from 'lucide-react';
import { UploadResponse, SampleScanItem } from '../../types/mri';
import { api } from '../../services/api';

interface Props {
  onUploadSuccess: (upload: UploadResponse) => void;
  activeUpload: UploadResponse | null;
  onClearUpload: () => void;
  selectedModality: string;
  onSelectModality: (mod: string) => void;
}

export const MriDropzone: React.FC<Props> = ({
  onUploadSuccess,
  activeUpload,
  onClearUpload,
  selectedModality,
  onSelectModality,
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [samples, setSamples] = useState<SampleScanItem[]>([]);
  const [loadingSample, setLoadingSample] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    // Load available sample scans
    api.getSampleScans()
      .then((res) => setSamples(res.samples))
      .catch(() => {});
  }, []);

  const handleFile = async (file: File) => {
    setErrorMessage(null);
    const validExtensions = ['.nii', '.nii.gz', '.dcm', '.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tif', '.tiff'];
    const lowerName = file.name.toLowerCase();
    const isValid = validExtensions.some((ext) => lowerName.endsWith(ext));

    if (!isValid) {
      setErrorMessage("Please upload a valid MRI scan (.nii, .nii.gz, .dcm) or MRI photo (.jpg, .jpeg, .png, .webp, .bmp).");
      return;
    }

    setUploading(true);
    try {
      const uploadRes = await api.uploadMri(file);
      onUploadSuccess(uploadRes);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to upload MRI volume.');
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleLoadSample = async (sampleId: string) => {
    setLoadingSample(true);
    setErrorMessage(null);
    try {
      const uploadRes = await api.loadSampleScan(sampleId);
      onUploadSuccess(uploadRes);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to load research sample scan.');
    } finally {
      setLoadingSample(false);
    }
  };

  const modalities = ['FLAIR', 'T1', 'T1ce', 'T2'];

  return (
    <div className="space-y-4">
      {/* Upload Drop Zone if no active upload */}
      {!activeUpload ? (
        <div
          onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all ${
            isDragging
              ? 'border-blue-500 bg-blue-50/70 dark:bg-blue-950/40 scale-[1.01]'
              : 'border-slate-300 dark:border-slate-700 hover:border-blue-400 bg-white dark:bg-slate-900/60'
          }`}
        >
          <input
            type="file"
            ref={fileInputRef}
            onChange={(e) => e.target.files && handleFile(e.target.files[0])}
            accept=".nii,.nii.gz,.gz,.dcm,.png,.jpg,.jpeg,.webp,.bmp,.tif,.tiff,image/*"
            className="hidden"
          />

          <div className="flex flex-col items-center justify-center space-y-3">
            <div className="w-14 h-14 rounded-full bg-blue-50 dark:bg-blue-950 flex items-center justify-center text-blue-600 dark:text-blue-400">
              {uploading ? (
                <RefreshCw className="w-7 h-7 animate-spin" />
              ) : (
                <UploadCloud className="w-7 h-7" />
              )}
            </div>

            <div>
              <p className="text-sm font-semibold text-slate-800 dark:text-slate-200">
                {uploading ? 'Validating and Processing MRI Volume / Photo...' : 'Drop MRI scan or brain photo here, or click to browse'}
              </p>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                Supports 3D NIfTI (.nii, .nii.gz), DICOM (.dcm) & MRI Photos (.jpg, .png, .jpeg, .webp) (Max 350 MB)
              </p>
            </div>

            <div className="flex items-center gap-2 pt-2">
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-50 dark:bg-blue-950 text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-800">
                MRI Photos (JPG/PNG)
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700">
                3D NIfTI / DICOM
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700">
                BraTS Protocol
              </span>
            </div>
          </div>
        </div>
      ) : (
        /* Active Upload Metadata Card */
        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 shadow-sm space-y-4">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-emerald-50 dark:bg-emerald-950 flex items-center justify-center text-emerald-600 dark:text-emerald-400">
                <CheckCircle2 className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-slate-900 dark:text-white truncate max-w-xs">
                  {activeUpload.filename}
                </h4>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  {(activeUpload.file_size_bytes / (1024 * 1024)).toFixed(2)} MB • {activeUpload.orientation} Coordinate Frame
                </p>
              </div>
            </div>

            <button
              onClick={onClearUpload}
              className="text-xs text-red-600 hover:text-red-700 dark:text-red-400 hover:underline flex items-center gap-1"
            >
              Change Scan
            </button>
          </div>

          {/* Spatial Grid Metrics */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 pt-2 border-t border-slate-100 dark:border-slate-800">
            <div className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/60">
              <span className="text-[10px] uppercase font-semibold text-slate-400 block">Dimensions</span>
              <span className="text-xs font-mono font-bold text-slate-800 dark:text-slate-200">
                {activeUpload.dimensions.join(' × ')}
              </span>
            </div>

            <div className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/60">
              <span className="text-[10px] uppercase font-semibold text-slate-400 block">Voxel Spacing</span>
              <span className="text-xs font-mono font-bold text-slate-800 dark:text-slate-200">
                {activeUpload.voxel_spacing.map(v => v.toFixed(2)).join(' × ')} mm
              </span>
            </div>

            <div className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/60">
              <span className="text-[10px] uppercase font-semibold text-slate-400 block">Axial Slices</span>
              <span className="text-xs font-mono font-bold text-slate-800 dark:text-slate-200">
                {activeUpload.total_slices_axial} slices
              </span>
            </div>

            <div className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/60">
              <span className="text-[10px] uppercase font-semibold text-slate-400 block">Modality</span>
              <span className="text-xs font-mono font-bold text-blue-600 dark:text-blue-400">
                {activeUpload.modalities_detected[0] || 'FLAIR'}
              </span>
            </div>
          </div>

          {/* Modality Selector */}
          <div>
            <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block mb-1.5">
              Input MRI Sequence / Modality
            </label>
            <div className="grid grid-cols-4 gap-2">
              {modalities.map((mod) => (
                <button
                  key={mod}
                  type="button"
                  onClick={() => onSelectModality(mod)}
                  className={`py-1.5 text-xs font-medium rounded-lg border transition-all ${
                    selectedModality === mod
                      ? 'bg-blue-600 text-white border-blue-600 shadow-sm shadow-blue-500/20'
                      : 'bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-750'
                  }`}
                >
                  {mod}
                </button>
              ))}
            </div>
          </div>

          {/* Warnings callout */}
          {activeUpload.warnings && activeUpload.warnings.length > 0 && (
            <div className="p-2.5 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900/40 text-amber-800 dark:text-amber-300 text-xs flex items-start gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold">Quality Notice:</span>
                <ul className="list-disc list-inside mt-0.5 space-y-0.5">
                  {activeUpload.warnings.map((w, i) => (
                    <li key={i}>{w}</li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Error display */}
      {errorMessage && (
        <div className="p-3 rounded-xl bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900/40 text-red-700 dark:text-red-300 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* One-Click Research Sample Scans Loader */}
      {!activeUpload && (
        <div className="bg-slate-50 dark:bg-slate-900/50 rounded-2xl border border-slate-200 dark:border-slate-800 p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />
              Don't have a NIfTI scan handy? Test with research samples:
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {samples.length > 0 ? (
              samples.map((s, idx) => (
                <button
                  key={s.sample_id}
                  onClick={() => handleLoadSample(s.sample_id)}
                  disabled={loadingSample}
                  className="p-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-left hover:border-blue-500 hover:shadow-sm transition-all group flex items-start gap-2.5"
                >
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${
                    idx % 2 === 0
                      ? 'bg-blue-100 dark:bg-blue-950 text-blue-600 dark:text-blue-400'
                      : 'bg-indigo-100 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-400'
                  }`}>
                    {idx % 2 === 0 ? <Box className="w-4 h-4" /> : <Layers className="w-4 h-4" />}
                  </div>
                  <div className="min-w-0">
                    <p className="text-xs font-bold text-slate-800 dark:text-slate-200 group-hover:text-blue-600 truncate">
                      {s.filename}
                    </p>
                    <p className="text-[11px] text-slate-500 dark:text-slate-400 line-clamp-2">
                      {s.description}
                    </p>
                  </div>
                </button>
              ))
            ) : (
              <>
                <button
                  onClick={() => handleLoadSample('sample_phantom_brats_flair')}
                  disabled={loadingSample}
                  className="p-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-left hover:border-blue-500 hover:shadow-sm transition-all group flex items-start gap-2.5"
                >
                  <div className="w-8 h-8 rounded-lg bg-blue-100 dark:bg-blue-950 text-blue-600 dark:text-blue-400 flex items-center justify-center shrink-0">
                    <Box className="w-4 h-4" />
                  </div>
                  <div>
                    <p className="text-xs font-bold text-slate-800 dark:text-slate-200 group-hover:text-blue-600">
                      Synthetic BraTS FLAIR Phantom
                    </p>
                    <p className="text-[11px] text-slate-500 dark:text-slate-400">
                      128×128×128 • Glioblastoma Multi-Compartment Phantom
                    </p>
                  </div>
                </button>

                <button
                  onClick={() => handleLoadSample('sample_phantom_brats_t1ce')}
                  disabled={loadingSample}
                  className="p-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-left hover:border-blue-500 hover:shadow-sm transition-all group flex items-start gap-2.5"
                >
                  <div className="w-8 h-8 rounded-lg bg-indigo-100 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-400 flex items-center justify-center shrink-0">
                    <Layers className="w-4 h-4" />
                  </div>
                  <div>
                    <p className="text-xs font-bold text-slate-800 dark:text-slate-200 group-hover:text-indigo-600">
                      Synthetic BraTS T1ce Phantom
                    </p>
                    <p className="text-[11px] text-slate-500 dark:text-slate-400">
                      128×128×128 • Contrast-Enhancing Rim Simulation
                    </p>
                  </div>
                </button>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
