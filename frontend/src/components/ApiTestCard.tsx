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
    <div className="bg-white rounded-xl border border-teal-100 shadow-sm p-6 mb-8">
      <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-5">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-teal-50 flex items-center justify-center text-teal-700">
            <Activity className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-800">Backend API Connectivity Test</h2>
            <p className="text-xs text-slate-500">Live communication check between React and FastAPI</p>
          </div>
        </div>
        <button
          onClick={testConnectivity}
          disabled={loading}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-teal-700 bg-teal-50 hover:bg-teal-100 rounded-lg transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          Retest Endpoints
        </button>
      </div>

      {loading ? (
        <div className="py-6 flex items-center justify-center gap-3 text-slate-400 text-sm">
          <RefreshCw className="w-4 h-4 animate-spin text-teal-600" />
          Probing FastAPI endpoints (/api/v1/health & /api/v1/model/status)...
        </div>
      ) : error ? (
        <div className="p-4 rounded-lg bg-red-50 border border-red-200 text-red-800 text-sm flex items-start gap-3">
          <XCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
          <div>
            <div className="font-semibold">Backend Unreachable or Not Running</div>
            <div className="text-xs text-red-600 mt-1">{error}</div>
            <div className="text-xs text-slate-600 mt-2">
              Start the FastAPI backend with: <code className="bg-white px-1.5 py-0.5 rounded border border-red-200">uvicorn backend.app.main:app --reload</code>
            </div>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 rounded-lg bg-emerald-50/60 border border-emerald-100">
            <div className="flex items-center gap-2 text-emerald-800 font-semibold text-sm mb-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              API Gateway Healthy
            </div>
            <div className="space-y-1 text-xs text-slate-600">
              <div><span className="font-medium text-slate-700">Service:</span> {health?.service}</div>
              <div><span className="font-medium text-slate-700">Version:</span> {health?.version}</div>
              <div><span className="font-medium text-slate-700">Timestamp:</span> {health?.timestamp}</div>
            </div>
          </div>

          <div className="p-4 rounded-lg bg-cyan-50/60 border border-cyan-100">
            <div className="flex items-center gap-2 text-cyan-800 font-semibold text-sm mb-2">
              <Cpu className="w-4 h-4 text-cyan-600" />
              PyTorch Model Service
            </div>
            <div className="space-y-1 text-xs text-slate-600">
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
