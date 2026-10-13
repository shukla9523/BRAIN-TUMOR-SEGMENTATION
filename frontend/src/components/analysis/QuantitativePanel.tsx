import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell
} from 'recharts';
import {
  Activity,
  Download,
  FileText,
  Info
} from 'lucide-react';
import { QuantitativeReport } from '../../types/mri';
import { api } from '../../services/api';

interface Props {
  report: QuantitativeReport;
  resultId: string;
}

export const QuantitativePanel: React.FC<Props> = ({ report, resultId }) => {
  const chartData = report.regions.map((reg) => ({
    name: reg.region_id.replace('_', '/'),
    fullName: reg.region_name,
    volume: reg.volume_cm3,
    color: reg.color_hex,
    voxels: reg.voxel_count,
  }));

  return (
    <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 shadow-sm space-y-6">
      {/* Header & Quick Stat */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            <h3 className="text-base font-bold text-slate-900 dark:text-white">
              Quantitative Volumetric Estimates
            </h3>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Model-derived volumetric calculations based on physical voxel dimensions
          </p>
        </div>

        {/* Total Tumor Stat Badge */}
        <div className="bg-blue-50 dark:bg-blue-950/60 border border-blue-200 dark:border-blue-800 rounded-xl px-4 py-2 flex items-center gap-3">
          <div>
            <span className="text-[10px] uppercase font-bold text-blue-600 dark:text-blue-400 block">
              Total Tumor Volume (WT)
            </span>
            <span className="text-xl font-black text-slate-900 dark:text-white font-mono">
              {report.total_tumor_volume_cm3.toFixed(3)}{' '}
              <span className="text-xs font-normal text-slate-500 dark:text-slate-400">cm³</span>
            </span>
          </div>
        </div>
      </div>

      {/* Recharts Bar Chart of Regional Volumes */}
      <div>
        <h4 className="text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-2">
          Subregion Volume Distribution (cm³)
        </h4>
        <div className="h-48 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} layout="vertical" margin={{ top: 5, right: 30, left: 40, bottom: 5 }}>
              <XAxis type="number" tick={{ fontSize: 11, fill: '#94a3b8' }} unit=" cm³" />
              <YAxis dataKey="name" type="category" tick={{ fontSize: 11, fill: '#94a3b8' }} />
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const data = payload[0].payload;
                    return (
                      <div className="bg-slate-900 text-white p-2.5 rounded-lg text-xs shadow-xl border border-slate-700">
                        <p className="font-bold">{data.fullName}</p>
                        <p className="font-mono text-blue-400">{data.volume.toFixed(3)} cm³</p>
                        <p className="text-slate-400">{data.voxels.toLocaleString()} voxels</p>
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Bar dataKey="volume" radius={[0, 4, 4, 0]}>
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Detailed Measurements Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-400 uppercase tracking-wider font-semibold">
              <th className="pb-2">Subregion</th>
              <th className="pb-2 text-right">Volume (cm³)</th>
              <th className="pb-2 text-right">Voxel Count</th>
              <th className="pb-2 text-center">Axial Extent</th>
              <th className="pb-2 text-center">Lesions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 font-mono">
            {report.regions.map((reg) => (
              <tr key={reg.region_id} className="hover:bg-slate-50 dark:hover:bg-slate-800/30 transition-colors">
                <td className="py-2.5 font-sans font-medium text-slate-900 dark:text-white flex items-center gap-2">
                  <span
                    className="w-2.5 h-2.5 rounded-full shrink-0"
                    style={{ backgroundColor: reg.color_hex }}
                  />
                  <span>{reg.region_name}</span>
                </td>
                <td className="py-2.5 text-right font-bold text-slate-900 dark:text-white">
                  {reg.volume_cm3.toFixed(3)}
                </td>
                <td className="py-2.5 text-right text-slate-500 dark:text-slate-400">
                  {reg.voxel_count.toLocaleString()}
                </td>
                <td className="py-2.5 text-center text-slate-500 dark:text-slate-400">
                  {reg.slice_extent_axial[0] === 0 && reg.slice_extent_axial[1] === 0
                    ? 'None'
                    : `${reg.slice_extent_axial[0]}–${reg.slice_extent_axial[1]}`}
                </td>
                <td className="py-2.5 text-center text-slate-500 dark:text-slate-400">
                  {reg.connected_components}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Export / Download Buttons */}
      <div className="pt-4 border-t border-slate-100 dark:border-slate-800 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <a
            href={api.getMaskDownloadUrl(resultId)}
            download
            className="px-3.5 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 text-xs font-semibold flex items-center gap-2 transition-all"
          >
            <Download className="w-3.5 h-3.5" /> Download NIfTI Mask (.nii.gz)
          </a>

          <a
            href={api.getReportDownloadUrl(resultId)}
            download
            className="px-3.5 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold flex items-center gap-2 shadow-sm shadow-blue-500/20 transition-all"
          >
            <FileText className="w-3.5 h-3.5" /> Download PDF Research Report
          </a>
        </div>

        <span className="text-[11px] text-slate-400">
          Inference Time: {report.processing_time_seconds.toFixed(2)}s
        </span>
      </div>

      {/* Mandatory Clinical Disclaimer */}
      <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400 text-[11px] flex items-start gap-2">
        <Info className="w-4 h-4 shrink-0 text-slate-400 mt-0.5" />
        <p>
          <span className="font-semibold text-slate-700 dark:text-slate-300">Notice:</span> Measurements are
          derived from deep neural network voxel predictions ($voxel\_count \times voxel\_spacing / 1000$).
          They represent mathematical approximations and are not definitive histological measurements.
        </p>
      </div>
    </div>
  );
};
