import React from 'react';
import {
  RotateCcw,
  Calendar,
  Hash,
  AlertTriangle,
  CheckCircle,
  FileText,
  Stethoscope,
  Info,
} from 'lucide-react';
import type { AIExplanationResponse, AnalysisResponse } from '../api/types';
import { GradCamViewer } from './GradCamViewer';
import { ABCDECard } from './ABCDECard';
import { AiSummaryCard } from './AiSummaryCard';

interface ResultsWorkspaceProps {
  analysis: AnalysisResponse;
  originalFile: File;
  originalImageUrl: string;
  onReset: () => void;
  onNavigateToReport: () => void;
  aiSummary: AIExplanationResponse | null;
  onSummaryLoaded: (summary: AIExplanationResponse) => void;
}

export const ResultsWorkspace: React.FC<ResultsWorkspaceProps> = ({
  analysis,
  originalImageUrl,
  onReset,
  onNavigateToReport,
  aiSummary,
  onSummaryLoaded,
}) => {
  const prediction = analysis.prediction!;
  const abcde = analysis.abcde!;
  const clinicalRisk = analysis.clinical_risk!;

  const isMalignant = prediction.predicted_label === 'Malignant';

  return (
    <div className="max-w-[1140px] w-full mx-auto space-y-8 pb-20">
      {/* Top Clinical Header & Stage Actions */}
      <div className="bg-white rounded-3xl border border-slate-200/90 shadow-xs p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500">
          <div className="flex items-center gap-1.5 font-mono font-semibold text-slate-800 bg-slate-50 px-3 py-1.5 rounded-xl border border-slate-200/70">
            <Hash className="w-3.5 h-3.5 text-teal-700" />
            <span>Case ID:</span>
            <span>{analysis.case_id}</span>
          </div>
          <div className="flex items-center gap-1.5 bg-slate-50 px-3 py-1.5 rounded-xl border border-slate-200/70">
            <Calendar className="w-3.5 h-3.5 text-slate-400" />
            <span>{new Date(analysis.timestamp).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}</span>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={onReset}
            className="px-4 py-2.5 rounded-xl text-xs font-bold text-slate-700 hover:text-slate-900 bg-slate-50 hover:bg-slate-100 border border-slate-200 transition-colors flex items-center gap-1.5 cursor-pointer"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            New Screening
          </button>
          <button
            onClick={onNavigateToReport}
            className="px-4 py-2.5 rounded-xl text-xs font-bold text-white bg-teal-700 hover:bg-teal-800 shadow-sm transition-all flex items-center gap-2 cursor-pointer"
          >
            <FileText className="w-4 h-4" />
            <span>View Full Report</span>
          </button>
        </div>
      </div>

      {/* SECTION 1: Screening Overview */}
      <section className="bg-white rounded-3xl border border-slate-200/90 shadow-xs p-6 md:p-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
          {/* Uploaded Lesion Image Thumbnail */}
          <div className="lg:col-span-4 flex flex-col items-center">
            <div className="relative w-full max-w-[280px] aspect-square rounded-2xl overflow-hidden border border-slate-200 bg-slate-100 shadow-inner flex items-center justify-center">
              <img
                src={originalImageUrl}
                alt="Analyzed Skin Lesion"
                className="w-full h-full object-cover select-none"
              />
              <div className="absolute bottom-2 left-2 right-2 bg-slate-900/75 backdrop-blur-xs text-white text-[11px] font-medium py-1 px-2.5 rounded-lg text-center">
                Uploaded Lesion Photo
              </div>
            </div>
          </div>

          {/* Classification & Clear Non-Alarmist Interpretation */}
          <div className="lg:col-span-8 space-y-4">
            <div className="flex flex-wrap items-center gap-2.5">
              <span
                className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${
                  isMalignant
                    ? 'bg-amber-100 text-amber-900 border border-amber-200'
                    : 'bg-emerald-100 text-emerald-900 border border-emerald-200'
                }`}
              >
                {isMalignant ? <AlertTriangle className="w-3.5 h-3.5" /> : <CheckCircle className="w-3.5 h-3.5" />}
                Screening Assessment
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-slate-100 text-slate-700 border border-slate-200">
                {clinicalRisk.risk_level} Priority Review
              </span>
            </div>

            <div>
              <div className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
                Model classified this image in the{' '}
                <span className={isMalignant ? 'text-amber-800' : 'text-teal-800'}>
                  {prediction.predicted_label.toLowerCase()}
                </span>{' '}
                category
              </div>
              <div className="text-xs text-slate-500 mt-1.5">
                Output Score:{' '}
                <span className="font-bold text-slate-800">{prediction.confidence_score.toFixed(2)}%</span>{' '}
                <span className="text-slate-400">
                  (Uncalibrated neural network output score; not a calibrated disease probability)
                </span>
              </div>
            </div>

            {/* Clear Professional Recommendation */}
            <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-2">
              <div className="flex items-center gap-2 text-xs font-bold text-slate-800">
                <Stethoscope className="w-4 h-4 text-teal-700 shrink-0" />
                <span>Recommendation for In-Person Professional Assessment:</span>
              </div>
              <p className="text-xs text-slate-600 leading-relaxed">
                {isMalignant
                  ? 'Because features matching malignant training patterns were detected, schedule an evaluation with a board-certified dermatologist for formal dermoscopy and clinical correlation.'
                  : 'While features align with benign training data, this automated screening cannot definitively exclude abnormal pathology. Maintain routine skin self-checks and consult a physician for new or changing lesions.'}
              </p>
            </div>

            {/* Performance Context */}
            <div className="text-[11px] text-slate-400 flex items-start gap-2 pt-1">
              <Info className="w-3.5 h-3.5 text-slate-400 shrink-0 mt-0.5" />
              <span>
                Model benchmark performance: 84.23% test accuracy, 80.89% recall. Automated screening aids are designed for clinical decision-support and do not replace histological biopsy.
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* SECTION 2: Visual Analysis (Grad-CAM) */}
      <section>
        <GradCamViewer
          originalImageUrl={originalImageUrl}
          heatmapBase64={analysis.heatmap_base64}
        />
      </section>

      {/* SECTION 3: Lesion Characteristics (ABCDE) */}
      <section>
        <ABCDECard abcde={abcde} clinicalRisk={clinicalRisk} />
      </section>

      {/* SECTION 4: AI Explanation (NVIDIA NIM Structured) */}
      <section>
        <AiSummaryCard
          analysis={analysis}
          initialSummary={aiSummary}
          onSummaryLoaded={onSummaryLoaded}
        />
      </section>

      {/* Action Footer to Proceed to Report Stage */}
      <div className="p-6 rounded-3xl bg-teal-50/70 border border-teal-200/80 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div>
          <h4 className="text-sm font-bold text-teal-950">
            Ready to review or print the official screening summary?
          </h4>
          <p className="text-xs text-teal-800/80 mt-0.5">
            Access the comprehensive formatted clinical report with complete findings and downloadable PDF.
          </p>
        </div>
        <button
          onClick={onNavigateToReport}
          className="px-5 py-2.5 rounded-xl text-xs font-bold text-white bg-teal-700 hover:bg-teal-800 shadow-sm transition-all flex items-center gap-2 shrink-0 cursor-pointer"
        >
          <FileText className="w-4 h-4" />
          <span>Go to Report View</span>
        </button>
      </div>
    </div>
  );
};
