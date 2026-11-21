import React, { useState } from 'react';
import {
  RotateCcw,
  ShieldAlert,
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
    <div className="max-w-6xl mx-auto space-y-6 pb-16">
      {/* Action Top Bar */}
      <div className="bg-white rounded-2xl border border-slate-200/90 shadow-xs p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500">
          <div className="flex items-center gap-1.5 font-mono font-semibold text-slate-800 bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200/60">
            <Hash className="w-3.5 h-3.5 text-teal-700" />
            <span>Case ID:</span>
            <span>{analysis.case_id}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5 text-slate-400" />
            <span>{new Date(analysis.timestamp).toLocaleString()}</span>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={onReset}
            className="px-4 py-2 rounded-xl text-xs font-bold text-slate-700 hover:text-slate-900 bg-slate-50 hover:bg-slate-100 border border-slate-200 transition-colors flex items-center gap-1.5 cursor-pointer"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            New Screening
          </button>
          <button
            onClick={handleDownloadPdf}
            disabled={downloading}
            className="px-4 py-2 rounded-xl text-xs font-bold text-white bg-teal-700 hover:bg-teal-800 shadow-sm transition-colors flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
          >
            {downloading ? (
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <FileDown className="w-3.5 h-3.5" />
            )}
            Download PDF Report
          </button>
        </div>
      </div>

      {downloadError && (
        <div className="p-3 bg-rose-50 border border-rose-200 text-rose-800 text-xs rounded-xl flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{downloadError}</span>
        </div>
      )}

      {/* Primary Screening Prediction Banner */}
      <div
        className={`rounded-3xl border p-6 md:p-8 shadow-sm transition-all ${
          isMalignant
            ? 'bg-gradient-to-r from-rose-50/70 via-white to-amber-50/40 border-rose-200'
            : 'bg-gradient-to-r from-emerald-50/70 via-white to-teal-50/40 border-emerald-200'
        }`}
      >
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
          {/* Output Classification */}
          <div className="lg:col-span-7 space-y-3">
            <div className="flex items-center gap-2.5">
              <span
                className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-extrabold uppercase tracking-wider ${
                  isMalignant
                    ? 'bg-rose-100 text-rose-800 border border-rose-200'
                    : 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                }`}
              >
                {isMalignant ? <AlertTriangle className="w-3.5 h-3.5" /> : <CheckCircle className="w-3.5 h-3.5" />}
                Primary AI Screening Output
              </span>
              <span
                className={`px-2.5 py-0.5 rounded-full text-[11px] font-bold uppercase tracking-wider ${
                  clinicalRisk.risk_level === 'HIGH'
                    ? 'bg-rose-100 text-rose-800'
                    : clinicalRisk.risk_level === 'MODERATE'
                    ? 'bg-amber-100 text-amber-800'
                    : 'bg-emerald-100 text-emerald-800'
                }`}
              >
                {clinicalRisk.risk_level} Risk
              </span>
            </div>

            <div>
              <div className="text-3xl md:text-4xl font-extrabold text-slate-900 tracking-tight">
                {prediction.predicted_label}
              </div>
              <p className="text-sm text-slate-600 mt-1">
                Model calculated output confidence:{' '}
                <span className="font-bold text-slate-900">{prediction.confidence_score.toFixed(2)}%</span>
              </p>
            </div>

            {/* Performance Context Disclaimer */}
            <div className="pt-2 text-xs text-slate-500 leading-relaxed border-t border-slate-200/60 max-w-xl flex items-start gap-2">
              <ShieldAlert className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
              <span>
                <strong>Model Performance Context:</strong> This dual-branch ResNet18 + Texture model demonstrated 84.23% test accuracy and 80.89% recall on dermatological evaluation benchmarks. It is an educational screening aid, not a definitive diagnosis.
              </span>
            </div>
          </div>

          {/* Probability Breakdown Gauge */}
          <div className="lg:col-span-5 bg-white rounded-2xl border border-slate-200 p-5 shadow-xs space-y-3">
            <div className="text-xs font-bold text-slate-700 uppercase tracking-wider">
              Output Probability Distribution
            </div>

            {/* Progress bar */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs font-semibold">
                <span className="text-emerald-700">Benign: {prediction.benign_probability.toFixed(1)}%</span>
                <span className="text-rose-700">Malignant: {prediction.malignant_probability.toFixed(1)}%</span>
              </div>
              <div className="h-3 w-full bg-slate-100 rounded-full overflow-hidden flex">
                <div
                  style={{ width: `${prediction.benign_probability}%` }}
                  className="bg-emerald-500 h-full transition-all duration-500"
                />
                <div
                  style={{ width: `${prediction.malignant_probability}%` }}
                  className="bg-rose-500 h-full transition-all duration-500"
                />
              </div>
            </div>

            <div className="text-[11px] text-slate-400 italic">
              Estimated softmax confidence over binary classification classes.
            </div>
          </div>
        </div>
      </div>

      {/* Main 2-Column Clinical Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Visual Attention & Grad-CAM */}
        <div className="lg:col-span-6 space-y-6">
          <GradCamViewer
            originalImageUrl={originalImageUrl}
            heatmapBase64={analysis.heatmap_base64}
          />
        </div>

        {/* Right Column: ABCDE Findings & AI Clinical Summary */}
        <div className="lg:col-span-6 space-y-6">
          <ABCDECard abcde={abcde} clinicalRisk={clinicalRisk} />
          <AiSummaryCard analysis={analysis} />
        </div>
      </div>
    </div>
  );
};
