import React from 'react';
import { Brain, Moon, Sun, Cpu } from 'lucide-react';

interface Props {
  currentTab: string;
  onSelectTab: (tab: string) => void;
  modelAvailable: boolean;
  deviceInfo: string;
  isDark: boolean;
  onToggleTheme: () => void;
}

export const Navbar: React.FC<Props> = ({
  currentTab,
  onSelectTab,
  modelAvailable,
  deviceInfo,
  isDark,
  onToggleTheme,
}) => {
  const navItems = [
    { id: 'landing', label: 'Overview' },
    { id: 'dashboard', label: 'Dashboard' },
    { id: 'workspace', label: 'MRI Workspace' },
    { id: 'evaluation', label: 'Model Evaluation' },
    { id: 'methodology', label: 'Methodology & Ethics' },
  ];

  return (
    <header className="sticky top-0 z-40 bg-white/90 dark:bg-slate-900/90 backdrop-blur-md border-b border-slate-200 dark:border-slate-800 transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <div 
          onClick={() => onSelectTab('landing')}
          className="flex items-center gap-3 cursor-pointer group"
        >
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-700 to-indigo-500 flex items-center justify-center text-white shadow-md shadow-blue-500/20 group-hover:scale-105 transition-transform">
            <Brain className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-lg tracking-tight text-slate-900 dark:text-white">
                NeuroScan<span className="text-blue-600 dark:text-blue-400">AI</span>
              </span>
              <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-blue-100 dark:bg-blue-950 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800">
                v1.0
              </span>
            </div>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-none">
              3D Brain Tumor Volumetrics
            </p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="hidden md:flex items-center gap-1">
          {navItems.map((item) => {
            const isActive = currentTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onSelectTab(item.id)}
                className={`px-3.5 py-2 text-sm font-medium rounded-lg transition-all ${
                  isActive
                    ? 'text-blue-700 dark:text-blue-400 bg-blue-50 dark:bg-blue-950/60 font-semibold'
                    : 'text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800/60'
                }`}
              >
                {item.label}
              </button>
            );
          })}
        </nav>

        {/* Status Pill & Controls */}
        <div className="flex items-center gap-3">
          {/* Model Status Pill */}
          <div
            title={
              modelAvailable
                ? `Model Checkpoint Loaded (${deviceInfo})`
                : 'Checkpoint uninitialized. Please run Colab training to generate weights.'
            }
            className={`hidden sm:flex items-center gap-2 px-2.5 py-1 rounded-full text-xs font-medium border ${
              modelAvailable
                ? 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800'
                : 'bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 border-amber-200 dark:border-amber-800'
            }`}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                modelAvailable ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'
              }`}
            />
            <span>{modelAvailable ? 'Model Ready' : 'Checkpoint Unavailable'}</span>
            <span className="text-[10px] text-slate-400 border-l border-slate-300 dark:border-slate-700 pl-1.5 flex items-center gap-0.5">
              <Cpu className="w-3 h-3 inline" /> {deviceInfo.toUpperCase()}
            </span>
          </div>

          {/* Theme Toggle */}
          <button
            onClick={onToggleTheme}
            className="p-2 text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
            title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
            aria-label="Toggle color theme"
          >
            {isDark ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4" />}
          </button>
        </div>
      </div>
    </header>
  );
};
