import React from 'react';
import { X, Clock, Info, CheckCircle2 } from 'lucide-react';

export default function ComingSoonModal({ isOpen, onClose, featureName }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#1E293B]/40 backdrop-blur-md transition-opacity">
      <div className="relative w-full max-w-md bg-[#FFFFFF] border border-[#E2E8F0] rounded-3xl p-6 shadow-2xl transform transition-all duration-300 scale-100">
        
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-2 rounded-xl text-[#64748B] hover:text-[#1E293B] hover:bg-[#EFF6FF] transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Modal Content */}
        <div className="flex flex-col items-center text-center">
          <div className="w-16 h-16 rounded-2xl bg-[#EFF6FF] border border-[#DBEAFE] flex items-center justify-center text-[#2563EB] mb-5">
            <Clock className="w-8 h-8 animate-pulse" />
          </div>

          <span className="px-3 py-1 text-xs font-bold uppercase tracking-wider text-[#2563EB] bg-[#DBEAFE] rounded-full border border-[#2563EB]/20 mb-3">
            Coming Soon
          </span>

          <h3 className="text-2xl font-bold text-[#1E293B] mb-2">
            {featureName || 'Module Under Development'}
          </h3>

          <p className="text-[#64748B] text-sm leading-relaxed mb-6">
            The data ingestion workflow for <strong className="text-[#1E293B]">{featureName}</strong> is scheduled for integration. Batch Excel/CSV imports and automated validation pipelines will be enabled soon.
          </p>

          <div className="w-full bg-[#F8FAFC] rounded-2xl p-4 border border-[#E2E8F0] mb-6 text-left space-y-2">
            <div className="flex items-center gap-2.5 text-xs text-[#1E293B]">
              <CheckCircle2 className="w-4 h-4 text-[#10B981] flex-shrink-0" />
              <span>Bulk CSV & XLSX Data Ingestion</span>
            </div>
            <div className="flex items-center gap-2.5 text-xs text-[#1E293B]">
              <CheckCircle2 className="w-4 h-4 text-[#10B981] flex-shrink-0" />
              <span>Automated Data Integrity Validation</span>
            </div>
            <div className="flex items-center gap-2.5 text-xs text-[#1E293B]">
              <CheckCircle2 className="w-4 h-4 text-[#10B981] flex-shrink-0" />
              <span>Real-time KPI Score Update Trigger</span>
            </div>
          </div>

          <button
            onClick={onClose}
            className="w-full py-3 rounded-xl font-bold text-sm bg-[#2563EB] hover:bg-[#3B82F6] text-white shadow-md shadow-blue-500/20 transition-all duration-200"
          >
            Got it, thanks!
          </button>
        </div>
      </div>
    </div>
  );
}
