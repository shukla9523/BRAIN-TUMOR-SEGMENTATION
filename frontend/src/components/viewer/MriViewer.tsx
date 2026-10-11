import React, { useState, useEffect, useRef } from 'react';
import {
  Sliders,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Maximize2,
  ChevronLeft,
  ChevronRight,
  Eye,
  EyeOff,
  Split,
  Layers,
  Sun,
  Activity,
  Check
} from 'lucide-react';
import { SliceVisualizationResponse } from '../../types/mri';
import { api } from '../../services/api';

interface Props {
  activeId: string; // upload_id or result_id
  isResult: boolean;
  totalSlices: {
    axial: number;
    coronal: number;
    sagittal: number;
  };
  dimensions: number[];
  voxelSpacing: number[];
}

export const MriViewer: React.FC<Props> = ({
  activeId,
  isResult,
  totalSlices,
  dimensions,
  voxelSpacing,
}) => {
  const [plane, setPlane] = useState<'axial' | 'coronal' | 'sagittal'>('axial');
  const [sliceIndex, setSliceIndex] = useState<number>(Math.floor((totalSlices.axial || 128) / 2));
  const [opacity, setOpacity] = useState<number>(0.65);
  const [brightness, setBrightness] = useState<number>(100);
  const [contrast, setContrast] = useState<number>(100);
  const [zoom, setZoom] = useState<number>(1.0);
  const [pan, setPan] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [isPanning, setIsPanning] = useState(false);
  const [startPan, setStartPan] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [viewMode, setViewMode] = useState<'overlay' | 'side-by-side'>('overlay');
  const [sliceData, setSliceData] = useState<SliceVisualizationResponse | null>(null);
  const [loadingSlice, setLoadingSlice] = useState(false);
  const [enabledRegions, setEnabledRegions] = useState<Record<string, boolean>>({
    WT: true,
    TC: true,
    ET: true,
    ED: true,
    NCR_NET: true,
  });

  const viewerContainerRef = useRef<HTMLDivElement>(null);

  // Maximum slice count for active plane
  const maxSlice = (totalSlices[plane] || 128) - 1;

  // Reset slice index to midpoint when switching orthogonal plane
  useEffect(() => {
    const mid = Math.floor((totalSlices[plane] || 128) / 2);
    setSliceIndex(mid);
  }, [plane, totalSlices]);

  // Fetch slice image whenever sliceIndex, plane, opacity, or activeId changes
  useEffect(() => {
    if (!activeId) return;

    let isSubscribed = true;
    setLoadingSlice(true);

    const fetchSlice = async () => {
      try {
        let res: SliceVisualizationResponse;
        if (isResult) {
          res = await api.getResultSlice(activeId, sliceIndex, plane, opacity);
        } else {
          res = await api.getUploadSlice(activeId, sliceIndex, plane);
        }
        if (isSubscribed) {
          setSliceData(res);
        }
      } catch (err) {
        console.error('Failed to load slice:', err);
      } finally {
        if (isSubscribed) {
          setLoadingSlice(false);
        }
      }
    };

    fetchSlice();
    return () => { isSubscribed = false; };
  }, [activeId, isResult, sliceIndex, plane, opacity]);

  // Keyboard navigation: Arrow Left / Arrow Right
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;
      if (e.key === 'ArrowLeft' || e.key === 'ArrowDown') {
        e.preventDefault();
        setSliceIndex((prev) => Math.max(0, prev - 1));
      } else if (e.key === 'ArrowRight' || e.key === 'ArrowUp') {
        e.preventDefault();
        setSliceIndex((prev) => Math.min(maxSlice, prev + 1));
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [maxSlice]);

  // Pan handlers
  const handleMouseDown = (e: React.MouseEvent) => {
    setIsPanning(true);
    setStartPan({ x: e.clientX - pan.x, y: e.clientY - pan.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isPanning) return;
    setPan({ x: e.clientX - startPan.x, y: e.clientY - startPan.y });
  };

  const handleMouseUp = () => setIsPanning(false);

  const resetViewport = () => {
    setZoom(1.0);
    setPan({ x: 0, y: 0 });
    setBrightness(100);
    setContrast(100);
  };

  const toggleRegion = (regId: string) => {
    setEnabledRegions(prev => ({ ...prev, [regId]: !prev[regId] }));
  };

  const regionsLegend = [
    { id: 'WT', name: 'Whole Tumor (WT)', color: '#2563EB', desc: 'Edema + Core + Enhancing' },
    { id: 'TC', name: 'Tumor Core (TC)', color: '#DC2626', desc: 'Necrotic + Enhancing' },
    { id: 'ET', name: 'Enhancing Tumor (ET)', color: '#F59E0B', desc: 'Active Rim (Label 4)' },
    { id: 'ED', name: 'Edema (ED)', color: '#10B981', desc: 'Infiltration (Label 2)' },
    { id: 'NCR_NET', name: 'Necrosis (NCR)', color: '#8B5CF6', desc: 'Non-enhancing (Label 1)' },
  ];

  return (
    <div className="bg-slate-900 rounded-2xl border border-slate-800 text-white overflow-hidden shadow-xl flex flex-col">
      {/* Top Toolbar */}
      <div className="bg-slate-950/80 px-4 py-3 border-b border-slate-800 flex flex-wrap items-center justify-between gap-3 text-xs">
        {/* Orthogonal Plane Selector */}
        <div className="flex items-center gap-1.5 bg-slate-900 p-1 rounded-xl border border-slate-800">
          {(['axial', 'coronal', 'sagittal'] as const).map((p) => (
            <button
              key={p}
              onClick={() => setPlane(p)}
              className={`px-3 py-1.5 rounded-lg font-semibold uppercase tracking-wider text-[11px] transition-all ${
                plane === p
                  ? 'bg-blue-600 text-white shadow-sm shadow-blue-500/20'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800'
              }`}
            >
              {p}
            </button>
          ))}
        </div>

        {/* View Mode (Overlay vs Side-by-Side) */}
        {isResult && (
          <div className="flex items-center gap-1 bg-slate-900 p-1 rounded-xl border border-slate-800">
            <button
              onClick={() => setViewMode('overlay')}
              className={`px-2.5 py-1 rounded-lg flex items-center gap-1 transition-all ${
                viewMode === 'overlay' ? 'bg-slate-800 text-blue-400 font-semibold' : 'text-slate-400 hover:text-white'
              }`}
              title="Show Overlay"
            >
              <Layers className="w-3.5 h-3.5" /> Overlay
            </button>
            <button
              onClick={() => setViewMode('side-by-side')}
              className={`px-2.5 py-1 rounded-lg flex items-center gap-1 transition-all ${
                viewMode === 'side-by-side' ? 'bg-slate-800 text-blue-400 font-semibold' : 'text-slate-400 hover:text-white'
              }`}
              title="Show Side-by-Side Comparison"
            >
              <Split className="w-3.5 h-3.5" /> Side-by-Side
            </button>
          </div>
        )}

        {/* Zoom & Pan Controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setZoom((z) => Math.min(3.0, z + 0.2))}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors"
            title="Zoom In"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          <span className="text-[11px] font-mono text-slate-400 w-10 text-center">
            {Math.round(zoom * 100)}%
          </span>
          <button
            onClick={() => setZoom((z) => Math.max(0.6, z - 0.2))}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors"
            title="Zoom Out"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <button
            onClick={resetViewport}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors"
            title="Reset View"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Main Medical Canvas Viewport */}
      <div
        ref={viewerContainerRef}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        className="relative flex-1 min-h-[380px] sm:min-h-[460px] bg-black flex items-center justify-center overflow-hidden cursor-grab active:cursor-grabbing select-none"
      >
        {/* Loading overlay */}
        {loadingSlice && (
          <div className="absolute top-4 right-4 z-20 bg-slate-900/80 backdrop-blur px-2.5 py-1 rounded-full text-[11px] text-blue-400 flex items-center gap-1.5 border border-slate-700">
            <span className="w-2 h-2 rounded-full bg-blue-500 animate-ping" /> Loading slice...
          </div>
        )}

        {/* HUD Info Badges */}
        <div className="absolute top-4 left-4 z-10 space-y-1 pointer-events-none">
          <div className="bg-slate-950/70 backdrop-blur px-2.5 py-1 rounded-lg text-[11px] font-mono text-slate-300 border border-slate-800">
            Plane: <span className="text-blue-400 uppercase font-bold">{plane}</span> • Slice{' '}
            <span className="text-white font-bold">{sliceIndex + 1}</span> / {maxSlice + 1}
          </div>
          <div className="bg-slate-950/70 backdrop-blur px-2.5 py-1 rounded-lg text-[10px] font-mono text-slate-400 border border-slate-800">
            Dim: {dimensions.join('×')} • Voxel: {voxelSpacing.map((v) => v.toFixed(1)).join('×')}mm
          </div>
          {sliceData?.has_tumor && (
            <div className="bg-red-950/80 backdrop-blur px-2.5 py-1 rounded-lg text-[10px] font-bold text-red-400 border border-red-800 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
              Tumor Mask Detected on this Slice
            </div>
          )}
        </div>

        {/* Render Viewport */}
        <div
          style={{
            transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
            filter: `brightness(${brightness}%) contrast(${contrast}%)`,
            transition: isPanning ? 'none' : 'transform 0.1s ease-out',
          }}
          className="flex items-center justify-center gap-4 transition-all"
        >
          {sliceData ? (
            viewMode === 'side-by-side' && isResult ? (
              /* Side-by-side mode */
              <div className="flex items-center gap-4">
                <div className="text-center">
                  <div className="text-[10px] font-mono text-slate-400 mb-1">ORIGINAL MRI SCAN</div>
                  <img
                    src={sliceData.image_base64}
                    alt="Original MRI Slice"
                    className="max-h-[360px] object-contain rounded-lg border border-slate-800 scan-viewport"
                  />
                </div>
                <div className="text-center">
                  <div className="text-[10px] font-mono text-blue-400 mb-1">SEGMENTATION OVERLAY</div>
                  <img
                    src={sliceData.overlay_base64}
                    alt="Segmented Slice Overlay"
                    className="max-h-[360px] object-contain rounded-lg border border-slate-800 scan-viewport"
                  />
                </div>
              </div>
            ) : (
              /* Overlay mode */
              <div className="relative">
                <img
                  src={isResult ? sliceData.overlay_base64 : sliceData.image_base64}
                  alt="MRI View"
                  className="max-h-[380px] sm:max-h-[440px] object-contain rounded-lg border border-slate-800 scan-viewport"
                />
              </div>
            )
          ) : (
            <div className="text-slate-500 text-xs flex flex-col items-center gap-2">
              <Activity className="w-8 h-8 animate-pulse text-blue-500" />
              <span>Initializing Slice Viewport...</span>
            </div>
          )}
        </div>
      </div>

      {/* Slice Navigation Slider & Step Controls */}
      <div className="bg-slate-950 p-4 border-t border-slate-800 space-y-3">
        <div className="flex items-center justify-between gap-3">
          <button
            onClick={() => setSliceIndex((s) => Math.max(0, s - 1))}
            disabled={sliceIndex <= 0}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-30 text-white"
            title="Previous Slice (←)"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>

          <div className="flex-1 flex items-center gap-3">
            <span className="text-[11px] font-mono text-slate-400">1</span>
            <input
              type="range"
              min={0}
              max={maxSlice}
              value={sliceIndex}
              onChange={(e) => setSliceIndex(Number(e.target.value))}
              className="flex-1 accent-blue-500 h-1.5 bg-slate-800 rounded-lg cursor-pointer"
            />
            <span className="text-[11px] font-mono text-slate-400">{maxSlice + 1}</span>
          </div>

          <button
            onClick={() => setSliceIndex((s) => Math.min(maxSlice, s + 1))}
            disabled={sliceIndex >= maxSlice}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-30 text-white"
            title="Next Slice (→)"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>

        {/* Secondary Windowing / Contrast & Opacity Controls */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2 border-t border-slate-900 text-xs text-slate-400">
          {/* Opacity */}
          {isResult && (
            <div className="flex items-center gap-2">
              <span className="text-[11px] w-20">Mask Opacity:</span>
              <input
                type="range"
                min={0}
                max={100}
                value={Math.round(opacity * 100)}
                onChange={(e) => setOpacity(Number(e.target.value) / 100)}
                className="flex-1 accent-blue-500 h-1 bg-slate-800 rounded cursor-pointer"
              />
              <span className="text-[11px] font-mono w-8 text-right">{Math.round(opacity * 100)}%</span>
            </div>
          )}

          {/* Brightness */}
          <div className="flex items-center gap-2">
            <span className="text-[11px] w-16">Brightness:</span>
            <input
              type="range"
              min={50}
              max={150}
              value={brightness}
              onChange={(e) => setBrightness(Number(e.target.value))}
              className="flex-1 accent-slate-400 h-1 bg-slate-800 rounded cursor-pointer"
            />
            <span className="text-[11px] font-mono w-8 text-right">{brightness}%</span>
          </div>

          {/* Contrast */}
          <div className="flex items-center gap-2">
            <span className="text-[11px] w-16">Contrast:</span>
            <input
              type="range"
              min={50}
              max={150}
              value={contrast}
              onChange={(e) => setContrast(Number(e.target.value))}
              className="flex-1 accent-slate-400 h-1 bg-slate-800 rounded cursor-pointer"
            />
            <span className="text-[11px] font-mono w-8 text-right">{contrast}%</span>
          </div>
        </div>

        {/* BraTS Subregion Legend & Toggle Badges */}
        {isResult && (
          <div className="pt-2 border-t border-slate-900">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-[10px] uppercase font-bold text-slate-500 mr-1">
                BraTS Subregions:
              </span>
              {regionsLegend.map((reg) => (
                <button
                  key={reg.id}
                  onClick={() => toggleRegion(reg.id)}
                  style={{ borderColor: reg.color }}
                  className={`px-2 py-0.5 rounded-md text-[11px] font-medium border flex items-center gap-1.5 transition-all ${
                    enabledRegions[reg.id]
                      ? 'bg-slate-800 text-white'
                      : 'bg-transparent text-slate-500 opacity-60'
                  }`}
                >
                  <span
                    className="w-2.5 h-2.5 rounded-full"
                    style={{ backgroundColor: reg.color }}
                  />
                  <span>{reg.name}</span>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
