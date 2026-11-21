import React from 'react';
import { AlertTriangle, ArrowLeft, HelpCircle } from 'lucide-react';
import type { ImageValidationResult } from '../api/types';

interface ValidationAlertProps {
  validation: ImageValidationResult;
  onReset: () => void;
}

export const ValidationAlert: React.FC<ValidationAlertProps> = ({ validation, onReset }) => {
  return (
    <div className="max-w-2xl w-full mx-auto bg-white rounded-2xl sm:rounded-3xl border border-amber-200 shadow-md p-4 sm:p-6 md:p-8 space-y-4 sm:space-y-6">
      <div className="flex flex-col sm:flex-row items-start gap-3 sm:gap-4">
        <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-xl sm:rounded-2xl bg-amber-50 border border-amber-200 text-amber-600 flex items-center justify-center shrink-0">
          <AlertTriangle className="w-5 h-5 sm:w-6 sm:h-6" />
        </div>
        <div>
          <h2 className="text-lg sm:text-xl font-bold text-slate-900 mb-1 leading-snug">
            Image Not Accepted for Screening
          </h2>
          <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
            The safety validation gate determined that this image does not appear to be a focused skin lesion photograph.
            To avoid misleading results, the model only screens close-up dermatological photographs.
          </p>
        </div>
      </div>

      {/* Specific Reasons */}
      <div className="bg-amber-50/60 rounded-xl sm:rounded-2xl border border-amber-100 p-4 sm:p-5">
        <h4 className="text-[11px] sm:text-xs font-bold uppercase tracking-wider text-amber-900 mb-2 flex items-center gap-1.5">
          <HelpCircle className="w-3.5 h-3.5 shrink-0" />
          <span>Validation Findings:</span>
        </h4>
        <ul className="space-y-1.5 text-xs text-amber-900 pl-4 list-disc leading-relaxed">
          {validation.reasons.map((reason, index) => (
            <li key={index} className="font-medium leading-relaxed">
              {reason}
            </li>
          ))}
        </ul>
      </div>

      {/* Technical Diagnostic Metrics */}
      <div className="bg-slate-50 rounded-xl sm:rounded-2xl p-3.5 sm:p-4 border border-slate-200/80 text-xs text-slate-600">
        <div className="font-semibold text-slate-800 mb-2">Automated Quality Checks:</div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 sm:gap-3 text-slate-700">
          <div className="p-2 bg-white rounded-lg border border-slate-200">
            <span className="text-slate-400 block text-[10px] uppercase">Skin Ratio</span>
            <span className="font-bold text-sm sm:text-base">{(validation.metrics.skin_ratio * 100).toFixed(1)}%</span>
          </div>
          <div className="p-2 bg-white rounded-lg border border-slate-200">
            <span className="text-slate-400 block text-[10px] uppercase">Contrast</span>
            <span className="font-bold text-sm sm:text-base">{validation.metrics.contrast.toFixed(1)}</span>
          </div>
          <div className="p-2 bg-white rounded-lg border border-slate-200">
            <span className="text-slate-400 block text-[10px] uppercase">Face Detected</span>
            <span className="font-bold text-xs sm:text-sm">{validation.metrics.face_detected ? 'Yes (Rejected)' : 'None'}</span>
          </div>
          <div className="p-2 bg-white rounded-lg border border-slate-200">
            <span className="text-slate-400 block text-[10px] uppercase">Document / Text</span>
            <span className="font-bold text-xs sm:text-sm">{validation.metrics.document_like ? 'Yes (Rejected)' : 'None'}</span>
          </div>
        </div>
      </div>

      {/* Reset Action */}
      <div className="flex justify-stretch sm:justify-end">
        <button
          onClick={onReset}
          className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-teal-700 hover:bg-teal-800 text-white font-bold text-xs sm:text-sm shadow-xs transition-colors cursor-pointer min-h-[44px]"
        >
          <ArrowLeft className="w-4 h-4 shrink-0" />
          <span>Upload a Clear Lesion Photo</span>
        </button>
      </div>
    </div>
  );
};
