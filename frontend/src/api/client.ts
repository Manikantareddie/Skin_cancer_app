import type {
  AIExplanationRequest,
  AIExplanationResponse,
  AnalysisResponse,
  DiameterAssessment,
  EvolutionAssessment,
  HealthResponse,
  ModelStatusResponse,
  PatientReportedChanges,
} from './types';

const API_BASE = '/api/v1';

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error(`Health check failed: HTTP ${res.status}`);
  return res.json();
}

export async function fetchModelStatus(): Promise<ModelStatusResponse> {
  const res = await fetch(`${API_BASE}/model/status`);
  if (!res.ok) throw new Error(`Model status failed: HTTP ${res.status}`);
  return res.json();
}

export interface AnalyzeImageOptions {
  file: File;
  baselineFile?: File | null;
  baselineDate?: string | null;
  followupDate?: string | null;
  manualDiameterMm?: number | null;
  p1?: { x: number; y: number } | null;
  p2?: { x: number; y: number } | null;
  physicalDistanceMm?: number | null;
  patientReportedChanges?: PatientReportedChanges | null;
}

export async function analyzeImage(options: AnalyzeImageOptions | File): Promise<AnalysisResponse> {
  const formData = new FormData();

  if (options instanceof File) {
    formData.append('file', options);
  } else {
    formData.append('file', options.file);
    if (options.baselineFile) {
      formData.append('baseline_file', options.baselineFile);
    }
    if (options.baselineDate) {
      formData.append('baseline_date', options.baselineDate);
    }
    if (options.followupDate) {
      formData.append('followup_date', options.followupDate);
    }
    if (options.manualDiameterMm !== undefined && options.manualDiameterMm !== null) {
      formData.append('manual_diameter_mm', options.manualDiameterMm.toString());
    }
    if (options.p1 && options.p2 && options.physicalDistanceMm) {
      formData.append('p1_x', options.p1.x.toString());
      formData.append('p1_y', options.p1.y.toString());
      formData.append('p2_x', options.p2.x.toString());
      formData.append('p2_y', options.p2.y.toString());
      formData.append('physical_distance_mm', options.physicalDistanceMm.toString());
    }
    if (options.patientReportedChanges) {
      formData.append('patient_reported_json', JSON.stringify(options.patientReportedChanges));
    }
  }

  const res = await fetch(`${API_BASE}/analyze`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: 'Analysis request failed' }));
    throw new Error(errorData.detail || `Analysis failed: HTTP ${res.status}`);
  }

  return res.json();
}

export async function calibrateRuler(
  file: File,
  p1?: { x: number; y: number },
  p2?: { x: number; y: number },
  physicalDistanceMm?: number,
  autoDetect = false,
): Promise<DiameterAssessment> {
  const formData = new FormData();
  formData.append('file', file);
  if (p1 && p2 && physicalDistanceMm) {
    formData.append('p1_x', p1.x.toString());
    formData.append('p1_y', p1.y.toString());
    formData.append('p2_x', p2.x.toString());
    formData.append('p2_y', p2.y.toString());
    formData.append('physical_distance_mm', physicalDistanceMm.toString());
  }
  formData.append('auto_detect', autoDetect.toString());

  const res = await fetch(`${API_BASE}/measurements/calibrate-ruler`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Calibration failed' }));
    throw new Error(err.detail || `Calibration failed: HTTP ${res.status}`);
  }

  return res.json();
}

export async function compareEvolution(
  followupFile: File,
  baselineFile?: File | null,
  baselineDate?: string | null,
  followupDate?: string | null,
  reportedChanges?: PatientReportedChanges | null,
): Promise<EvolutionAssessment> {
  const formData = new FormData();
  formData.append('followup_file', followupFile);
  if (baselineFile) {
    formData.append('baseline_file', baselineFile);
  }
  if (baselineDate) {
    formData.append('baseline_date', baselineDate);
  }
  if (followupDate) {
    formData.append('followup_date', followupDate);
  }
  if (reportedChanges) {
    formData.append('patient_reported_json', JSON.stringify(reportedChanges));
  }

  const res = await fetch(`${API_BASE}/evolution/compare`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Evolution comparison failed' }));
    throw new Error(err.detail || `Evolution comparison failed: HTTP ${res.status}`);
  }

  return res.json();
}

export async function generateAiSummary(payload: AIExplanationRequest): Promise<AIExplanationResponse> {
  const res = await fetch(`${API_BASE}/ai/summary`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: 'Failed to generate AI explanation' }));
    throw new Error(errorData.detail || `AI explanation failed: HTTP ${res.status}`);
  }

  return res.json();
}

export interface DownloadPdfParams {
  originalFile: File;
  heatmapBase64: string;
  prediction: string;
  confidence: number;
  riskLevel: string;
  abcdResults: Record<string, string>;
  aiSummary: string;
  caseId: string;
  differenceBase64?: string | null;
  diameterDetail?: string | null;
  evolutionDetail?: string | null;
}

export async function downloadPdfReport(params: DownloadPdfParams): Promise<void> {
  const formData = new FormData();
  formData.append('original_file', params.originalFile);
  formData.append('heatmap_base64', params.heatmapBase64);
  formData.append('prediction', params.prediction);
  formData.append('confidence', params.confidence.toString());
  formData.append('risk_level', params.riskLevel);
  formData.append('abcd_results_json', JSON.stringify(params.abcdResults));
  formData.append('ai_summary', params.aiSummary);
  formData.append('case_id', params.caseId);
  if (params.differenceBase64) {
    formData.append('difference_base64', params.differenceBase64);
  }
  if (params.diameterDetail) {
    formData.append('diameter_detail', params.diameterDetail);
  }
  if (params.evolutionDetail) {
    formData.append('evolution_detail', params.evolutionDetail);
  }

  const res = await fetch(`${API_BASE}/report/generate`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    throw new Error(`Report generation failed: HTTP ${res.status}`);
  }

  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `Skin_Cancer_Report_${params.caseId.replace(/-/g, '_')}.pdf`;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}
