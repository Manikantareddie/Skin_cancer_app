import React, { useState } from 'react';
import { Eye, Sliders, Layers, HelpCircle, Columns, Maximize2, X } from 'lucide-react';

interface GradCamViewerProps {
  originalImageUrl: string;
  heatmapBase64?: string;
}

export const GradCamViewer: React.FC<GradCamViewerProps> = ({ originalImageUrl, heatmapBase64 }) => {
  const [opacity, setOpacity] = useState<number>(70);
  const [viewMode, setViewMode] = useState<'overlay' | 'side-by-side'>('overlay');
  const [isZoomed, setIsZoomed] = useState<boolean>(false);

  return (
    <div className="bg-white rounded-2xl sm:rounded-3xl border border-slate-200/90 shadow-xs p-4 sm:p-6 md:p-8 space-y-4 sm:space-y-5">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 sm:gap-4 pb-3 sm:pb-4 border-b border-slate-100">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-1.5 rounded-lg bg-teal-50 text-teal-700 shrink-0">
              <Eye className="w-4 h-4 sm:w-5 sm:h-5" />
            </span>
            <h3 className="text-base sm:text-lg font-bold text-slate-900 tracking-tight">
              Visual Analysis & Grad-CAM Attention
            </h3>
          </div>
          <p className="text-xs text-slate-500 mt-1 leading-relaxed">
            Visual explanation revealing image regions that drove the model's neural activations
          </p>
        </div>

        {/* View Mode Toggle & Zoom Button */}
        <div className="flex items-center gap-2 self-start sm:self-auto shrink-0">
          <div className="inline-flex rounded-xl bg-slate-100 p-1 border border-slate-200/60 text-xs">
            <button
              onClick={() => setViewMode('overlay')}
              className={`px-2.5 sm:px-3 py-1.5 rounded-lg font-semibold flex items-center gap-1.5 transition-all cursor-pointer min-h-[32px] ${
                viewMode === 'overlay'
                  ? 'bg-white text-teal-800 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
              <span>Overlay</span>
            </button>
            <button
              onClick={() => setViewMode('side-by-side')}
              className={`px-2.5 sm:px-3 py-1.5 rounded-lg font-semibold flex items-center gap-1.5 transition-all cursor-pointer min-h-[32px] ${
                viewMode === 'side-by-side'
                  ? 'bg-white text-teal-800 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Columns className="w-3.5 h-3.5" />
              <span>Side-by-Side</span>
            </button>
          </div>

          <button
            onClick={() => setIsZoomed(true)}
            className="p-2 rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-600 hover:text-slate-900 transition-colors cursor-pointer min-h-[36px] min-w-[36px] flex items-center justify-center"
            title="Enlarge inspection view"
            aria-label="Enlarge inspection view"
          >
            <Maximize2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {viewMode === 'overlay' ? (
        /* Overlay Mode with Opacity Slider */
        <div className="space-y-3 sm:space-y-4">
          <div className="relative rounded-xl sm:rounded-2xl overflow-hidden bg-slate-950/5 border border-slate-200 flex items-center justify-center min-h-[220px] max-h-[320px] sm:max-h-[400px] md:max-h-[460px] p-2">
            {/* Base layer: Original image */}
            <img
              src={originalImageUrl}
              alt="Original lesion"
              className="max-h-[300px] sm:max-h-[380px] md:max-h-[440px] w-auto max-w-full object-contain rounded-xl select-none"
            />
            {/* Top layer: Heatmap with dynamic opacity */}
            {heatmapBase64 && (
              <img
                src={heatmapBase64}
                alt="Grad-CAM activation overlay"
                style={{ opacity: opacity / 100 }}
                className="absolute inset-0 m-auto max-h-[300px] sm:max-h-[380px] md:max-h-[440px] w-auto max-w-full object-contain rounded-xl pointer-events-none transition-opacity duration-75 select-none"
              />
            )}
          </div>

          {/* Interactive Opacity Slider */}
          {heatmapBase64 && (
            <div className="bg-slate-50 rounded-xl sm:rounded-2xl p-3 sm:p-3.5 border border-slate-200/80 flex flex-col sm:flex-row items-stretch sm:items-center gap-2 sm:gap-4">
              <div className="flex items-center justify-between sm:justify-start gap-2 text-xs font-bold text-slate-700 shrink-0">
                <div className="flex items-center gap-1.5">
                  <Sliders className="w-4 h-4 text-teal-700" />
                  <span>Heatmap Opacity:</span>
                </div>
                <span className="sm:hidden font-mono font-bold text-teal-800">{opacity}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="100"
                value={opacity}
                onChange={(e) => setOpacity(Number(e.target.value))}
                className="w-full accent-teal-700 cursor-pointer h-2.5 sm:h-2 bg-slate-200 rounded-lg touch-none"
              />
              <span className="hidden sm:inline text-xs font-mono font-bold text-slate-700 w-12 text-right shrink-0">{opacity}%</span>
            </div>
          )}
        </div>
      ) : (
        /* Side by Side Mode */
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 sm:gap-4">
          <div className="space-y-1.5">
            <div className="text-[11px] sm:text-xs font-bold text-slate-700 uppercase tracking-wider">
              Original Dermatological Image
            </div>
            <div className="rounded-xl sm:rounded-2xl overflow-hidden bg-slate-50 border border-slate-200 flex items-center justify-center h-[220px] sm:h-[260px] md:h-[300px] p-2">
              <img
                src={originalImageUrl}
                alt="Original Lesion Photograph"
                className="max-h-full max-w-full object-contain rounded-xl"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <div className="text-[11px] sm:text-xs font-bold text-slate-700 uppercase tracking-wider">
              Grad-CAM Activation Heatmap
            </div>
            <div className="rounded-xl sm:rounded-2xl overflow-hidden bg-slate-50 border border-slate-200 flex items-center justify-center h-[220px] sm:h-[260px] md:h-[300px] p-2">
              {heatmapBase64 ? (
                <img
                  src={heatmapBase64}
                  alt="Grad-CAM Activation"
                  className="max-h-full max-w-full object-contain rounded-xl"
                />
              ) : (
                <div className="text-xs text-slate-400">Heatmap unavailable</div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Visual Attention Legend & Scientific Boundary Disclaimer */}
      <div className="pt-3 sm:pt-4 border-t border-slate-100 flex flex-col md:flex-row md:items-center justify-between gap-2.5 sm:gap-3 text-xs text-slate-500">
        <div className="flex flex-wrap items-center gap-1.5 sm:gap-2">
          <span className="font-semibold text-slate-700 text-[11px] sm:text-xs">Model Focus:</span>
          <div className="flex items-center gap-1.5 font-medium text-[10px] sm:text-[11px]">
            <span className="inline-block w-2.5 h-2.5 rounded-full bg-red-500 shadow-xs"></span>
            <span>High Activation</span>
            <span className="inline-block w-2.5 h-2.5 rounded-full bg-yellow-400 ml-1.5 shadow-xs"></span>
            <span>Moderate</span>
            <span className="inline-block w-2.5 h-2.5 rounded-full bg-blue-500 ml-1.5 shadow-xs"></span>
            <span>Baseline</span>
          </div>
        </div>

        <div className="text-[10px] sm:text-[11px] text-slate-500 flex items-start gap-1.5 max-w-md">
          <HelpCircle className="w-3.5 h-3.5 text-teal-700 shrink-0 mt-0.5" />
          <span>
            <strong>Note:</strong> Heatmap highlights neural network focus areas; it is <em>not</em> an anatomical tumor border or surgical margin.
          </span>
        </div>
      </div>

      {/* Zoom / Enlarge Modal */}
      {isZoomed && (
        <div className="fixed inset-0 z-50 bg-slate-950/70 backdrop-blur-xs flex items-center justify-center p-3 sm:p-4">
          <div className="bg-white rounded-2xl sm:rounded-3xl max-w-4xl w-full p-4 sm:p-6 shadow-2xl border border-slate-200 space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="font-bold text-slate-900 text-xs sm:text-sm flex items-center gap-2">
                <Maximize2 className="w-4 h-4 text-teal-700" />
                <span>High-Resolution Visual Inspection</span>
              </div>
              <button
                onClick={() => setIsZoomed(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-800 hover:bg-slate-100 cursor-pointer min-h-[36px] min-w-[36px] flex items-center justify-center"
                aria-label="Close modal"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 sm:gap-4 p-1">
              <div className="space-y-1 text-center">
                <div className="text-[11px] sm:text-xs font-semibold text-slate-600">Original Photograph</div>
                <div className="rounded-xl sm:rounded-2xl border border-slate-200 bg-slate-50 p-2 flex items-center justify-center min-h-[220px] sm:min-h-[320px]">
                  <img
                    src={originalImageUrl}
                    alt="Original Enlarged"
                    className="max-h-[360px] w-auto max-w-full object-contain rounded-xl"
                  />
                </div>
              </div>

              <div className="space-y-1 text-center">
                <div className="text-[11px] sm:text-xs font-semibold text-slate-600">Grad-CAM Activation Heatmap</div>
                <div className="rounded-xl sm:rounded-2xl border border-slate-200 bg-slate-50 p-2 flex items-center justify-center min-h-[220px] sm:min-h-[320px]">
                  {heatmapBase64 ? (
                    <img
                      src={heatmapBase64}
                      alt="Grad-CAM Enlarged"
                      className="max-h-[360px] w-auto max-w-full object-contain rounded-xl"
                    />
                  ) : (
                    <div className="text-xs text-slate-400">Heatmap unavailable</div>
                  )}
                </div>
              </div>
            </div>

            <div className="text-right pt-2">
              <button
                onClick={() => setIsZoomed(false)}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-bold rounded-xl cursor-pointer min-h-[36px]"
              >
                Close View
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
