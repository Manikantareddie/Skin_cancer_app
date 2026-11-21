import React from 'react';
import { Stethoscope, Info, Upload, Activity, FileText, Ruler } from 'lucide-react';

export type Stage = 'upload' | 'measurements' | 'analysis' | 'report';

interface NavbarProps {
  currentStage: Stage;
  canNavigateToMeasurements: boolean;
  canNavigateToAnalysis: boolean;
  canNavigateToReport: boolean;
  onSelectStage: (stage: Stage) => void;
  onShowDiagnostics?: () => void;
  isModelReady?: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentStage,
  canNavigateToMeasurements,
  canNavigateToAnalysis,
  canNavigateToReport,
  onSelectStage,
  onShowDiagnostics,
  isModelReady = true,
}) => {
  return (
    <header className="bg-white border-b border-slate-200/80 sticky top-0 z-30 shadow-xs print:hidden">
      <div className="max-w-[1140px] mx-auto px-4 h-16 flex items-center justify-between gap-4">
        {/* Brand / Logo */}
        <div
          onClick={() => onSelectStage('upload')}
          className="flex items-center gap-3 cursor-pointer select-none"
        >
          <div className="w-10 h-10 rounded-xl bg-teal-700 flex items-center justify-center text-white shadow-sm shadow-teal-700/20">
            <Stethoscope className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-slate-900 tracking-tight text-base">DermaAssist</span>
              <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 bg-teal-50 text-teal-700 border border-teal-200/60 rounded-full">
                CDSS
              </span>
            </div>
            <p className="text-[11px] text-slate-400 hidden sm:block">AI Skin Lesion Clinical Decision Support</p>
          </div>
        </div>

        {/* 4-Stage Workflow Navigation Pills */}
        <div className="flex items-center gap-1 sm:gap-1.5 bg-slate-100/90 p-1 rounded-2xl border border-slate-200/70 text-xs">
          {/* Stage 1: Upload */}
          <button
            onClick={() => onSelectStage('upload')}
            className={`px-3 py-1.5 rounded-xl font-bold flex items-center gap-1.5 transition-all cursor-pointer ${
              currentStage === 'upload'
                ? 'bg-white text-teal-800 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Upload className="w-3.5 h-3.5" />
            <span className="hidden md:inline">1.</span>
            <span>Upload</span>
          </button>

          {/* Stage 2: Measurements & History */}
          <button
            onClick={() => canNavigateToMeasurements && onSelectStage('measurements')}
            disabled={!canNavigateToMeasurements}
            className={`px-3 py-1.5 rounded-xl font-bold flex items-center gap-1.5 transition-all ${
              currentStage === 'measurements'
                ? 'bg-white text-teal-800 shadow-xs'
                : canNavigateToMeasurements
                ? 'text-slate-600 hover:text-slate-900 cursor-pointer'
                : 'text-slate-400 opacity-50 cursor-not-allowed'
            }`}
          >
            <Ruler className="w-3.5 h-3.5" />
            <span className="hidden md:inline">2.</span>
            <span>History & Scale</span>
          </button>

          {/* Stage 3: Analysis */}
          <button
            onClick={() => canNavigateToAnalysis && onSelectStage('analysis')}
            disabled={!canNavigateToAnalysis}
            className={`px-3 py-1.5 rounded-xl font-bold flex items-center gap-1.5 transition-all ${
              currentStage === 'analysis'
                ? 'bg-white text-teal-800 shadow-xs'
                : canNavigateToAnalysis
                ? 'text-slate-600 hover:text-slate-900 cursor-pointer'
                : 'text-slate-400 opacity-50 cursor-not-allowed'
            }`}
          >
            <Activity className="w-3.5 h-3.5" />
            <span className="hidden md:inline">3.</span>
            <span>Analysis</span>
          </button>

          {/* Stage 4: Report */}
          <button
            onClick={() => canNavigateToReport && onSelectStage('report')}
            disabled={!canNavigateToReport}
            className={`px-3 py-1.5 rounded-xl font-bold flex items-center gap-1.5 transition-all ${
              currentStage === 'report'
                ? 'bg-white text-teal-800 shadow-xs'
                : canNavigateToReport
                ? 'text-slate-600 hover:text-slate-900 cursor-pointer'
                : 'text-slate-400 opacity-50 cursor-not-allowed'
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            <span className="hidden md:inline">4.</span>
            <span>Report</span>
          </button>
        </div>

        {/* Status & Diagnostics */}
        <div className="flex items-center gap-3">
          <div className="hidden lg:flex items-center gap-1.5 px-3 py-1 bg-slate-50 border border-slate-200/60 rounded-full text-xs text-slate-600 font-medium">
            <span className={`w-2 h-2 rounded-full ${isModelReady ? 'bg-emerald-500' : 'bg-amber-500'}`}></span>
            <span>{isModelReady ? 'Dual ResNet18 + Texture Ready' : 'Model Initializing'}</span>
          </div>

          {onShowDiagnostics && (
            <button
              onClick={onShowDiagnostics}
              className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 p-2 rounded-lg hover:bg-slate-100 transition-colors cursor-pointer"
              title="System Diagnostics"
            >
              <Info className="w-4 h-4" />
              <span className="hidden xl:inline">Diagnostics</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
};
