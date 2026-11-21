import React, { useState } from 'react';
import {
  RotateCcw,
  Calendar,
  Hash,
  AlertTriangle,
  CheckCircle,
  FileDown,
  RefreshCw,
} from 'lucide-react';
import type { AnalysisResponse } from '../api/types';
import { GradCamViewer } from './GradCamViewer';
import { ABCDECard } from './ABCDECard';
import { AiSummaryCard } from './AiSummaryCard';
import { downloadPdfReport } from '../api/client';

interface ResultsViewProps {
  analysis: AnalysisResponse;
  originalFile: File;
  originalImageUrl: string;
  onReset: () => void;
}

export const ResultsView: React.FC<ResultsViewProps> = ({
  analysis,
  originalFile,
  originalImageUrl,
  onReset,
}) => {
  const [downloading, setDownloading] = useState(false);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  const prediction = analysis.prediction!;
  const abcde = analysis.abcde!;
  const clinicalRisk = analysis.clinical_risk!;

  const isMalignant = prediction.predicted_label === 'Malignant';

  const handleDownloadPdf = async () => {
    if (!analysis.heatmap_base64) return;
    setDownloading(true);
    setDownloadError(null);
    try {
      await downloadPdfReport({
        originalFile,
        heatmapBase64: analysis.heatmap_base64,
        prediction: prediction.predicted_label,
        confidence: prediction.confidence_score,
        riskLevel: clinicalRisk.risk_level,
        abcdResults: abcde.raw_dictionary,
        aiSummary: `AI-Assisted Lesion Screening\nPrediction: ${prediction.predicted_label} (${prediction.confidence_score.toFixed(2)}% confidence)\nOverall Clinical Risk: ${clinicalRisk.risk_level}`,
        caseId: analysis.case_id,
      });
    } catch (err: any) {
      setDownloadError(err?.message || 'Failed to download PDF report.');
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="max-w-6xl w-full mx-auto space-y-4 sm:space-y-6 pb-16">
      {/* Action Top Bar */}
      <div className="bg-white rounded-xl sm:rounded-2xl border border-slate-200/90 shadow-xs p-3.5 sm:p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 sm:gap-4">
        <div className="flex flex-wrap items-center gap-2 sm:gap-3 text-xs text-slate-500">
          <div className="flex items-center gap-1.5 font-mono font-semibold text-slate-800 bg-slate-50 px-2.5 py-1.5 rounded-lg border border-slate-200/60 text-[11px] sm:text-xs">
            <Hash className="w-3.5 h-3.5 text-teal-700 shrink-0" />
            <span>Case ID:</span>
            <span className="truncate max-w-[150px] sm:max-w-none">{analysis.case_id}</span>
          </div>
          <div className="flex items-center gap-1.5 text-[11px] sm:text-xs">
            <Calendar className="w-3.5 h-3.5 text-slate-400 shrink-0" />
            <span>{new Date(analysis.timestamp).toLocaleDateString()}</span>
          </div>
        </div>

        <div className="grid grid-cols-2 sm:flex items-center gap-2 sm:gap-2.5 w-full sm:w-auto">
          <button
            onClick={onReset}
            className="px-3 sm:px-4 py-2 rounded-xl text-xs font-bold text-slate-700 hover:text-slate-900 bg-slate-50 hover:bg-slate-100 border border-slate-200 transition-colors flex items-center justify-center gap-1.5 cursor-pointer min-h-[38px]"
          >
            <RotateCcw className="w-3.5 h-3.5 shrink-0" />
            <span>New</span>
          </button>
          <button
            onClick={handleDownloadPdf}
            disabled={downloading}
            className="px-3 sm:px-4 py-2 rounded-xl text-xs font-bold text-white bg-teal-700 hover:bg-teal-800 shadow-sm transition-colors flex items-center justify-center gap-1.5 cursor-pointer disabled:opacity-50 min-h-[38px]"
          >
            {downloading ? (
              <RefreshCw className="w-3.5 h-3.5 animate-spin shrink-0" />
            ) : (
              <FileDown className="w-3.5 h-3.5 shrink-0" />
            )}
            <span>PDF Report</span>
          </button>
        </div>
      </div>

      {downloadError && (
        <div className="p-3.5 rounded-xl bg-red-50 border border-red-200 text-red-800 text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{downloadError}</span>
        </div>
      )}

      {/* Primary Screening Alert Card */}
      <div className="bg-white rounded-2xl sm:rounded-3xl border border-slate-200/90 shadow-md p-4 sm:p-6 md:p-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 sm:gap-4 pb-4 border-b border-slate-100 mb-5">
          <div className="flex items-center gap-2.5">
            <span
              className={`p-2 rounded-xl flex items-center justify-center ${
                isMalignant ? 'bg-amber-100 text-amber-800' : 'bg-emerald-100 text-emerald-800'
              }`}
            >
              {isMalignant ? <AlertTriangle className="w-5 h-5" /> : <CheckCircle className="w-5 h-5" />}
            </span>
            <div>
              <div className="text-xs uppercase tracking-wider font-bold text-slate-400">Model Screening Verdict</div>
              <h2 className="text-xl sm:text-2xl font-black text-slate-900 leading-snug">
                {prediction.predicted_label} Lesion Pattern
              </h2>
            </div>
          </div>

          <div className="self-start sm:self-auto">
            <span
              className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider border ${
                isMalignant
                  ? 'bg-amber-50 text-amber-900 border-amber-200'
                  : 'bg-emerald-50 text-emerald-900 border-emerald-200'
              }`}
            >
              {prediction.model_risk_label}
            </span>
          </div>
        </div>

        {/* Metrics Bar */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/70">
            <span className="text-slate-400 block mb-1">Model Output Score</span>
            <span className="text-lg sm:text-xl font-black text-slate-800">{prediction.confidence_score.toFixed(2)}%</span>
          </div>
          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/70">
            <span className="text-slate-400 block mb-1">Benign Pattern Probability</span>
            <span className="text-lg sm:text-xl font-bold text-emerald-700">{prediction.benign_probability.toFixed(2)}%</span>
          </div>
          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/70">
            <span className="text-slate-400 block mb-1">Malignant Pattern Probability</span>
            <span className="text-lg sm:text-xl font-bold text-amber-700">{prediction.malignant_probability.toFixed(2)}%</span>
          </div>
        </div>
      </div>

      {/* Grad-CAM Viewer */}
      <GradCamViewer
        originalImageUrl={originalImageUrl}
        heatmapBase64={analysis.heatmap_base64}
      />

      {/* ABCDE Feature Analysis */}
      <ABCDECard abcde={abcde} clinicalRisk={clinicalRisk} />

      {/* NVIDIA AI Explanation */}
      <AiSummaryCard analysis={analysis} />
    </div>
  );
};
