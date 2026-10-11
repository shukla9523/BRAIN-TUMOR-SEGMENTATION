import React, { useState } from 'react';
import { AlertTriangle, X } from 'lucide-react';

interface Props {
  dismissible?: boolean;
}

export const DisclaimerBanner: React.FC<Props> = ({ dismissible = false }) => {
  const [dismissed, setDismissed] = useState(false);

  if (dismissed) return null;

  return (
    <aside aria-label="Medical research prototype disclaimer" className="bg-amber-50 dark:bg-amber-950/40 border-b border-amber-200 dark:border-amber-900/50 px-4 py-2.5 text-xs text-amber-900 dark:text-amber-200 transition-all">
      <div className="max-w-7xl mx-auto flex items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0" />
          <p>
            <span className="font-semibold uppercase tracking-wider text-amber-800 dark:text-amber-300 mr-1.5">
              Research & Educational Prototype Only:
            </span>
            NeuroScan AI is not an FDA-approved or CE-marked medical device. Model-derived volumetric measurements are
            voxel approximations for benchmarking. Clinical diagnosis must always be established by a qualified radiologist.
          </p>
        </div>
        {dismissible && (
          <button
            onClick={() => setDismissed(true)}
            className="p-1 hover:bg-amber-200/50 dark:hover:bg-amber-900/50 rounded text-amber-700 dark:text-amber-400"
            title="Dismiss notice"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        )}
      </div>
    </aside>
  );
};
