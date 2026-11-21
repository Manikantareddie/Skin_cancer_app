import React from 'react';
import { ShieldCheck, Info, Activity, Ruler, History } from 'lucide-react';
import type { ABCDEIndicators, ClinicalRiskResult } from '../api/types';

interface ABCDECardProps {
  abcde: ABCDEIndicators;
  clinicalRisk: ClinicalRiskResult;
}

export const ABCDECard: React.FC<ABCDECardProps> = ({ abcde, clinicalRisk }) => {
  const getRiskBadge = (level: string) => {
    switch (level) {
      case 'HIGH':
        return 'bg-rose-50 text-rose-800 border-rose-200';
      case 'MODERATE':
        return 'bg-amber-50 text-amber-800 border-amber-200';
      case 'LOW':
      default:
        return 'bg-emerald-50 text-emerald-800 border-emerald-200';
    }
  };

  const diameter = abcde.diameter;
  const evolution = abcde.evolution;

  return (
    <div className="bg-white rounded-3xl border border-slate-200/90 shadow-xs p-6 md:p-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-100">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-1.5 rounded-lg bg-teal-50 text-teal-700">
              <Activity className="w-5 h-5" />
            </span>
            <h3 className="text-lg font-bold text-slate-900 tracking-tight">
              Lesion Morphological Characteristics (ABCDE)
            </h3>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Standard clinical criteria evaluated via computer vision, calibrated scale, and longitudinal registration
          </p>
        </div>
        <span
          className={`px-3 py-1 rounded-full text-xs font-bold border uppercase tracking-wider self-start sm:self-auto ${getRiskBadge(
            clinicalRisk.risk_level
          )}`}
        >
          {clinicalRisk.risk_level} Risk Category
        </span>
      </div>

      {/* Grid of ABCDE Observations */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* A - Asymmetry */}
        <div className="p-4 rounded-2xl bg-slate-50/80 border border-slate-200/70 flex flex-col justify-between">
          <div>
            <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
              A • Asymmetry
            </div>
            <div className="text-sm font-bold text-slate-800 mt-1">{abcde.asymmetry_label}</div>
            <p className="text-xs text-slate-600 mt-2 leading-relaxed">
              Contour symmetry index: <span className="font-mono font-semibold text-slate-800">{abcde.asymmetry_score.toFixed(2)}</span>.
              Calculated across primary and secondary orthogonal axes.
            </p>
          </div>
        </div>

        {/* B - Border */}
        <div className="p-4 rounded-2xl bg-slate-50/80 border border-slate-200/70 flex flex-col justify-between">
          <div>
            <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
              B • Border Regularity
            </div>
            <div className="text-sm font-bold text-slate-800 mt-1">{abcde.border_label}</div>
            <p className="text-xs text-slate-600 mt-2 leading-relaxed">
              Perimeter compactness: <span className="font-mono font-semibold text-slate-800">{abcde.border_score.toFixed(2)}</span>.
              Evaluates border sharpness and margin notched irregularity.
            </p>
          </div>
        </div>

        {/* C - Color */}
        <div className="p-4 rounded-2xl bg-slate-50/80 border border-slate-200/70 flex flex-col justify-between">
          <div>
            <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
              C • Color Variation
            </div>
            <div className="text-sm font-bold text-slate-800 mt-1">{abcde.color_label}</div>
            <p className="text-xs text-slate-600 mt-2 leading-relaxed">
              Clustering identified <span className="font-mono font-semibold text-slate-800">{abcde.color_count}</span> dominant color tones
              (e.g., shades of brown, tan, dark pigment, or erythema).
            </p>
          </div>
        </div>

        {/* D - Diameter (Fully Functional & Provenance-Aware) */}
        <div className="p-4 rounded-2xl bg-slate-50/80 border border-slate-200/70 flex flex-col justify-between sm:col-span-1 lg:col-span-1">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1">
                <Ruler className="w-3.5 h-3.5 text-teal-700" />
                D • Physical Diameter
              </span>
              <span
                className={`text-[9px] font-black px-2 py-0.5 rounded-full uppercase tracking-wider ${
                  diameter?.status === 'MEASURED'
                    ? 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                    : diameter?.status === 'USER_REPORTED'
                    ? 'bg-blue-100 text-blue-800 border border-blue-200'
                    : 'bg-amber-100 text-amber-800 border border-amber-200'
                }`}
              >
                {diameter?.status || 'UNAVAILABLE'}
              </span>
            </div>

            {diameter?.status === 'MEASURED' && diameter.longest_diameter_mm ? (
              <div className="mt-1 space-y-1">
                <div className="text-base font-black text-slate-900">
                  {diameter.longest_diameter_mm.toFixed(1)} mm
                </div>
                <div className="text-[11px] text-slate-600 leading-tight">
                  Longest Feret caliper distance ({diameter.pixels_per_mm} px/mm calibrated scale).
                </div>
                <div className="text-[10px] text-slate-500 pt-1">
                  6 mm is a heuristic reference, not a definitive diagnostic threshold.
                </div>
              </div>
            ) : diameter?.status === 'USER_REPORTED' && diameter.longest_diameter_mm ? (
              <div className="mt-1 space-y-1">
                <div className="text-base font-black text-slate-900">
                  {diameter.longest_diameter_mm.toFixed(1)} mm
                </div>
                <div className="text-[11px] text-slate-600 leading-tight">
                  Manual measurement reported by patient or clinician.
                </div>
              </div>
            ) : (
              <div className="mt-1 space-y-1">
                <div className="text-xs font-bold text-amber-900">
                  Physical diameter cannot be determined from this image
                </div>
                <div className="text-[11px] text-amber-800/80 flex items-start gap-1">
                  <Info className="w-3 h-3 shrink-0 mt-0.5" />
                  <span>No in-frame calibrated millimeter ruler or patient report provided.</span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* E - Evolution (Fully Functional & Longitudinal-Aware) */}
        <div className="p-4 rounded-2xl bg-slate-50/80 border border-slate-200/70 flex flex-col justify-between sm:col-span-2 lg:col-span-2">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1">
                <History className="w-3.5 h-3.5 text-teal-700" />
                E • Longitudinal Evolution & History
              </span>
              <span
                className={`text-[9px] font-black px-2 py-0.5 rounded-full uppercase tracking-wider ${
                  evolution?.status === 'OBSERVED'
                    ? 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                    : evolution?.status === 'REPORTED'
                    ? 'bg-blue-100 text-blue-800 border border-blue-200'
                    : evolution?.status === 'UNCERTAIN'
                    ? 'bg-amber-100 text-amber-800 border border-amber-200'
                    : 'bg-slate-200 text-slate-700'
                }`}
              >
                {evolution?.status || 'NOT_ASSESSABLE'}
              </span>
            </div>

            {evolution?.status === 'OBSERVED' ? (
              <div className="mt-1 space-y-1">
                <div className="text-sm font-bold text-slate-900">
                  Observed Apparent Area Change:{' '}
                  <span className="text-teal-800">
                    {evolution.area_change_percent !== null && evolution.area_change_percent !== undefined
                      ? `${evolution.area_change_percent > 0 ? '+' : ''}${evolution.area_change_percent}%`
                      : 'Assessed'}
                  </span>{' '}
                  <span className="text-xs text-slate-500 font-normal">
                    ({evolution.time_interval_display || 'Sequential photos'}, {evolution.comparability} comparability)
                  </span>
                </div>
                {evolution.technical_confounders.confounding_disclosures.length > 0 && (
                  <div className="text-[11px] text-amber-800 pt-0.5">
                    Note: {evolution.technical_confounders.confounding_disclosures.join('; ')}
                  </div>
                )}
              </div>
            ) : evolution?.status === 'REPORTED' ? (
              <div className="mt-1 space-y-1">
                <div className="text-sm font-bold text-slate-900">
                  Patient-Reported Historical Changes Documented
                </div>
                <div className="text-[11px] text-slate-600">
                  {evolution.clinical_summary}
                </div>
              </div>
            ) : evolution?.status === 'UNCERTAIN' ? (
              <div className="mt-1 space-y-1">
                <div className="text-sm font-bold text-amber-900">
                  Longitudinal Comparison Uncertain
                </div>
                <div className="text-[11px] text-amber-800">
                  Camera angle, lighting, or focus differences prevent objective biological confirmation.
                </div>
              </div>
            ) : (
              <div className="mt-1 space-y-1">
                <div className="text-xs font-bold text-slate-700">
                  Not assessable — requires previous images or clinical history
                </div>
                <div className="text-[11px] text-slate-500">
                  Single static photographic snapshot; longitudinal evolution over time cannot be determined.
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Morphological Summary Findings */}
      <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200/80">
        <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2 flex items-center gap-1.5">
          <ShieldCheck className="w-4 h-4 text-teal-700" />
          Morphological Finding Summary:
        </h4>
        {clinicalRisk.risk_reasons.length > 0 ? (
          <ul className="space-y-1 text-xs text-slate-600 pl-4 list-disc">
            {clinicalRisk.risk_reasons.map((reason, idx) => (
              <li key={idx} className="leading-relaxed">
                {reason}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-xs text-slate-500">
            No high-risk morphological markers flagged by the rule engine.
          </p>
        )}
      </div>
    </div>
  );
};
