import React, { useEffect, useState } from 'react';
import { Activity, Cpu, CheckCircle2, XCircle, RefreshCw } from 'lucide-react';
import { fetchHealth, fetchModelStatus } from '../api/client';
import type { HealthResponse, ModelStatusResponse } from '../api/types';

export const ApiTestCard: React.FC = () => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [modelStatus, setModelStatus] = useState<ModelStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const testConnectivity = async () => {
    setLoading(true);
    setError(null);
    try {
      const [hData, mData] = await Promise.all([fetchHealth(), fetchModelStatus()]);
      setHealth(hData);
      setModelStatus(mData);
    } catch (err: any) {
      setError(err?.message || 'Could not connect to FastAPI backend');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    testConnectivity();
  }, []);

  return (
    <div className="bg-white rounded-xl sm:rounded-2xl border border-teal-100 shadow-sm p-4 sm:p-6 mb-4 sm:mb-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 sm:pb-4 border-b border-slate-100 mb-4 sm:mb-5">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-lg bg-teal-50 flex items-center justify-center text-teal-700 shrink-0">
            <Activity className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-sm sm:text-base font-bold text-slate-800">Backend API Connectivity Test</h2>
            <p className="text-xs text-slate-500">Live communication check between React and FastAPI</p>
          </div>
        </div>
        <button
          onClick={testConnectivity}
          disabled={loading}
          className="flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-semibold text-teal-700 bg-teal-50 hover:bg-teal-100 rounded-lg transition-colors disabled:opacity-50 cursor-pointer min-h-[36px] self-start sm:self-auto"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Retest Endpoints</span>
        </button>
      </div>

      {loading ? (
        <div className="py-6 flex items-center justify-center gap-3 text-slate-400 text-xs sm:text-sm">
          <RefreshCw className="w-4 h-4 animate-spin text-teal-600" />
          <span>Probing FastAPI endpoints (/api/v1/health & /api/v1/model/status)...</span>
        </div>
      ) : error ? (
        <div className="p-3.5 sm:p-4 rounded-xl bg-red-50 border border-red-200 text-red-800 text-xs sm:text-sm flex items-start gap-3">
          <XCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
          <div className="min-w-0 flex-1">
            <div className="font-semibold">Backend Unreachable or Not Running</div>
            <div className="text-xs text-red-600 mt-1 break-words">{error}</div>
            <div className="text-xs text-slate-600 mt-2 leading-relaxed">
              Start the FastAPI backend with: <code className="bg-white px-1.5 py-0.5 rounded border border-red-200 inline-block">uvicorn backend.app.main:app --reload</code>
            </div>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 sm:gap-4">
          <div className="p-3.5 sm:p-4 rounded-xl bg-emerald-50/60 border border-emerald-100">
            <div className="flex items-center gap-2 text-emerald-800 font-semibold text-xs sm:text-sm mb-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
              <span>API Gateway Healthy</span>
            </div>
            <div className="space-y-1 text-xs text-slate-600 break-words">
              <div><span className="font-medium text-slate-700">Service:</span> {health?.service}</div>
              <div><span className="font-medium text-slate-700">Version:</span> {health?.version}</div>
              <div><span className="font-medium text-slate-700">Timestamp:</span> {health?.timestamp}</div>
            </div>
          </div>

          <div className="p-3.5 sm:p-4 rounded-xl bg-cyan-50/60 border border-cyan-100">
            <div className="flex items-center gap-2 text-cyan-800 font-semibold text-xs sm:text-sm mb-2">
              <Cpu className="w-4 h-4 text-cyan-600 shrink-0" />
              <span>PyTorch Model Service</span>
            </div>
            <div className="space-y-1 text-xs text-slate-600 break-words">
              <div><span className="font-medium text-slate-700">Architecture:</span> {modelStatus?.architecture}</div>
              <div><span className="font-medium text-slate-700">Device:</span> {modelStatus?.device}</div>
              <div><span className="font-medium text-slate-700">Weights Status:</span> {modelStatus?.is_loaded ? 'Loaded in Memory' : 'Ready (Lazy Load)'}</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
