import React from 'react';
import { X, Clock, Info, CheckCircle2 } from 'lucide-react';

export default function ComingSoonModal({ isOpen, onClose, featureName }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md transition-opacity">
      <div className="relative w-full max-w-md bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-2xl shadow-indigo-500/10 transform transition-all duration-300 scale-100">
        
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Modal Content */}
        <div className="flex flex-col items-center text-center">
          <div className="w-16 h-16 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 mb-5">
            <Clock className="w-8 h-8 animate-pulse" />
          </div>

          <span className="px-3 py-1 text-xs font-bold uppercase tracking-wider text-indigo-400 bg-indigo-500/10 rounded-full border border-indigo-500/20 mb-3">
            Coming Soon
          </span>

          <h3 className="text-2xl font-bold text-white mb-2">
            {featureName || 'Module Under Development'}
          </h3>

          <p className="text-slate-400 text-sm leading-relaxed mb-6">
            The data ingestion workflow for <strong className="text-slate-200">{featureName}</strong> is scheduled for integration. Batch Excel/CSV imports and automated validation pipelines will be enabled soon.
          </p>

          <div className="w-full bg-slate-950/60 rounded-2xl p-4 border border-slate-800/80 mb-6 text-left space-y-2">
            <div className="flex items-center gap-2.5 text-xs text-slate-300">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
              <span>Bulk CSV & XLSX Data Ingestion</span>
            </div>
            <div className="flex items-center gap-2.5 text-xs text-slate-300">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
              <span>Automated Data Integrity Validation</span>
            </div>
            <div className="flex items-center gap-2.5 text-xs text-slate-300">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
              <span>Real-time KPI Score Update Trigger</span>
            </div>
          </div>

          <button
            onClick={onClose}
            className="w-full py-3 rounded-xl font-bold text-sm bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white shadow-lg shadow-indigo-500/25 transition-all duration-200"
          >
            Got it, thanks!
          </button>
        </div>
      </div>
    </div>
  );
}
