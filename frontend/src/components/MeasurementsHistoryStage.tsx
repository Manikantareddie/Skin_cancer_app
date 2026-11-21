import React, { useState, useRef, useEffect } from 'react';
import {
  Ruler,
  History,
  ArrowRight,
  ArrowLeft,
  AlertCircle,
  HelpCircle,
  RefreshCw,
  Upload,
  Calendar,
  Layers,
  ShieldAlert,
  Info,
} from 'lucide-react';
import type {
  DiameterAssessment,
  EvolutionAssessment,
  PatientReportedChanges,
} from '../api/types';
import { calibrateRuler, compareEvolution } from '../api/client';

interface MeasurementsHistoryStageProps {
  primaryFile: File;
  primaryImageUrl: string;
  onProceedToAnalyze: (data: {
    baselineFile?: File | null;
    baselineDate?: string | null;
    followupDate?: string | null;
    manualDiameterMm?: number | null;
    calibrationPoints?: { p1: { x: number; y: number }; p2: { x: number; y: number }; physicalMm: number } | null;
    diameterAssessment?: DiameterAssessment | null;
    evolutionAssessment?: EvolutionAssessment | null;
    patientReportedChanges?: PatientReportedChanges | null;
  }) => void;
  onBackToUpload: () => void;
}

export const MeasurementsHistoryStage: React.FC<MeasurementsHistoryStageProps> = ({
  primaryFile,
  primaryImageUrl,
  onProceedToAnalyze,
  onBackToUpload,
}) => {
  // Tab state: 'diameter' | 'evolution'
  const [activeTab, setActiveTab] = useState<'diameter' | 'evolution'>('diameter');

  // --- Diameter State ---
  const [diameterMode, setDiameterMode] = useState<'ruler' | 'manual' | 'none'>('ruler');
  const [manualDiameter, setManualDiameter] = useState<string>('');
  const [physicalDistanceMm, setPhysicalDistanceMm] = useState<number>(10.0);
  const [point1, setPoint1] = useState<{ x: number; y: number } | null>(null);
  const [point2, setPoint2] = useState<{ x: number; y: number } | null>(null);
  const [calibrating, setCalibrating] = useState<boolean>(false);
  const [calibrationError, setCalibrationError] = useState<string | null>(null);
  const [diameterResult, setDiameterResult] = useState<DiameterAssessment | null>(null);

  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [imageLoaded, setImageLoaded] = useState(false);
  const imgRef = useRef<HTMLImageElement | null>(null);

  // --- Evolution State ---
  const [baselineFile, setBaselineFile] = useState<File | null>(null);
  const [baselinePreviewUrl, setBaselinePreviewUrl] = useState<string | null>(null);
  const [baselineDate, setBaselineDate] = useState<string>('');
  const [followupDate, setFollowupDate] = useState<string>(new Date().toISOString().split('T')[0]);
  const [comparing, setComparing] = useState<boolean>(false);
  const [evolutionError, setEvolutionError] = useState<string | null>(null);
  const [evolutionResult, setEvolutionResult] = useState<EvolutionAssessment | null>(null);

  // Patient symptoms
  const [symptoms, setSymptoms] = useState<PatientReportedChanges>({
    size_change: false,
    color_change: false,
    shape_change: false,
    itching: false,
    pain: false,
    bleeding: false,
    crusting_or_oozing: false,
    patient_notes: '',
  });

  // Load image onto canvas for 2-point ruler calibration
  useEffect(() => {
    const img = new Image();
    img.src = primaryImageUrl;
    img.onload = () => {
      imgRef.current = img;
      setImageLoaded(true);
      drawCanvas();
    };
  }, [primaryImageUrl]);

  const drawCanvas = () => {
    const canvas = canvasRef.current;
    const img = imgRef.current;
    if (!canvas || !img) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    canvas.width = img.naturalWidth || 600;
    canvas.height = img.naturalHeight || 600;

    // Draw background image
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

    // Draw calibration points and line
    if (point1) {
      ctx.fillStyle = '#0F766E';
      ctx.strokeStyle = '#FFFFFF';
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.arc(point1.x, point1.y, 8, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();

      ctx.fillStyle = '#FFFFFF';
      ctx.font = 'bold 14px sans-serif';
      ctx.fillText('1', point1.x + 12, point1.y + 5);
    }

    if (point2) {
      ctx.fillStyle = '#0F766E';
      ctx.strokeStyle = '#FFFFFF';
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.arc(point2.x, point2.y, 8, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();

      ctx.fillStyle = '#FFFFFF';
      ctx.font = 'bold 14px sans-serif';
      ctx.fillText('2', point2.x + 12, point2.y + 5);
    }

    if (point1 && point2) {
      ctx.strokeStyle = '#0F766E';
      ctx.lineWidth = 3;
      ctx.setLineDash([6, 6]);
      ctx.beginPath();
      ctx.moveTo(point1.x, point1.y);
      ctx.lineTo(point2.x, point2.y);
      ctx.stroke();
      ctx.setLineDash([]);
    }
  };

  useEffect(() => {
    if (imageLoaded) {
      drawCanvas();
    }
  }, [point1, point2, imageLoaded]);

  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;

    const clickX = (e.clientX - rect.left) * scaleX;
    const clickY = (e.clientY - rect.top) * scaleY;

    if (!point1 || (point1 && point2)) {
      setPoint1({ x: clickX, y: clickY });
      setPoint2(null);
      setDiameterResult(null);
    } else {
      setPoint2({ x: clickX, y: clickY });
    }
  };

  const handleResetPoints = () => {
    setPoint1(null);
    setPoint2(null);
    setDiameterResult(null);
    setCalibrationError(null);
    drawCanvas();
  };

  const handleApplyRulerCalibration = async () => {
    if (!point1 || !point2) {
      setCalibrationError('Please click two points along the ruler scale on the photo.');
      return;
    }
    setCalibrating(true);
    setCalibrationError(null);
    try {
      const res = await calibrateRuler(primaryFile, point1, point2, physicalDistanceMm);
      setDiameterResult(res);
    } catch (err: any) {
      setCalibrationError(err?.message || 'Ruler calibration failed.');
    } finally {
      setCalibrating(false);
    }
  };

  // Evolution Baseline Upload
  const handleBaselineFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setBaselineFile(file);
      setBaselinePreviewUrl(URL.createObjectURL(file));
      setEvolutionResult(null);
      setEvolutionError(null);
    }
  };

  const handleRunEvolutionComparison = async () => {
    setComparing(true);
    setEvolutionError(null);
    try {
      const res = await compareEvolution(
        primaryFile,
        baselineFile,
        baselineDate || undefined,
        followupDate || undefined,
        symptoms,
      );
      setEvolutionResult(res);
    } catch (err: any) {
      setEvolutionError(err?.message || 'Evolution comparison failed.');
    } finally {
      setComparing(false);
    }
  };

  const handleProceed = () => {
    let finalManualMm: number | null = null;
    if (diameterMode === 'manual' && manualDiameter) {
      const parsed = parseFloat(manualDiameter);
      if (!isNaN(parsed) && parsed > 0) {
        finalManualMm = parsed;
      }
    }

    const calibPayload =
      diameterMode === 'ruler' && point1 && point2 && diameterResult?.ruler_calibration
        ? { p1: point1, p2: point2, physicalMm: physicalDistanceMm }
        : null;

    onProceedToAnalyze({
      baselineFile,
      baselineDate: baselineDate || null,
      followupDate: followupDate || null,
      manualDiameterMm: finalManualMm,
      calibrationPoints: calibPayload,
      diameterAssessment: diameterResult,
      evolutionAssessment: evolutionResult,
      patientReportedChanges: symptoms,
    });
  };

  return (
    <div className="max-w-[1140px] w-full mx-auto space-y-6 pb-24">
      {/* Top Clinical Header & Stage Navigation */}
      <div className="bg-white rounded-3xl border border-slate-200/90 shadow-xs p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-1.5 rounded-xl bg-teal-50 text-teal-700 font-bold">
              <Ruler className="w-5 h-5" />
            </span>
            <h2 className="text-xl font-black text-slate-900 tracking-tight">
              Optional Measurements & Longitudinal History
            </h2>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Provide ruler scale calibration or an earlier photo of this lesion to enrich criteria D and E.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={onBackToUpload}
            className="px-4 py-2 rounded-xl text-xs font-bold text-slate-700 hover:text-slate-900 bg-slate-50 hover:bg-slate-100 border border-slate-200 transition-colors flex items-center gap-1.5 cursor-pointer"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Back to Upload
          </button>
          <button
            onClick={handleProceed}
            className="px-5 py-2 rounded-xl text-xs font-bold text-white bg-teal-700 hover:bg-teal-800 shadow-sm transition-all flex items-center gap-2 cursor-pointer"
          >
            <span>Proceed to Analysis</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Tabs Switcher: Diameter (D) vs Evolution (E) */}
      <div className="flex items-center gap-2 border-b border-slate-200 pb-2">
        <button
          onClick={() => setActiveTab('diameter')}
          className={`px-5 py-2.5 rounded-2xl text-xs font-bold flex items-center gap-2 transition-all cursor-pointer ${
            activeTab === 'diameter'
              ? 'bg-teal-700 text-white shadow-xs'
              : 'bg-white text-slate-600 hover:text-slate-900 border border-slate-200/70'
          }`}
        >
          <Ruler className="w-4 h-4" />
          <span>Criterion D: Physical Diameter & Scale</span>
          {diameterResult?.status === 'MEASURED' && (
            <span className="px-2 py-0.5 rounded-full text-[10px] bg-emerald-100 text-emerald-800 font-extrabold">
              Calibrated ({diameterResult.longest_diameter_mm} mm)
            </span>
          )}
        </button>

        <button
          onClick={() => setActiveTab('evolution')}
          className={`px-5 py-2.5 rounded-2xl text-xs font-bold flex items-center gap-2 transition-all cursor-pointer ${
            activeTab === 'evolution'
              ? 'bg-teal-700 text-white shadow-xs'
              : 'bg-white text-slate-600 hover:text-slate-900 border border-slate-200/70'
          }`}
        >
          <History className="w-4 h-4" />
          <span>Criterion E: Longitudinal Evolution & History</span>
          {evolutionResult?.status === 'OBSERVED' && (
            <span className="px-2 py-0.5 rounded-full text-[10px] bg-teal-100 text-teal-800 font-extrabold">
              Aligned ({evolutionResult.area_change_percent}%)
            </span>
          )}
        </button>
      </div>

      {/* TAB 1: DIAMETER & RULER CALIBRATION */}
      {activeTab === 'diameter' && (
        <div className="bg-white rounded-3xl border border-slate-200/90 shadow-xs p-6 md:p-8 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-100">
            <div>
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <Ruler className="w-5 h-5 text-teal-700" />
                Lesion Diameter Assessment
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Support photographs with a millimeter ruler or manual measurement. Arbitrary pixel conversion is prohibited.
              </p>
            </div>

            {/* Mode Selector */}
            <div className="inline-flex rounded-xl bg-slate-100 p-1 border border-slate-200/60 self-start sm:self-auto text-xs">
              <button
                onClick={() => setDiameterMode('ruler')}
                className={`px-3 py-1 rounded-lg font-bold transition-all cursor-pointer ${
                  diameterMode === 'ruler'
                    ? 'bg-white text-teal-800 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Interactive Ruler
              </button>
              <button
                onClick={() => setDiameterMode('manual')}
                className={`px-3 py-1 rounded-lg font-bold transition-all cursor-pointer ${
                  diameterMode === 'manual'
                    ? 'bg-white text-teal-800 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Manual Entry
              </button>
              <button
                onClick={() => setDiameterMode('none')}
                className={`px-3 py-1 rounded-lg font-bold transition-all cursor-pointer ${
                  diameterMode === 'none'
                    ? 'bg-white text-teal-800 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Skip (Unavailable)
              </button>
            </div>
          </div>

          {diameterMode === 'ruler' && (
            <div className="space-y-4">
              <div className="p-4 rounded-2xl bg-teal-50/50 border border-teal-200/70 text-xs text-teal-950 flex items-start gap-2.5">
                <Info className="w-4 h-4 text-teal-700 shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <span className="font-bold block">How to calibrate:</span>
                  <p>
                    1. Click two tick marks along the physical ruler visible in the photograph (e.g., 0 cm and 1 cm).
                    <br />
                    2. Specify the physical distance between them in millimeters (default: 10 mm).
                    <br />
                    3. Click <strong>"Calculate Calibrated Diameter"</strong>. The longest Feret diameter is extracted automatically from the segmentation mask.
                  </p>
                </div>
              </div>

              {/* Interactive Canvas */}
              <div className="relative rounded-2xl overflow-hidden border border-slate-200 bg-slate-900/5 flex flex-col items-center justify-center p-2">
                <canvas
                  ref={canvasRef}
                  onClick={handleCanvasClick}
                  className="max-h-[500px] w-auto max-w-full rounded-xl cursor-crosshair shadow-xs select-none"
                />
                <div className="text-[11px] text-slate-500 mt-2 font-medium">
                  {point1 && !point2
                    ? 'Point 1 selected. Click a second tick mark along the ruler.'
                    : point1 && point2
                    ? 'Both points selected. Enter distance and apply calibration below.'
                    : 'Click Point 1 on any clear ruler tick mark.'}
                </div>
              </div>

              {/* Calibration Controls */}
              <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-2xl bg-slate-50 border border-slate-200">
                <div className="flex items-center gap-3">
                  <label className="text-xs font-bold text-slate-700">Distance between points:</label>
                  <div className="flex items-center gap-1.5">
                    <input
                      type="number"
                      step="0.5"
                      min="1"
                      value={physicalDistanceMm}
                      onChange={(e) => setPhysicalDistanceMm(parseFloat(e.target.value) || 10)}
                      className="w-20 px-3 py-1.5 bg-white border border-slate-300 rounded-xl text-xs font-bold text-slate-900 focus:outline-teal-700"
                    />
                    <span className="text-xs font-bold text-slate-500">mm</span>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={handleResetPoints}
                    className="px-3 py-1.5 rounded-xl text-xs font-semibold text-slate-600 hover:text-slate-900 bg-white border border-slate-200 hover:bg-slate-100"
                  >
                    Reset Points
                  </button>
                  <button
                    onClick={handleApplyRulerCalibration}
                    disabled={!point1 || !point2 || calibrating}
                    className="px-4 py-1.5 rounded-xl text-xs font-bold text-white bg-teal-700 hover:bg-teal-800 disabled:opacity-40 transition-all flex items-center gap-1.5 cursor-pointer"
                  >
                    {calibrating ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Ruler className="w-3.5 h-3.5" />}
                    Calculate Calibrated Diameter
                  </button>
                </div>
              </div>

              {calibrationError && (
                <div className="p-3 bg-rose-50 border border-rose-200 text-rose-800 text-xs rounded-xl flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
                  <span>{calibrationError}</span>
                </div>
              )}

              {/* Diameter Result Box */}
              {diameterResult && (
                <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                      Calculated Measurement
                    </span>
                    <span className="px-2.5 py-0.5 rounded-full text-[11px] font-extrabold bg-emerald-100 text-emerald-800 border border-emerald-200">
                      Provenance: {diameterResult.status}
                    </span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
                    <div className="p-3 rounded-xl bg-white border border-slate-200">
                      <div className="text-slate-400 font-medium">Longest Lesion Diameter</div>
                      <div className="text-xl font-black text-slate-900 mt-1">
                        {diameterResult.longest_diameter_mm} mm
                      </div>
                      <div className="text-[10px] text-slate-400 mt-0.5">
                        Feret caliper distance across contour
                      </div>
                    </div>

                    <div className="p-3 rounded-xl bg-white border border-slate-200">
                      <div className="text-slate-400 font-medium">Calibrated Scale</div>
                      <div className="text-xl font-black text-slate-900 mt-1">
                        {diameterResult.pixels_per_mm} px/mm
                      </div>
                      <div className="text-[10px] text-slate-400 mt-0.5">
                        {diameterResult.ruler_calibration?.pixel_distance} px / {physicalDistanceMm} mm
                      </div>
                    </div>

                    <div className="p-3 rounded-xl bg-white border border-slate-200">
                      <div className="text-slate-400 font-medium">Calculated Area</div>
                      <div className="text-xl font-black text-slate-900 mt-1">
                        {diameterResult.lesion_area_mm2 || 'N/A'} mm²
                      </div>
                      <div className="text-[10px] text-slate-400 mt-0.5">
                        2D segmented lesion surface
                      </div>
                    </div>
                  </div>

                  <div className="p-3 rounded-xl bg-amber-50/70 border border-amber-200/80 text-[11px] text-amber-950 flex items-start gap-2">
                    <HelpCircle className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
                    <span>{diameterResult.guideline_note}</span>
                  </div>
                </div>
              )}
            </div>
          )}

          {diameterMode === 'manual' && (
            <div className="max-w-md space-y-4">
              <label className="text-xs font-bold text-slate-700 block">
                Enter Patient or Clinician Measured Longest Diameter:
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  step="0.1"
                  min="0.5"
                  placeholder="e.g. 7.5"
                  value={manualDiameter}
                  onChange={(e) => setManualDiameter(e.target.value)}
                  className="px-4 py-2 border border-slate-300 rounded-xl text-sm font-bold text-slate-900 focus:outline-teal-700 w-36"
                />
                <span className="text-sm font-bold text-slate-600">millimeters (mm)</span>
              </div>
              <p className="text-xs text-slate-500">
                This value will be recorded with provenance tag <code>USER_REPORTED</code> and included in the screening report.
              </p>
            </div>
          )}

          {diameterMode === 'none' && (
            <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200 text-xs text-slate-600 space-y-1">
              <div className="font-bold text-slate-800">Physical Diameter Left Uncalibrated</div>
              <p>
                In accordance with dermatological guidelines, the system will mark Criterion D as <code>UNAVAILABLE</code> rather than fabricating an arbitrary pixel-to-millimeter conversion.
              </p>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: LONGITUDINAL EVOLUTION & HISTORY */}
      {activeTab === 'evolution' && (
        <div className="bg-white rounded-3xl border border-slate-200/90 shadow-xs p-6 md:p-8 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-100">
            <div>
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <History className="w-5 h-5 text-teal-700" />
                Criterion E: Lesion Evolution & Historical Comparison
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Upload an earlier photo of the same lesion or document patient-reported symptoms.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Earlier Photograph Upload */}
            <div className="p-5 rounded-2xl bg-slate-50/80 border border-slate-200 space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
                  <Upload className="w-4 h-4 text-teal-700" />
                  Earlier Lesion Photograph (Optional)
                </span>
                {baselineFile && (
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-teal-100 text-teal-800">
                    Selected
                  </span>
                )}
              </div>

              {!baselinePreviewUrl ? (
                <label className="border-2 border-dashed border-slate-300 hover:border-teal-600 rounded-2xl p-6 flex flex-col items-center justify-center cursor-pointer transition-colors bg-white">
                  <Upload className="w-8 h-8 text-slate-400 mb-2" />
                  <span className="text-xs font-bold text-slate-700">Choose earlier image of this lesion</span>
                  <span className="text-[10px] text-slate-400 mt-1">PNG, JPG up to 15MB</span>
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleBaselineFileChange}
                    className="hidden"
                  />
                </label>
              ) : (
                <div className="space-y-3">
                  <div className="relative aspect-[4/3] rounded-xl overflow-hidden border border-slate-200 bg-white flex items-center justify-center">
                    <img
                      src={baselinePreviewUrl}
                      alt="Earlier Lesion"
                      className="max-h-full max-w-full object-contain"
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-slate-600 truncate max-w-[200px]">
                      {baselineFile?.name}
                    </span>
                    <button
                      onClick={() => {
                        setBaselineFile(null);
                        setBaselinePreviewUrl(null);
                        setEvolutionResult(null);
                      }}
                      className="text-xs font-bold text-rose-600 hover:underline cursor-pointer"
                    >
                      Remove
                    </button>
                  </div>
                </div>
              )}

              {/* Dates */}
              <div className="grid grid-cols-2 gap-3 pt-2">
                <div>
                  <label className="text-[11px] font-bold text-slate-600 flex items-center gap-1 mb-1">
                    <Calendar className="w-3 h-3 text-slate-400" />
                    Earlier Photo Date:
                  </label>
                  <input
                    type="date"
                    value={baselineDate}
                    onChange={(e) => setBaselineDate(e.target.value)}
                    className="w-full px-3 py-1.5 text-xs bg-white border border-slate-300 rounded-xl text-slate-800"
                  />
                </div>
                <div>
                  <label className="text-[11px] font-bold text-slate-600 flex items-center gap-1 mb-1">
                    <Calendar className="w-3 h-3 text-slate-400" />
                    Recent Photo Date:
                  </label>
                  <input
                    type="date"
                    value={followupDate}
                    onChange={(e) => setFollowupDate(e.target.value)}
                    className="w-full px-3 py-1.5 text-xs bg-white border border-slate-300 rounded-xl text-slate-800"
                  />
                </div>
              </div>
            </div>

            {/* Patient-Reported Changes & Symptoms */}
            <div className="p-5 rounded-2xl bg-slate-50/80 border border-slate-200 space-y-4">
              <span className="text-xs font-bold text-slate-800 uppercase tracking-wider block">
                Patient-Reported Evolution & Symptoms (Optional)
              </span>

              <div className="space-y-2 text-xs">
                <label className="flex items-center gap-2 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={symptoms.size_change}
                    onChange={(e) => setSymptoms({ ...symptoms, size_change: e.target.checked })}
                    className="rounded text-teal-700 accent-teal-700"
                  />
                  <span className="text-slate-800 font-medium">Lesion has visibly increased in size</span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={symptoms.color_change}
                    onChange={(e) => setSymptoms({ ...symptoms, color_change: e.target.checked })}
                    className="rounded text-teal-700 accent-teal-700"
                  />
                  <span className="text-slate-800 font-medium">Darkening, multi-tonal, or uneven color changes</span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={symptoms.shape_change}
                    onChange={(e) => setSymptoms({ ...symptoms, shape_change: e.target.checked })}
                    className="rounded text-teal-700 accent-teal-700"
                  />
                  <span className="text-slate-800 font-medium">Edges or border contour have become irregular</span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={symptoms.itching}
                    onChange={(e) => setSymptoms({ ...symptoms, itching: e.target.checked })}
                    className="rounded text-teal-700 accent-teal-700"
                  />
                  <span className="text-slate-800 font-medium">Persistent itching or irritation (pruritus)</span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={symptoms.pain}
                    onChange={(e) => setSymptoms({ ...symptoms, pain: e.target.checked })}
                    className="rounded text-teal-700 accent-teal-700"
                  />
                  <span className="text-slate-800 font-medium">Pain or localized tenderness</span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={symptoms.bleeding}
                    onChange={(e) => setSymptoms({ ...symptoms, bleeding: e.target.checked })}
                    className="rounded text-teal-700 accent-teal-700"
                  />
                  <span className="text-slate-800 font-medium">Spontaneous bleeding or oozing</span>
                </label>
              </div>

              {/* Patient Notes */}
              <div>
                <label className="text-[11px] font-bold text-slate-600 block mb-1">
                  Additional clinical notes or context:
                </label>
                <textarea
                  rows={2}
                  value={symptoms.patient_notes || ''}
                  onChange={(e) => setSymptoms({ ...symptoms, patient_notes: e.target.value })}
                  placeholder="e.g., Noticed rapid darkening over the last 3 months..."
                  className="w-full p-2.5 text-xs bg-white border border-slate-300 rounded-xl text-slate-800 focus:outline-teal-700"
                />
              </div>

              <div className="pt-2">
                <button
                  onClick={handleRunEvolutionComparison}
                  disabled={comparing}
                  className="w-full py-2.5 rounded-xl bg-teal-700 hover:bg-teal-800 text-white font-bold text-xs shadow-xs transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
                >
                  {comparing ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Layers className="w-3.5 h-3.5" />}
                  <span>{baselineFile ? 'Run Digital Image Registration & Delta' : 'Save Patient History'}</span>
                </button>
              </div>
            </div>
          </div>

          {evolutionError && (
            <div className="p-3 bg-rose-50 border border-rose-200 text-rose-800 text-xs rounded-xl flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
              <span>{evolutionError}</span>
            </div>
          )}

          {/* Evolution Result Box */}
          {evolutionResult && (
            <div className="p-6 rounded-2xl bg-slate-50 border border-slate-200 space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-200">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                    Evolution Analysis Status:
                  </span>
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-black uppercase tracking-wider ${
                      evolutionResult.status === 'OBSERVED'
                        ? 'bg-emerald-100 text-emerald-800'
                        : evolutionResult.status === 'REPORTED'
                        ? 'bg-blue-100 text-blue-800'
                        : evolutionResult.status === 'UNCERTAIN'
                        ? 'bg-amber-100 text-amber-800'
                        : 'bg-slate-200 text-slate-700'
                    }`}
                  >
                    {evolutionResult.status}
                  </span>
                </div>

                <div className="text-xs text-slate-500">
                  Comparability Grade: <strong className="text-slate-800">{evolutionResult.comparability}</strong>
                </div>
              </div>

              {/* Difference Overlay & Visual Side by Side if Generated */}
              {evolutionResult.difference_overlay_base64 && (
                <div className="space-y-3">
                  <div className="text-xs font-bold text-slate-700 flex items-center justify-between">
                    <span>Registered Difference Overlay:</span>
                    <div className="flex items-center gap-3 text-[11px] font-medium">
                      <span className="flex items-center gap-1">
                        <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span> Stable Area
                      </span>
                      <span className="flex items-center gap-1">
                        <span className="w-2.5 h-2.5 rounded-full bg-rose-500"></span> Expanded Boundary
                      </span>
                      <span className="flex items-center gap-1">
                        <span className="w-2.5 h-2.5 rounded-full bg-blue-500"></span> Baseline Outline
                      </span>
                    </div>
                  </div>

                  <div className="rounded-2xl overflow-hidden border border-slate-200 bg-white max-h-[420px] flex items-center justify-center p-2">
                    <img
                      src={evolutionResult.difference_overlay_base64}
                      alt="Evolution Difference Overlay"
                      className="max-h-[400px] w-auto object-contain rounded-xl"
                    />
                  </div>
                </div>
              )}

              {/* Metrics Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
                <div className="p-3.5 rounded-xl bg-white border border-slate-200">
                  <div className="text-slate-400 font-medium">Relative 2D Area Delta</div>
                  <div className="text-xl font-black text-slate-900 mt-1">
                    {evolutionResult.area_change_percent !== null && evolutionResult.area_change_percent !== undefined
                      ? `${evolutionResult.area_change_percent > 0 ? '+' : ''}${evolutionResult.area_change_percent}%`
                      : 'N/A'}
                  </div>
                  <div className="text-[10px] text-slate-400 mt-0.5">
                    {evolutionResult.time_interval_display || 'Sequential pair'}
                  </div>
                </div>

                <div className="p-3.5 rounded-xl bg-white border border-slate-200">
                  <div className="text-slate-400 font-medium">Color Histogram Shift</div>
                  <div className="text-xl font-black text-slate-900 mt-1">
                    {evolutionResult.color_shift_metric !== null && evolutionResult.color_shift_metric !== undefined
                      ? evolutionResult.color_shift_metric
                      : 'N/A'}
                  </div>
                  <div className="text-[10px] text-slate-400 mt-0.5">
                    Bhattacharyya distance (&lt;0.4 = stable)
                  </div>
                </div>

                <div className="p-3.5 rounded-xl bg-white border border-slate-200">
                  <div className="text-slate-400 font-medium">Patient Symptoms Flagged</div>
                  <div className="text-xl font-black text-slate-900 mt-1">
                    {Object.values(evolutionResult.patient_reported_changes).filter((v) => v === true).length}
                  </div>
                  <div className="text-[10px] text-slate-400 mt-0.5">Reported clinical markers</div>
                </div>
              </div>

              {/* Technical Confounders Disclosure */}
              {evolutionResult.technical_confounders.confounding_disclosures.length > 0 && (
                <div className="p-3.5 rounded-xl bg-amber-50/70 border border-amber-200/80 text-xs text-amber-950 space-y-1">
                  <div className="font-bold flex items-center gap-1.5 text-amber-900">
                    <ShieldAlert className="w-4 h-4 text-amber-700" />
                    Photographic Confounders Detected:
                  </div>
                  <ul className="list-disc pl-5 space-y-0.5 text-[11px] text-amber-900/90">
                    {evolutionResult.technical_confounders.confounding_disclosures.map((d, i) => (
                      <li key={i}>{d}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Biological Change Disclaimer */}
              <div className="p-3 rounded-xl bg-slate-100 text-[11px] text-slate-600 leading-relaxed">
                <strong>Medical Notice:</strong> {evolutionResult.biological_change_warning}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Action Footer to Proceed to Screening Analysis */}
      <div className="p-6 rounded-3xl bg-slate-100 border border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div>
          <h4 className="text-sm font-bold text-slate-900">
            Finished reviewing measurements and history?
          </h4>
          <p className="text-xs text-slate-500 mt-0.5">
            Proceeding will execute ResNet-18 + Texture deep neural classification and synthesize all findings.
          </p>
        </div>
        <button
          onClick={handleProceed}
          className="px-6 py-3 rounded-2xl text-xs font-bold text-white bg-teal-700 hover:bg-teal-800 shadow-sm transition-all flex items-center gap-2 shrink-0 cursor-pointer"
        >
          <span>Run Screening Analysis</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
