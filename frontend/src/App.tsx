import React, { useState } from 'react';
import { Navbar, Stage } from './components/Navbar';
import { ImageUploader } from './components/ImageUploader';
import { MeasurementsHistoryStage } from './components/MeasurementsHistoryStage';
import { ValidationAlert } from './components/ValidationAlert';
import { ResultsWorkspace } from './components/ResultsWorkspace';
import { ReportStage } from './components/ReportStage';
import { ApiTestCard } from './components/ApiTestCard';
import { analyzeImage } from './api/client';
import type {
  AIExplanationResponse,
  AnalysisResponse,
  DiameterAssessment,
  EvolutionAssessment,
  PatientReportedChanges,
} from './api/types';
import { AlertCircle, X } from 'lucide-react';

export const App: React.FC = () => {
  const [stage, setStage] = useState<Stage>('upload');
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [aiSummary, setAiSummary] = useState<AIExplanationResponse | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [globalError, setGlobalError] = useState<string | null>(null);
  const [showDiagnostics, setShowDiagnostics] = useState(false);

  // When user uploads file on Stage 1
  const handleUploadSelect = (file: File) => {
    setSelectedFile(file);
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
    setGlobalError(null);
    setAnalysis(null);
    setAiSummary(null);
    setStage('measurements');
  };

  // When user proceeds from Measurements & History Stage to Screening Analysis
  const handleProceedFromMeasurements = async (data: {
    baselineFile?: File | null;
    baselineDate?: string | null;
    followupDate?: string | null;
    manualDiameterMm?: number | null;
    calibrationPoints?: { p1: { x: number; y: number }; p2: { x: number; y: number }; physicalMm: number } | null;
    diameterAssessment?: DiameterAssessment | null;
    evolutionAssessment?: EvolutionAssessment | null;
    patientReportedChanges?: PatientReportedChanges | null;
  }) => {
    if (!selectedFile) return;

    setIsLoading(true);
    setGlobalError(null);

    try {
      const result = await analyzeImage({
        file: selectedFile,
        baselineFile: data.baselineFile,
        baselineDate: data.baselineDate,
        followupDate: data.followupDate,
        manualDiameterMm: data.manualDiameterMm,
        p1: data.calibrationPoints?.p1,
        p2: data.calibrationPoints?.p2,
        physicalDistanceMm: data.calibrationPoints?.physicalMm,
        patientReportedChanges: data.patientReportedChanges,
      });

      setAnalysis(result);

      if (result.validation.is_valid) {
        setStage('analysis');
      } else {
        // Validation gate rejection
        setStage('upload');
      }
    } catch (err: any) {
      setGlobalError(err?.message || 'Failed to analyze lesion. Please ensure the backend is running.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setAnalysis(null);
    setAiSummary(null);
    setSelectedFile(null);
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
      setPreviewUrl(null);
    }
    setGlobalError(null);
    setStage('upload');
  };

  const canNavigateToMeasurements = Boolean(selectedFile);
  const canNavigateToAnalysis = Boolean(analysis && analysis.validation.is_valid);
  const canNavigateToReport = Boolean(analysis && analysis.validation.is_valid);

  return (
    <div className="min-h-screen bg-[#F8FAFC] text-slate-800 flex flex-col font-sans antialiased selection:bg-teal-100 selection:text-teal-900 overflow-x-hidden">
      {/* Top Clinical Navigation with 4 Stages */}
      <Navbar
        currentStage={stage}
        canNavigateToMeasurements={canNavigateToMeasurements}
        canNavigateToAnalysis={canNavigateToAnalysis}
        canNavigateToReport={canNavigateToReport}
        onSelectStage={(newStage) => setStage(newStage)}
        onShowDiagnostics={() => setShowDiagnostics(true)}
      />

      {/* Main Screening Work Area (Max width 1140px centered, responsive padding) */}
      <main className="flex-1 max-w-[1140px] w-full mx-auto px-3 sm:px-4 md:px-6 py-4 sm:py-6 md:py-10">
        {/* Global Error Banner */}
        {globalError && (
          <div className="max-w-2xl mx-auto mb-4 sm:mb-6 p-3 sm:p-4 bg-rose-50 border border-rose-200 rounded-xl sm:rounded-2xl text-rose-800 text-xs flex items-start justify-between gap-2.5 shadow-xs">
            <div className="flex items-center gap-2 font-medium">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
              <span className="leading-relaxed">{globalError}</span>
            </div>
            <button
              onClick={() => setGlobalError(null)}
              className="text-rose-500 hover:text-rose-800 p-1 cursor-pointer shrink-0"
              aria-label="Close error banner"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        )}

        {/* Stage 1: Upload */}
        {stage === 'upload' && (
          <>
            {analysis && !analysis.validation.is_valid ? (
              <ValidationAlert validation={analysis.validation} onReset={handleReset} />
            ) : (
              <ImageUploader onAnalyze={handleUploadSelect} isLoading={isLoading} />
            )}
          </>
        )}

        {/* Stage 2: Dedicated Measurements & History */}
        {stage === 'measurements' && selectedFile && previewUrl && (
          <MeasurementsHistoryStage
            primaryFile={selectedFile}
            primaryImageUrl={previewUrl}
            onProceedToAnalyze={handleProceedFromMeasurements}
            onBackToUpload={() => setStage('upload')}
          />
        )}

        {/* Stage 3: Analysis Workspace */}
        {stage === 'analysis' && analysis && analysis.validation.is_valid && (
          <ResultsWorkspace
            analysis={analysis}
            originalFile={selectedFile!}
            originalImageUrl={previewUrl!}
            onReset={handleReset}
            onNavigateToReport={() => setStage('report')}
            aiSummary={aiSummary}
            onSummaryLoaded={(summary) => setAiSummary(summary)}
          />
        )}

        {/* Stage 4: Report Preview & PDF Export */}
        {stage === 'report' && analysis && analysis.validation.is_valid && (
          <ReportStage
            analysis={analysis}
            originalFile={selectedFile!}
            originalImageUrl={previewUrl!}
            aiSummary={aiSummary}
            onBackToAnalysis={() => setStage('analysis')}
            onReset={handleReset}
          />
        )}
      </main>

      {/* Diagnostics Modal for developers */}
      {showDiagnostics && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-3 sm:p-4">
          <div className="bg-white rounded-2xl sm:rounded-3xl max-w-2xl w-full p-4 sm:p-6 shadow-2xl border border-slate-200 relative max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
              <h3 className="text-sm font-bold text-slate-900">Developer Diagnostics</h3>
              <button
                onClick={() => setShowDiagnostics(false)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 cursor-pointer min-h-[36px] min-w-[36px] flex items-center justify-center"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <ApiTestCard />
            <div className="mt-4 text-right">
              <button
                onClick={() => setShowDiagnostics(false)}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-xl cursor-pointer min-h-[36px]"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Document/App Footer */}
      <footer className="print:hidden border-t border-slate-200/80 bg-white py-4 sm:py-6 mt-auto">
        <div className="max-w-[1140px] mx-auto px-3 sm:px-4 flex flex-col sm:flex-row items-center justify-between gap-2 sm:gap-3 text-center sm:text-left text-xs text-slate-400">
          <div>
            AI Skin Cancer Detection & CDSS • Multimodal ResNet-18 Texture Fusion
          </div>
          <div className="text-[10px] sm:text-[11px] text-slate-400">
            For educational clinical screening decision support only. Not a medical diagnosis.
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;
