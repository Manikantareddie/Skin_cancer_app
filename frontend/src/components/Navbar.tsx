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
      <div className="max-w-[1140px] mx-auto px-3 sm:px-4">
        {/* Top bar: Brand, Status & Diagnostics */}
        <div className="h-14 sm:h-16 flex items-center justify-between gap-2 sm:gap-4">
          {/* Brand / Logo */}
          <div
            onClick={() => onSelectStage('upload')}
            className="flex items-center gap-2 sm:gap-3 cursor-pointer select-none shrink-0"
          >
            <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-xl bg-teal-700 flex items-center justify-center text-white shadow-sm shadow-teal-700/20 shrink-0">
              <Stethoscope className="w-4 h-4 sm:w-5 sm:h-5" />
            </div>
            <div>
              <div className="flex items-center gap-1.5 sm:gap-2">
                <span className="font-extrabold text-slate-900 tracking-tight text-sm sm:text-base">
                  DermaAssist
                </span>
                <span className="text-[9px] sm:text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 bg-teal-50 text-teal-700 border border-teal-200/60 rounded-full">
                  CDSS
                </span>
              </div>
              <p className="text-[10px] sm:text-[11px] text-slate-400 hidden sm:block truncate">
                AI Skin Lesion Clinical Decision Support
              </p>
            </div>
          </div>

          {/* Desktop 4-Stage Workflow Navigation Pills (hidden on mobile, shown on md+) */}
          <nav className="hidden md:flex items-center gap-1 lg:gap-1.5 bg-slate-100/90 p-1 rounded-2xl border border-slate-200/70 text-xs">
            {/* Stage 1: Upload */}
            <button
              onClick={() => onSelectStage('upload')}
              className={`px-3 py-1.5 rounded-xl font-bold flex items-center gap-1.5 transition-all cursor-pointer min-h-[36px] ${
                currentStage === 'upload'
                  ? 'bg-white text-teal-800 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Upload className="w-3.5 h-3.5 shrink-0" />
              <span>1. Upload</span>
            </button>

            {/* Stage 2: Measurements & History */}
            <button
              onClick={() => canNavigateToMeasurements && onSelectStage('measurements')}
              disabled={!canNavigateToMeasurements}
              className={`px-3 py-1.5 rounded-xl font-bold flex items-center gap-1.5 transition-all min-h-[36px] ${
                currentStage === 'measurements'
                  ? 'bg-white text-teal-800 shadow-xs'
                  : canNavigateToMeasurements
                  ? 'text-slate-600 hover:text-slate-900 cursor-pointer'
                  : 'text-slate-400 opacity-50 cursor-not-allowed'
              }`}
            >
              <Ruler className="w-3.5 h-3.5 shrink-0" />
              <span>2. History & Scale</span>
            </button>

            {/* Stage 3: Analysis */}
            <button
              onClick={() => canNavigateToAnalysis && onSelectStage('analysis')}
              disabled={!canNavigateToAnalysis}
              className={`px-3 py-1.5 rounded-xl font-bold flex items-center gap-1.5 transition-all min-h-[36px] ${
                currentStage === 'analysis'
                  ? 'bg-white text-teal-800 shadow-xs'
                  : canNavigateToAnalysis
                  ? 'text-slate-600 hover:text-slate-900 cursor-pointer'
                  : 'text-slate-400 opacity-50 cursor-not-allowed'
              }`}
            >
              <Activity className="w-3.5 h-3.5 shrink-0" />
              <span>3. Analysis</span>
            </button>

            {/* Stage 4: Report */}
            <button
              onClick={() => canNavigateToReport && onSelectStage('report')}
              disabled={!canNavigateToReport}
              className={`px-3 py-1.5 rounded-xl font-bold flex items-center gap-1.5 transition-all min-h-[36px] ${
                currentStage === 'report'
                  ? 'bg-white text-teal-800 shadow-xs'
                  : canNavigateToReport
                  ? 'text-slate-600 hover:text-slate-900 cursor-pointer'
                  : 'text-slate-400 opacity-50 cursor-not-allowed'
              }`}
            >
              <FileText className="w-3.5 h-3.5 shrink-0" />
              <span>4. Report</span>
            </button>
          </nav>

          {/* Status & Diagnostics */}
          <div className="flex items-center gap-1.5 sm:gap-3 shrink-0">
            <div className="hidden lg:flex items-center gap-1.5 px-3 py-1 bg-slate-50 border border-slate-200/60 rounded-full text-xs text-slate-600 font-medium">
              <span className={`w-2 h-2 rounded-full ${isModelReady ? 'bg-emerald-500' : 'bg-amber-500'}`}></span>
              <span>{isModelReady ? 'Dual ResNet18 + Texture Ready' : 'Model Initializing'}</span>
            </div>

            {onShowDiagnostics && (
              <button
                onClick={onShowDiagnostics}
                className="flex items-center gap-1 text-xs font-semibold text-slate-500 hover:text-slate-800 p-1.5 sm:p-2 rounded-lg hover:bg-slate-100 transition-colors cursor-pointer min-h-[36px]"
                title="System Diagnostics"
              >
                <Info className="w-4 h-4" />
                <span className="hidden xl:inline">Diagnostics</span>
              </button>
            )}
          </div>
        </div>

        {/* Mobile Stage Navigation Row (visible on <md, touch-friendly, scrollable or wrap-free) */}
        <nav className="flex md:hidden items-center justify-between gap-1 pb-2 pt-0.5 overflow-x-auto no-scrollbar text-[11px]">
          <button
            onClick={() => onSelectStage('upload')}
            className={`flex-1 py-1.5 px-2 rounded-xl font-bold flex items-center justify-center gap-1 transition-all cursor-pointer min-h-[36px] shrink-0 ${
              currentStage === 'upload'
                ? 'bg-teal-700 text-white shadow-xs'
                : 'bg-slate-100 text-slate-600 hover:text-slate-900'
            }`}
          >
            <Upload className="w-3 h-3 shrink-0" />
            <span>Upload</span>
          </button>

          <button
            onClick={() => canNavigateToMeasurements && onSelectStage('measurements')}
            disabled={!canNavigateToMeasurements}
            className={`flex-1 py-1.5 px-2 rounded-xl font-bold flex items-center justify-center gap-1 transition-all min-h-[36px] shrink-0 ${
              currentStage === 'measurements'
                ? 'bg-teal-700 text-white shadow-xs'
                : canNavigateToMeasurements
                ? 'bg-slate-100 text-slate-600 hover:text-slate-900 cursor-pointer'
                : 'bg-slate-50 text-slate-400 opacity-50 cursor-not-allowed'
            }`}
          >
            <Ruler className="w-3 h-3 shrink-0" />
            <span>Scale</span>
          </button>

          <button
            onClick={() => canNavigateToAnalysis && onSelectStage('analysis')}
            disabled={!canNavigateToAnalysis}
            className={`flex-1 py-1.5 px-2 rounded-xl font-bold flex items-center justify-center gap-1 transition-all min-h-[36px] shrink-0 ${
              currentStage === 'analysis'
                ? 'bg-teal-700 text-white shadow-xs'
                : canNavigateToAnalysis
                ? 'bg-slate-100 text-slate-600 hover:text-slate-900 cursor-pointer'
                : 'bg-slate-50 text-slate-400 opacity-50 cursor-not-allowed'
            }`}
          >
            <Activity className="w-3 h-3 shrink-0" />
            <span>Analysis</span>
          </button>

          <button
            onClick={() => canNavigateToReport && onSelectStage('report')}
            disabled={!canNavigateToReport}
            className={`flex-1 py-1.5 px-2 rounded-xl font-bold flex items-center justify-center gap-1 transition-all min-h-[36px] shrink-0 ${
              currentStage === 'report'
                ? 'bg-teal-700 text-white shadow-xs'
                : canNavigateToReport
                ? 'bg-slate-100 text-slate-600 hover:text-slate-900 cursor-pointer'
                : 'bg-slate-50 text-slate-400 opacity-50 cursor-not-allowed'
            }`}
          >
            <FileText className="w-3 h-3 shrink-0" />
            <span>Report</span>
          </button>
        </nav>
      </div>
    </header>
  );
};
