import React, { useState } from 'react';
import {
  FileDown,
  RotateCcw,
  ArrowLeft,
  Calendar,
  Hash,
  Stethoscope,
  ShieldAlert,
  Printer,
  RefreshCw,
  AlertTriangle,
  Ruler,
  History,
} from 'lucide-react';
import type { AIExplanationResponse, AnalysisResponse } from '../api/types';
import { downloadPdfReport } from '../api/client';

interface ReportStageProps {
  analysis: AnalysisResponse;
  originalFile: File;
  originalImageUrl: string;
  aiSummary: AIExplanationResponse | null;
  onBackToAnalysis: () => void;
  onReset: () => void;
}

export const ReportStage: React.FC<ReportStageProps> = ({
  analysis,
  originalFile,
  originalImageUrl,
  aiSummary,
  onBackToAnalysis,
  onReset,
}) => {
  const [downloading, setDownloading] = useState(false);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  const prediction = analysis.prediction!;
  const abcde = analysis.abcde!;
  const clinicalRisk = analysis.clinical_risk!;
  const isMalignant = prediction.predicted_label === 'Malignant';
  const diameter = abcde.diameter;
  const evolution = abcde.evolution;

  const handleDownloadPdf = async () => {
    if (!analysis.heatmap_base64) return;
    setDownloading(true);
    setDownloadError(null);

    // Format AI summary text for the PDF generator
    let summaryText = `AI-Assisted Lesion Screening Report\nScreening Category: Model classified into '${prediction.predicted_label}' category (${prediction.confidence_score.toFixed(2)}% score)\nOverall Clinical Priority: ${clinicalRisk.risk_level}\n\n`;

    if (aiSummary?.explanation) {
      summaryText += `Clinical Interpretation: ${aiSummary.explanation.result_explanation}\n\n`;
      summaryText += "Observed Features:\n" + aiSummary.explanation.observed_features.map(f => `• ${f.feature}: ${f.explanation}`).join("\n") + "\n\n";
      summaryText += "Limitations:\n" + aiSummary.explanation.limitations.map(l => `• ${l}`).join("\n") + "\n\n";
      summaryText += "Next Steps:\n" + aiSummary.explanation.next_steps.map(s => `• ${s}`).join("\n");
    } else {
      summaryText += "Automated screening aid. Does not replace physical dermatoscopy or biopsy.";
    }

    let diameterDetail = diameter
      ? `Status: ${diameter.status}. ${
          diameter.longest_diameter_mm
            ? `Longest diameter: ${diameter.longest_diameter_mm} mm (${diameter.measurement_method}).`
            : diameter.measurement_method
        }`
      : undefined;

    let evolutionDetail = evolution
      ? `Status: ${evolution.status}. Comparability: ${evolution.comparability}. ${evolution.clinical_summary}`
      : undefined;

    try {
      await downloadPdfReport({
        originalFile,
        heatmapBase64: analysis.heatmap_base64,
        prediction: prediction.predicted_label,
        confidence: prediction.confidence_score,
        riskLevel: clinicalRisk.risk_level,
        abcdResults: abcde.raw_dictionary,
        aiSummary: summaryText,
        caseId: analysis.case_id,
        differenceBase64: evolution?.difference_overlay_base64,
        diameterDetail,
        evolutionDetail,
      });
    } catch (err: any) {
      setDownloadError(err?.message || 'Failed to download PDF report.');
    } finally {
      setDownloading(false);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="max-w-[1140px] w-full mx-auto space-y-4 sm:space-y-6 pb-20 sm:pb-24">
      {/* Top Action Bar (Hidden when printing) */}
      <div className="print:hidden bg-white rounded-2xl sm:rounded-3xl border border-slate-200/90 shadow-xs p-3.5 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 sm:gap-4">
        <button
          onClick={onBackToAnalysis}
          className="px-3.5 sm:px-4 py-2 sm:py-2.5 rounded-xl text-xs font-bold text-slate-700 hover:text-slate-900 bg-slate-50 hover:bg-slate-100 border border-slate-200 transition-colors flex items-center justify-center sm:justify-start gap-2 cursor-pointer w-full sm:w-auto min-h-[40px]"
        >
          <ArrowLeft className="w-4 h-4 shrink-0" />
          <span>Back to Analysis</span>
        </button>

        <div className="grid grid-cols-2 sm:flex items-center gap-2 sm:gap-2.5 w-full sm:w-auto">
          <button
            onClick={onReset}
            className="px-3 sm:px-4 py-2 sm:py-2.5 rounded-xl text-xs font-bold text-slate-700 hover:text-slate-900 bg-slate-50 hover:bg-slate-100 border border-slate-200 transition-colors flex items-center justify-center gap-1.5 cursor-pointer min-h-[40px]"
          >
            <RotateCcw className="w-3.5 h-3.5 shrink-0" />
            <span>Reset</span>
          </button>
          <button
            onClick={handlePrint}
            className="px-3 sm:px-4 py-2 sm:py-2.5 rounded-xl text-xs font-bold text-slate-700 hover:text-slate-900 bg-slate-50 hover:bg-slate-100 border border-slate-200 transition-colors flex items-center justify-center gap-1.5 cursor-pointer min-h-[40px]"
          >
            <Printer className="w-3.5 h-3.5 shrink-0" />
            <span>Print</span>
          </button>
          <button
            onClick={handleDownloadPdf}
            disabled={downloading}
            className="col-span-2 sm:col-span-1 px-4 sm:px-5 py-2 sm:py-2.5 rounded-xl text-xs font-bold text-white bg-teal-700 hover:bg-teal-800 shadow-sm transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50 min-h-[40px]"
          >
            {downloading ? (
              <RefreshCw className="w-4 h-4 animate-spin shrink-0" />
            ) : (
              <FileDown className="w-4 h-4 shrink-0" />
            )}
            <span>Download Official PDF</span>
          </button>
        </div>
      </div>

      {downloadError && (
        <div className="print:hidden p-3.5 sm:p-4 bg-rose-50 border border-rose-200 text-rose-800 text-xs rounded-xl sm:rounded-2xl flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{downloadError}</span>
        </div>
      )}

      {/* Structured Medical Report Document */}
      <div className="bg-white rounded-2xl sm:rounded-3xl border border-slate-200 shadow-sm p-4 sm:p-8 md:p-12 space-y-6 sm:space-y-8 font-sans">
        {/* Document Header */}
        <div className="border-b border-slate-200 pb-4 sm:pb-6">
          <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
            <div>
              <div className="flex items-center gap-1.5 sm:gap-2 text-teal-800 font-bold text-[11px] sm:text-xs uppercase tracking-widest mb-1">
                <Stethoscope className="w-4 h-4 shrink-0" />
                <span>DermaAssist Decision Support</span>
              </div>
              <h1 className="text-xl sm:text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight leading-snug">
                AI Skin Lesion Screening Report
              </h1>
              <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                Automated multimodal screening evaluation • Educational research decision support
              </p>
            </div>

            <div className="bg-slate-50 border border-slate-200/80 rounded-xl sm:rounded-2xl p-3 sm:p-3.5 text-xs text-slate-600 space-y-1 sm:text-right shrink-0">
              <div className="flex sm:justify-end items-center gap-1.5 font-mono font-bold text-slate-900">
                <Hash className="w-3.5 h-3.5 text-teal-700 shrink-0" />
                <span>Case ID: {analysis.case_id}</span>
              </div>
              <div className="flex sm:justify-end items-center gap-1.5 text-slate-500 text-[11px]">
                <Calendar className="w-3 h-3 text-slate-400 shrink-0" />
                <span>{new Date(analysis.timestamp).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })}</span>
              </div>
              <div className="text-[11px] text-slate-400">Patient: Anonymous Screening Record</div>
            </div>
          </div>
        </div>

        {/* Section: Screening Assessment Summary */}
        <div className="space-y-2.5 sm:space-y-3">
          <h2 className="text-[11px] sm:text-xs font-bold text-slate-400 uppercase tracking-wider">
            1. Primary Screening Assessment
          </h2>
          <div className="p-4 sm:p-5 rounded-xl sm:rounded-2xl bg-slate-50/90 border border-slate-200/90 flex flex-col md:flex-row md:items-center justify-between gap-3 sm:gap-4">
            <div className="space-y-1">
              <div className="text-xs text-slate-500 font-medium">Model Classification Result</div>
              <div className="text-lg sm:text-xl md:text-2xl font-black text-slate-900 leading-snug">
                Model classified image into '{prediction.predicted_label}' category
              </div>
              <div className="text-xs text-slate-500 leading-relaxed">
                Uncalibrated Model Output Score:{' '}
                <span className="font-bold text-slate-800">{prediction.confidence_score.toFixed(2)}%</span>{' '}
                <span className="text-slate-400 block sm:inline mt-0.5 sm:mt-0">
                  (ResNet-18 + Texture Fusion, 84.23% test acc, 80.89% recall)
                </span>
              </div>
            </div>

            <div className="self-start md:self-auto shrink-0">
              <span
                className={`px-3.5 py-1.5 rounded-full text-xs font-extrabold uppercase tracking-wider border inline-block ${
                  isMalignant
                    ? 'bg-amber-100 text-amber-900 border-amber-300'
                    : 'bg-emerald-100 text-emerald-900 border-emerald-300'
                }`}
              >
                {clinicalRisk.risk_level} Priority Review
              </span>
            </div>
          </div>
        </div>

        {/* Section: Photographic & Neural Attention Inspection */}
        <div className="space-y-2.5 sm:space-y-3">
          <h2 className="text-[11px] sm:text-xs font-bold text-slate-400 uppercase tracking-wider">
            2. Visual Examination & Neural Attention
          </h2>
          <div className={`grid grid-cols-1 ${evolution?.difference_overlay_base64 ? 'md:grid-cols-3' : 'md:grid-cols-2'} gap-3 sm:gap-4`}>
            <div className="border border-slate-200 rounded-xl sm:rounded-2xl p-3 bg-slate-50/50 space-y-2 text-center">
              <div className="text-xs font-bold text-slate-700">Uploaded Lesion Photo</div>
              <div className="aspect-[4/3] rounded-xl overflow-hidden bg-slate-100 flex items-center justify-center border border-slate-200">
                <img
                  src={originalImageUrl}
                  alt="Original lesion"
                  className="w-full h-full object-contain"
                />
              </div>
            </div>

            <div className="border border-slate-200 rounded-xl sm:rounded-2xl p-3 bg-slate-50/50 space-y-2 text-center">
              <div className="text-xs font-bold text-slate-700">Grad-CAM Activation Heatmap</div>
              <div className="aspect-[4/3] rounded-xl overflow-hidden bg-slate-100 flex items-center justify-center border border-slate-200">
                {analysis.heatmap_base64 ? (
                  <img
                    src={analysis.heatmap_base64}
                    alt="Grad-CAM activation"
                    className="w-full h-full object-contain"
                  />
                ) : (
                  <span className="text-xs text-slate-400">Heatmap unavailable</span>
                )}
              </div>
            </div>

            {evolution?.difference_overlay_base64 && (
              <div className="border border-slate-200 rounded-xl sm:rounded-2xl p-3 bg-slate-50/50 space-y-2 text-center">
                <div className="text-xs font-bold text-slate-700">Longitudinal Difference Overlay</div>
                <div className="aspect-[4/3] rounded-xl overflow-hidden bg-slate-100 flex items-center justify-center border border-slate-200">
                  <img
                    src={evolution.difference_overlay_base64}
                    alt="Evolution difference overlay"
                    className="w-full h-full object-contain"
                  />
                </div>
              </div>
            )}
          </div>
          <div className="text-[10px] sm:text-[11px] text-slate-400 italic">
            * Grad-CAM highlights regions influencing the deep neural network’s activation, not surgical borders.
          </div>
        </div>

        {/* Section: ABCDE Morphological Characteristics Table */}
        <div className="space-y-2.5 sm:space-y-3">
          <h2 className="text-[11px] sm:text-xs font-bold text-slate-400 uppercase tracking-wider">
            3. ABCDE Morphological Criteria & Provenance
          </h2>
          <div className="overflow-x-auto -mx-1 sm:mx-0 rounded-xl sm:rounded-2xl border border-slate-200">
            <table className="w-full min-w-[480px] text-left text-xs border-collapse">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-slate-700 font-bold">
                  <th className="py-2.5 sm:py-3 px-3 sm:px-4 w-1/4">Criterion</th>
                  <th className="py-2.5 sm:py-3 px-3 sm:px-4 w-1/4">Evaluated Metric</th>
                  <th className="py-2.5 sm:py-3 px-3 sm:px-4 w-1/2">Clinical Evaluation Note</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-600">
                <tr>
                  <td className="py-2.5 sm:py-3 px-3 sm:px-4 font-bold text-slate-900">A — Asymmetry</td>
                  <td className="py-2.5 sm:py-3 px-3 sm:px-4 font-mono font-semibold text-slate-800">{abcde.asymmetry_score.toFixed(2)}</td>
                  <td className="py-2.5 sm:py-3 px-3 sm:px-4">{abcde.asymmetry_label}</td>
                </tr>
                <tr>
                  <td className="py-2.5 sm:py-3 px-3 sm:px-4 font-bold text-slate-900">B — Border Regularity</td>
                  <td className="py-2.5 sm:py-3 px-3 sm:px-4 font-mono font-semibold text-slate-800">{abcde.border_score.toFixed(2)}</td>
                  <td className="py-2.5 sm:py-3 px-3 sm:px-4">{abcde.border_label}</td>
                </tr>
                <tr>
                  <td className="py-2.5 sm:py-3 px-3 sm:px-4 font-bold text-slate-900">C — Color Variation</td>
                  <td className="py-2.5 sm:py-3 px-3 sm:px-4 font-mono font-semibold text-slate-800">{abcde.color_count} color clusters</td>
                  <td className="py-2.5 sm:py-3 px-3 sm:px-4">{abcde.color_label}</td>
                </tr>
                <tr className="bg-slate-50/30">
                  <td className="py-2.5 sm:py-3 px-3 sm:px-4 font-bold text-slate-900 flex items-center gap-1.5">
                    <Ruler className="w-3.5 h-3.5 text-teal-700 shrink-0" />
                    <span>D — Physical Diameter</span>
                  </td>
                  <td className="py-2.5 sm:py-3 px-3 sm:px-4">
                    {diameter?.status === 'MEASURED' && diameter.longest_diameter_mm ? (
                      <span className="font-bold text-slate-900">
                        {diameter.longest_diameter_mm.toFixed(1)} mm{' '}
                        <span className="text-[10px] font-semibold text-emerald-800 bg-emerald-100 px-1.5 py-0.5 rounded-full">
                          MEASURED
                        </span>
                      </span>
                    ) : diameter?.status === 'USER_REPORTED' && diameter.longest_diameter_mm ? (
                      <span className="font-bold text-slate-900">
                        {diameter.longest_diameter_mm.toFixed(1)} mm{' '}
                        <span className="text-[10px] font-semibold text-blue-800 bg-blue-100 px-1.5 py-0.5 rounded-full">
                          USER_REPORTED
                        </span>
                      </span>
                    ) : (
                      <span className="text-amber-800 font-semibold">UNAVAILABLE</span>
                    )}
                  </td>
                  <td className="py-2.5 sm:py-3 px-3 sm:px-4 leading-relaxed">
                    {diameter?.status === 'MEASURED' && diameter.longest_diameter_mm
                      ? `Longest Feret caliper diameter measured using calibrated scale (${diameter.pixels_per_mm} px/mm). 6mm reference guideline applies non-definitively.`
                      : diameter?.status === 'USER_REPORTED' && diameter.longest_diameter_mm
                      ? 'Patient or clinician manual caliper measurement. 6mm reference guideline applies non-definitively.'
                      : 'Physical diameter cannot be determined from this image without an in-frame calibrated reference scale.'}
                  </td>
                </tr>
                <tr className="bg-slate-50/50">
                  <td className="py-2.5 sm:py-3 px-3 sm:px-4 font-bold text-slate-900 flex items-center gap-1.5">
                    <History className="w-3.5 h-3.5 text-teal-700 shrink-0" />
                    <span>E — Evolution & History</span>
                  </td>
                  <td className="py-2.5 sm:py-3 px-3 sm:px-4">
                    <span
                      className={`text-[10px] font-black px-2 py-0.5 rounded-full uppercase tracking-wider ${
                        evolution?.status === 'OBSERVED'
                          ? 'bg-emerald-100 text-emerald-800'
                          : evolution?.status === 'REPORTED'
                          ? 'bg-blue-100 text-blue-800'
                          : evolution?.status === 'UNCERTAIN'
                          ? 'bg-amber-100 text-amber-800'
                          : 'bg-slate-200 text-slate-700'
                      }`}
                    >
                      {evolution?.status || 'NOT_ASSESSABLE'}
                    </span>
                  </td>
                  <td className="py-2.5 sm:py-3 px-3 sm:px-4 leading-relaxed">
                    {evolution?.status === 'OBSERVED'
                      ? `Digital registration across ${evolution.time_interval_display || 'two timepoints'} observed an apparent 2D area change of ${evolution.area_change_percent !== null && evolution.area_change_percent !== undefined ? (evolution.area_change_percent > 0 ? '+' : '') + evolution.area_change_percent + '%' : 'assessed'}.`
                      : evolution?.status === 'REPORTED'
                      ? evolution.clinical_summary
                      : evolution?.status === 'UNCERTAIN'
                      ? 'Camera angle, lighting, or focus differences prevent objective biological confirmation.'
                      : 'Not assessable — requires sequential chronological images or longitudinal patient history.'}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Section: AI Clinical Explanation & Guidance */}
        {aiSummary?.explanation && (
          <div className="space-y-2.5 sm:space-y-3">
            <h2 className="text-[11px] sm:text-xs font-bold text-slate-400 uppercase tracking-wider">
              4. AI Clinical Explanation & Patient Recommendations
            </h2>
            <div className="p-4 sm:p-5 rounded-xl sm:rounded-2xl bg-slate-50 border border-slate-200 space-y-3 sm:space-y-4 text-xs text-slate-700">
              <div>
                <span className="font-bold text-slate-900 block mb-1">Interpretation:</span>
                <p className="leading-relaxed">{aiSummary.explanation.result_explanation}</p>
              </div>

              <div>
                <span className="font-bold text-slate-900 block mb-1">Key Observations:</span>
                <ul className="space-y-1 pl-4 list-disc text-slate-600 leading-relaxed">
                  {aiSummary.explanation.observed_features.map((f, i) => (
                    <li key={i} className="leading-relaxed">
                      <strong>{f.feature}:</strong> {f.explanation}
                    </li>
                  ))}
                </ul>
              </div>

              <div>
                <span className="font-bold text-slate-900 block mb-1">Recommended Next Steps:</span>
                <ul className="space-y-1 pl-4 list-disc text-slate-600 leading-relaxed">
                  {aiSummary.explanation.next_steps.map((s, i) => (
                    <li key={i} className="leading-relaxed">{s}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* Section: Clinical Limitations & Legal Safety Note */}
        <div className="p-4 sm:p-5 rounded-xl sm:rounded-2xl bg-amber-50/60 border border-amber-200/80 text-xs text-amber-950 space-y-2">
          <div className="flex items-center gap-2 font-bold text-amber-900">
            <ShieldAlert className="w-4 h-4 text-amber-700 shrink-0" />
            <span>Clinical Safety Notice & Limitations</span>
          </div>
          <p className="leading-relaxed text-[11px] sm:text-xs">
            This screening report is generated by an automated clinical decision support prototype (ResNet18 + Texture Fusion). It does not provide a definitive diagnosis or replace examination by a physician. Important principles: (1) 6 mm is a heuristic clinical guideline, not an absolute diagnostic boundary. (2) Photographic differences (lighting, camera distance, angle) can simulate physical variation and do not confirm biological progression. (3) Machine learning classifiers can produce false positives and false negatives. A board-certified dermatologist should perform full in-person clinical dermoscopy and histological biopsy if indicated.
          </p>
        </div>

        {/* Document Footer */}
        <div className="pt-4 sm:pt-6 border-t border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-1.5 sm:gap-2 text-[10px] sm:text-[11px] text-slate-400">
          <div>Report generated by DermaAssist CDSS Prototype</div>
          <div>Page 1 of 1 • For clinical decision support only</div>
        </div>
      </div>
    </div>
  );
};
