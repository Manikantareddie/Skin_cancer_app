import React from 'react';
import { AlertTriangle, ArrowLeft, HelpCircle } from 'lucide-react';
import type { ImageValidationResult } from '../api/types';

interface ValidationAlertProps {
  validation: ImageValidationResult;
  onReset: () => void;
}

export const ValidationAlert: React.FC<ValidationAlertProps> = ({ validation, onReset }) => {
  return (
    <div className="max-w-2xl mx-auto bg-white rounded-3xl border border-amber-200 shadow-md p-6 md:p-8">
      <div className="flex items-start gap-4 mb-6">
        <div className="w-12 h-12 rounded-2xl bg-amber-50 border border-amber-200 text-amber-600 flex items-center justify-center shrink-0">
          <AlertTriangle className="w-6 h-6" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-slate-900 mb-1">
            Image Not Accepted for Screening
          </h2>
          <p className="text-sm text-slate-600 leading-relaxed">
            The safety validation gate determined that this image does not appear to be a focused skin lesion photograph.
            To avoid misleading results, the model only screens close-up dermatological photographs.
          </p>
        </div>
      </div>

      {/* Specific Reasons */}
      <div className="bg-amber-50/60 rounded-2xl border border-amber-100 p-5 mb-6">
        <h4 className="text-xs font-bold uppercase tracking-wider text-amber-900 mb-2.5 flex items-center gap-1.5">
          <HelpCircle className="w-3.5 h-3.5" />
          Validation Findings:
        </h4>
        <ul className="space-y-1.5 text-xs text-amber-900 pl-4 list-disc">
          {validation.reasons.map((reason, index) => (
            <li key={index} className="font-medium leading-relaxed">
              {reason}
            </li>
          ))}
        </ul>
      </div>

      {/* Technical Diagnostic Metrics */}
      <div className="bg-slate-50 rounded-2xl p-4 border border-slate-200/80 mb-6 text-xs text-slate-600">
        <div className="font-semibold text-slate-800 mb-2">Automated Quality Checks:</div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-slate-700">
          <div>
            <span className="text-slate-400 block text-[10px] uppercase">Skin Ratio</span>
            <span className="font-bold">{(validation.metrics.skin_ratio * 100).toFixed(1)}%</span>
          </div>
          <div>
            <span className="text-slate-400 block text-[10px] uppercase">Image Contrast</span>
            <span className="font-bold">{validation.metrics.contrast.toFixed(1)}</span>
          </div>
          <div>
            <span className="text-slate-400 block text-[10px] uppercase">Face Detected</span>
            <span className="font-bold">{validation.metrics.face_detected ? 'Yes (Rejected)' : 'None'}</span>
          </div>
          <div>
            <span className="text-slate-400 block text-[10px] uppercase">Document / Graphic</span>
            <span className="font-bold">{validation.metrics.document_like ? 'Yes (Rejected)' : 'None'}</span>
          </div>
        </div>
      </div>

      {/* Reset Action */}
      <div className="flex justify-end">
        <button
          onClick={onReset}
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-teal-700 hover:bg-teal-800 text-white font-bold text-sm shadow-xs transition-colors cursor-pointer"
        >
          <ArrowLeft className="w-4 h-4" />
          Upload a Clear Lesion Photo
        </button>
      </div>
    </div>
  );
};
