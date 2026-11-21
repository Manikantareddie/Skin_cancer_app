import React, { useState, useEffect } from 'react';
import {
  Sparkles,
  RefreshCw,
  AlertCircle,
  HelpCircle,
  Eye,
  ShieldAlert,
  ArrowRightCircle,
  Cpu,
  CheckCircle2,
} from 'lucide-react';
import { generateAiSummary } from '../api/client';
import type { AIExplanationResponse, AnalysisResponse } from '../api/types';

interface AiSummaryCardProps {
  analysis: AnalysisResponse;
  initialSummary?: AIExplanationResponse | null;
  onSummaryLoaded?: (summary: AIExplanationResponse) => void;
}

export const AiSummaryCard: React.FC<AiSummaryCardProps> = ({
  analysis,
  initialSummary,
  onSummaryLoaded,
}) => {
  const [summaryData, setSummaryData] = useState<AIExplanationResponse | null>(initialSummary || null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSummary = async () => {
    if (!analysis.prediction || !analysis.abcde || !analysis.clinical_risk) return;
    setLoading(true);
    setError(null);
    try {
      const resp = await generateAiSummary({
        case_id: analysis.case_id,
        predicted_label: analysis.prediction.predicted_label,
        confidence_score: analysis.prediction.confidence_score,
        risk_level: analysis.clinical_risk.risk_level,
        abcd_results: analysis.abcde.raw_dictionary,
      });
      setSummaryData(resp);
      if (onSummaryLoaded) {
        onSummaryLoaded(resp);
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to generate AI educational explanation.');
    } finally {
      setLoading(false);
    }
  };

  // Automatically fetch on mount if not yet loaded
  useEffect(() => {
    if (!summaryData && !loading && !error) {
      fetchSummary();
    }
  }, [analysis.case_id]);

  const explanation = summaryData?.explanation;
  const isFallback = summaryData?.is_fallback || summaryData?.provider === 'deterministic_rules_engine';

  return (
    <div className="bg-white rounded-3xl border border-slate-200/90 shadow-xs p-6 md:p-8 space-y-6">
      {/* Section Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="p-1.5 rounded-lg bg-teal-50 text-teal-700">
              <Sparkles className="w-5 h-5" />
            </span>
            <h3 className="text-lg font-bold text-slate-900 tracking-tight">
              AI Clinical Explanation
            </h3>
          </div>
          <p className="text-xs text-slate-500">
            Synthesized interpretation of neural network activations and morphological features
          </p>
        </div>

        {/* Engine Status Badge & Refresh */}
        <div className="flex items-center gap-2 self-start sm:self-auto">
          {summaryData && (
            <div
              className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-semibold border ${
                !isFallback
                  ? 'bg-emerald-50 text-emerald-800 border-emerald-200/80'
                  : 'bg-slate-50 text-slate-700 border-slate-200'
              }`}
            >
              <Cpu className="w-3 h-3" />
              <span>{isFallback ? 'Deterministic Clinical Engine' : 'NVIDIA NIM Intelligence'}</span>
            </div>
          )}

          <button
            onClick={fetchSummary}
            disabled={loading}
            title="Regenerate explanation"
            className="p-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-500 hover:text-slate-800 transition-colors disabled:opacity-40 cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-teal-700' : ''}`} />
          </button>
        </div>
      </div>

      {/* Loading State */}
      {loading && !summaryData && (
        <div className="py-12 text-center space-y-3">
          <div className="inline-flex p-3 rounded-2xl bg-teal-50 text-teal-700 animate-pulse">
            <RefreshCw className="w-6 h-6 animate-spin" />
          </div>
          <div className="text-sm font-bold text-slate-800">
            Generating Structured AI Explanation...
          </div>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            Processing lesion descriptors and calculating clinical interpretations
          </p>
        </div>
      )}

      {/* Error State */}
      {error && !summaryData && (
        <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs space-y-2">
          <div className="flex items-center gap-2 font-bold text-rose-900">
            <AlertCircle className="w-4 h-4 text-rose-600" />
            Unable to connect to AI Explanation service
          </div>
          <p>{error}</p>
          <button
            onClick={fetchSummary}
            className="mt-1 text-xs font-bold text-teal-700 hover:underline cursor-pointer"
          >
            Try Again
          </button>
        </div>
      )}

      {/* Structured 4-Card Presentation */}
      {explanation && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Card 1: Understanding the Result */}
            <div className="p-5 rounded-2xl bg-slate-50/80 border border-slate-200/80 flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-2 text-teal-800 font-bold text-xs uppercase tracking-wider mb-2">
                  <HelpCircle className="w-4 h-4 text-teal-700" />
                  Understanding the Result
                </div>
                <p className="text-xs text-slate-700 leading-relaxed">
                  {explanation.result_explanation}
                </p>
              </div>
              <div className="mt-3 pt-3 border-t border-slate-200/60 text-[11px] text-slate-400">
                Classification reflects statistical pattern alignment from trained images.
              </div>
            </div>

            {/* Card 2: What the Model Observed */}
            <div className="p-5 rounded-2xl bg-teal-50/40 border border-teal-200/60 flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-2 text-teal-900 font-bold text-xs uppercase tracking-wider mb-2">
                  <Eye className="w-4 h-4 text-teal-700" />
                  What the Model Observed
                </div>
                <div className="space-y-2 text-xs text-slate-700">
                  {explanation.observed_features.map((item, idx) => (
                    <div key={idx} className="flex items-start gap-1.5">
                      <span className="font-semibold text-teal-950 shrink-0">• {item.feature}:</span>
                      <span className="text-slate-600">{item.explanation}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div className="mt-3 pt-3 border-t border-teal-200/50 text-[11px] text-teal-700/80">
                Ground-truth visual indicators extracted during preprocessing.
              </div>
            </div>

            {/* Card 3: Important Limitations */}
            <div className="p-5 rounded-2xl bg-amber-50/40 border border-amber-200/70 flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-2 text-amber-900 font-bold text-xs uppercase tracking-wider mb-2">
                  <ShieldAlert className="w-4 h-4 text-amber-700" />
                  Important Limitations
                </div>
                <ul className="space-y-1.5 text-xs text-slate-700">
                  {explanation.limitations.map((lim, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-amber-500 mt-1.5 shrink-0"></span>
                      <span>{lim}</span>
                    </li>
                  ))}
                </ul>
              </div>
              <div className="mt-3 pt-3 border-t border-amber-200/50 text-[11px] text-amber-800">
                Automated models are non-diagnostic decision-support aids.
              </div>
            </div>

            {/* Card 4: Suggested Next Steps */}
            <div className="p-5 rounded-2xl bg-indigo-50/40 border border-indigo-200/60 flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-2 text-indigo-900 font-bold text-xs uppercase tracking-wider mb-2">
                  <ArrowRightCircle className="w-4 h-4 text-indigo-700" />
                  Suggested Next Steps
                </div>
                <ul className="space-y-1.5 text-xs text-slate-700">
                  {explanation.next_steps.map((step, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <CheckCircle2 className="w-3.5 h-3.5 text-indigo-600 mt-0.5 shrink-0" />
                      <span>{step}</span>
                    </li>
                  ))}
                </ul>
              </div>
              <div className="mt-3 pt-3 border-t border-indigo-200/50 text-[11px] text-indigo-700">
                Professional in-person evaluation is recommended for peace of mind.
              </div>
            </div>
          </div>

          {/* Legal / Medical Safety Banner */}
          <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200/70 text-[11px] text-slate-500 flex items-start gap-2.5">
            <ShieldAlert className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
            <span className="leading-relaxed">
              <strong>Medical Notice:</strong> {summaryData?.disclaimer}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
