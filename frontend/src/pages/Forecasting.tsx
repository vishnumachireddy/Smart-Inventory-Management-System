import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  BrainCircuit,
  Calendar,
  Layers,
  Sparkles,
  Info,
  CheckCircle2,
  RefreshCw,
} from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
} from 'recharts';
import { apiClient } from '../api/client';
import { Product, ForecastResult } from '../types';
import { Badge, LoadingSpinner, EmptyState } from '../components/common';

export const Forecasting: React.FC = () => {
  const [products, setProducts] = useState<Product[]>([]);
  const [selectedProductId, setSelectedProductId] = useState<number | ''>('');
  const [horizon, setHorizon] = useState<number>(7);
  const [modelType, setModelType] = useState<string>('auto');
  const [forecast, setForecast] = useState<ForecastResult | null>(null);
  const [modelEval, setModelEval] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [evalLoading, setEvalLoading] = useState<boolean>(false);

  useEffect(() => {
    const fetchInit = async () => {
      try {
        const prodRes = await apiClient.getProducts();
        setProducts(prodRes.data);
        if (prodRes.data.length > 0) {
          setSelectedProductId(prodRes.data[0].id);
        }
      } catch (err) {
        console.error('Failed to load products for forecasting:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchInit();
  }, []);

  const fetchForecast = async (productId: number) => {
    setLoading(true);
    try {
      const res = await apiClient.getForecast(productId, {
        horizon_days: horizon,
        model_type: modelType,
      });
      setForecast(res.data);
    } catch (err) {
      console.error('Failed to generate forecast:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchEvaluation = async (productId: number) => {
    setEvalLoading(true);
    try {
      const res = await apiClient.getModelEvaluation({ product_id: productId });
      setModelEval(res.data);
    } catch (err) {
      console.error('Failed to load evaluation metrics:', err);
    } finally {
      setEvalLoading(false);
    }
  };

  useEffect(() => {
    if (typeof selectedProductId === 'number') {
      fetchForecast(selectedProductId);
      fetchEvaluation(selectedProductId);
    }
  }, [selectedProductId, horizon, modelType]);

  // Transform timeline points for Recharts dual series
  const chartData = React.useMemo(() => {
    if (!forecast) return [];
    return forecast.forecast.map((pt) => ({
      date: pt.date.slice(5), // MM-DD
      actual: pt.is_forecast ? null : pt.actual_demand,
      forecast: pt.is_forecast ? pt.predicted_demand : pt.actual_demand,
      is_forecast: pt.is_forecast,
    }));
  }, [forecast]);

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Demand Forecasting Engine</h1>
          <p className="text-xs text-slate-500 mt-1">
            Machine learning daily velocity projections, backtested MAE & RMSE evaluation, and replenishment estimates
          </p>
        </div>
        {typeof selectedProductId === 'number' && (
          <button
            onClick={() => {
              fetchForecast(selectedProductId);
              fetchEvaluation(selectedProductId);
            }}
            className="flex items-center space-x-1.5 px-3 py-2 bg-white hover:bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold text-slate-700 shadow-sm"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Retrain & Re-estimate</span>
          </button>
        )}
      </div>

      {/* Control Configuration Panel */}
      <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label className="block text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-1.5">
            Select Product
          </label>
          <select
            value={selectedProductId}
            onChange={(e) => setSelectedProductId(Number(e.target.value))}
            className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 bg-white text-slate-800 font-medium focus:ring-2 focus:ring-indigo-500"
          >
            {products.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} ({p.sku})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-1.5">
            Forecast Horizon
          </label>
          <div className="grid grid-cols-3 gap-1 bg-slate-100 p-1 rounded-xl">
            {[7, 14, 30].map((h) => (
              <button
                key={h}
                type="button"
                onClick={() => setHorizon(h)}
                className={`py-1.5 text-xs font-bold rounded-lg transition-colors ${
                  horizon === h ? 'bg-white text-indigo-700 shadow-xs' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                {h} Days
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-1.5">
            Pipeline Algorithm
          </label>
          <select
            value={modelType}
            onChange={(e) => setModelType(e.target.value)}
            className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 bg-white text-slate-800 font-medium focus:ring-2 focus:ring-indigo-500"
          >
            <option value="auto">Auto (Select lowest error model)</option>
            <option value="moving_average">Moving Average Baseline (7-Day)</option>
            <option value="random_forest">Random Forest Regressor (Lag Features)</option>
          </select>
        </div>
      </div>

      {/* Main Forecast Chart & Evaluation Metrics */}
      {loading ? (
        <LoadingSpinner label="Generating demand forecast..." />
      ) : !forecast ? (
        <EmptyState
          title="No Forecast Generated"
          description="Select an active product to view demand predictions."
        />
      ) : (
        <div className="space-y-6">
          {/* Chart Card */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-4 border-b border-slate-100 gap-2">
              <div>
                <div className="flex items-center space-x-2">
                  <h3 className="text-base font-bold text-slate-900">{forecast.product_name}</h3>
                  <Badge variant="info">{forecast.model_type}</Badge>
                </div>
                <p className="text-xs text-slate-500 mt-0.5">
                  Distinguishing actual historical customer demand from projected {forecast.horizon_days}-day future velocity
                </p>
              </div>

              <div className="flex items-center space-x-3 text-xs">
                <div className="flex items-center space-x-1.5">
                  <span className="w-3 h-0.5 bg-slate-500 rounded"></span>
                  <span className="text-slate-600 font-medium">Actual Historical Sales</span>
                </div>
                <div className="flex items-center space-x-1.5">
                  <span className="w-3 h-0.5 bg-indigo-600 border-dashed rounded"></span>
                  <span className="text-indigo-600 font-bold">Predicted Future Demand</span>
                </div>
              </div>
            </div>

            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="date" stroke="#94a3b8" fontSize={11} />
                  <YAxis stroke="#94a3b8" fontSize={11} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#ffffff',
                      borderRadius: '8px',
                      border: '1px solid #e2e8f0',
                      fontSize: '12px',
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="actual"
                    name="Actual Sales"
                    stroke="#64748b"
                    strokeWidth={2}
                    dot={{ r: 3 }}
                    connectNulls={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="forecast"
                    name="Demand Forecast"
                    stroke="#6366f1"
                    strokeWidth={2.5}
                    strokeDasharray="4 4"
                    dot={{ r: 4, stroke: '#6366f1', fill: '#ffffff' }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Model Statistics & Comparison Grid */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white p-4 rounded-xl border border-slate-200">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block">
                Average Daily Velocity
              </span>
              <span className="text-xl font-extrabold text-slate-900 mt-1 block">
                {forecast.daily_average_demand} <span className="text-xs font-normal text-slate-500">units/day</span>
              </span>
            </div>

            <div className="bg-white p-4 rounded-xl border border-slate-200">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block">
                Historical Training Periods
              </span>
              <span className="text-xl font-extrabold text-slate-900 mt-1 block font-mono">
                {forecast.historical_periods} <span className="text-xs font-normal text-slate-500">daily records</span>
              </span>
            </div>

            <div className="bg-white p-4 rounded-xl border border-slate-200">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block">
                Validation MAE (Error)
              </span>
              <span className="text-xl font-extrabold text-indigo-600 mt-1 block font-mono">
                {forecast.mae !== null ? forecast.mae : 'N/A'}
              </span>
              <span className="text-[10px] text-slate-400">Mean Absolute Error</span>
            </div>

            <div className="bg-white p-4 rounded-xl border border-slate-200">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block">
                Validation RMSE
              </span>
              <span className="text-xl font-extrabold text-indigo-600 mt-1 block font-mono">
                {forecast.rmse !== null ? forecast.rmse : 'N/A'}
              </span>
              <span className="text-[10px] text-slate-400">Root Mean Squared Error</span>
            </div>
          </div>

          {/* Machine Learning Insights Box */}
          <div className="p-4 rounded-2xl bg-indigo-50/50 border border-indigo-200 flex items-start space-x-3 text-xs">
            <Sparkles className="w-5 h-5 text-indigo-600 shrink-0 mt-0.5" />
            <div>
              <h5 className="font-bold text-indigo-950">Replenishment Rationale & Algorithmic Notes</h5>
              <p className="text-indigo-900/80 mt-0.5">{forecast.insights}</p>
              {modelEval?.comparison_summary && (
                <p className="text-slate-600 mt-1.5 font-medium border-t border-indigo-100 pt-1.5">
                  Comparison Summary: {modelEval.comparison_summary}
                </p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
