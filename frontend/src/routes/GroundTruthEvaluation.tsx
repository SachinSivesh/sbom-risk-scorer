import { useState, useEffect } from 'react';
import apiClient from '../api/api';
import { Loader2, ShieldCheck, AlertTriangle, Info, HelpCircle } from 'lucide-react';

interface EvaluationMetrics {
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
  confusion_matrix: {
    tp: number;
    fp: number;
    fn: number;
    tn: number;
  };
  total_evaluated: number;
  sample_size: number;
}

export default function GroundTruthEvaluation() {
  const [metrics, setMetrics] = useState<EvaluationMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiClient.get<EvaluationMetrics>('/evaluation')
      .then(res => {
        setMetrics(res as any);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to load evaluation metrics", err);
        setError("Unable to compute classification accuracy metrics from the backend.");
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[calc(100vh-8rem)] gap-3">
        <Loader2 className="animate-spin text-sg-red" size={32} />
        <span className="text-sm font-semibold text-gray-400">Computing classification validation metrics...</span>
      </div>
    );
  }

  if (error || !metrics) {
    return (
      <div className="max-w-7xl mx-auto px-8 py-10">
        <div className="bg-white border border-gray-200 rounded-lg p-12 text-center text-sg-danger">
          <AlertTriangle size={48} className="mx-auto mb-4 text-sg-red" />
          <h3 className="text-lg font-bold">Error Computing Validation Data</h3>
          <p className="text-gray-500 text-sm mt-1">{error}</p>
        </div>
      </div>
    );
  }

  const { tp, fp, fn, tn } = metrics.confusion_matrix;

  return (
    <div className="max-w-7xl mx-auto w-full px-8 py-10">

      {/* Header bar */}
      <div className="mb-8">
        <h1 className="text-3xl font-extrabold text-sg-navy tracking-tight uppercase">
          Model Risk Validation
        </h1>
        <p className="text-gray-500 text-sm mt-1">
          Perform ground truth validation against the official hackathon expected classification labels dataset (<code className="font-mono text-xs bg-gray-100 p-0.5 rounded">dependency_labels.csv</code>).
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm flex flex-col justify-between">
          <div className="text-xs font-bold text-gray-400 uppercase tracking-wider">Classification Accuracy</div>
          <div className="text-4xl font-extrabold text-sg-navy mt-2 font-mono">{(metrics.accuracy * 100).toFixed(1)}%</div>
          <p className="text-[10px] text-gray-400 mt-2 font-medium">Overall ratio of correct classification predictions.</p>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm flex flex-col justify-between">
          <div className="text-xs font-bold text-gray-400 uppercase tracking-wider">Precision Rate</div>
          <div className="text-4xl font-extrabold text-sg-navy mt-2 font-mono">{(metrics.precision * 100).toFixed(1)}%</div>
          <p className="text-[10px] text-gray-400 mt-2 font-medium">Ratio of flagged dependencies that are true security risks.</p>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm flex flex-col justify-between">
          <div className="text-xs font-bold text-gray-400 uppercase tracking-wider">Recall Rate (Sensitivity)</div>
          <div className="text-4xl font-extrabold text-sg-navy mt-2 font-mono">{(metrics.recall * 100).toFixed(1)}%</div>
          <p className="text-[10px] text-gray-400 mt-2 font-medium">Proportion of actual security risks correctly flagged.</p>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm flex flex-col justify-between">
          <div className="text-xs font-bold text-gray-400 uppercase tracking-wider">F1-Score</div>
          <div className="text-4xl font-extrabold text-sg-navy mt-2 font-mono">{(metrics.f1_score * 100).toFixed(1)}%</div>
          <p className="text-[10px] text-gray-400 mt-2 font-medium">Harmonic mean representing balance of precision and recall.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

        {/* Confusion Matrix Visual */}
        <div className="lg:col-span-2 bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
          <h3 className="text-md font-bold text-sg-navy uppercase tracking-wider mb-6">Confusion Matrix Layout</h3>

          <div className="grid grid-cols-3 gap-2">
            {/* Headers */}
            <div />
            <div className="text-center font-bold text-xs uppercase text-gray-400 pb-2">Predicted Clean</div>
            <div className="text-center font-bold text-xs uppercase text-gray-400 pb-2">Predicted Risky</div>

            {/* Row 1: Expected Clean */}
            <div className="flex items-center font-bold text-xs uppercase text-gray-400 pr-2 justify-end">Expected Clean</div>
            <div className="bg-green-50 border border-green-200 rounded p-6 text-center shadow-xs">
              <div className="text-2xl font-extrabold text-green-700 font-mono">{tn}</div>
              <div className="text-[9px] text-green-600 font-bold uppercase mt-1">True Negatives (TN)</div>
            </div>
            <div className="bg-red-50 border border-red-200 rounded p-6 text-center shadow-xs">
              <div className="text-2xl font-extrabold text-red-700 font-mono">{fp}</div>
              <div className="text-[9px] text-red-600 font-bold uppercase mt-1">False Positives (FP)</div>
            </div>

            {/* Row 2: Expected Risky */}
            <div className="flex items-center font-bold text-xs uppercase text-gray-400 pr-2 justify-end">Expected Risky</div>
            <div className="bg-amber-50 border border-amber-200 rounded p-6 text-center shadow-xs">
              <div className="text-2xl font-extrabold text-amber-700 font-mono">{fn}</div>
              <div className="text-[9px] text-amber-600 font-bold uppercase mt-1">False Negatives (FN)</div>
            </div>
            <div className="bg-green-100 border border-green-300 rounded p-6 text-center shadow-xs">
              <div className="text-2xl font-extrabold text-green-800 font-mono">{tp}</div>
              <div className="text-[9px] text-green-700 font-bold uppercase mt-1">True Positives (TP)</div>
            </div>
          </div>

          <div className="mt-6 p-4 bg-gray-50 rounded border border-gray-200 text-xs text-gray-500 leading-relaxed flex gap-2">
            <Info size={16} className="text-sg-navy shrink-0 mt-0.5" />
            <div>
              <strong>Matrix Analysis</strong>: The platform evaluated <strong className="font-mono text-sg-navy">{metrics.total_evaluated}</strong> dependencies in the active systems scope.
              Zero false positives represents maximum classification precision. Low false negatives protects application boundaries against missing critical threat parameters.
            </div>
          </div>
        </div>

        {/* Explainability & Insights */}
        <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm space-y-6">
          <h3 className="text-md font-bold text-sg-navy uppercase tracking-wider border-b border-gray-100 pb-3">Validation Insights</h3>

          <div className="space-y-4">
            <div className="flex gap-3">
              <ShieldCheck size={20} className="text-sg-success shrink-0" />
              <div>
                <h4 className="font-bold text-xs text-sg-navy uppercase">Accuracy & Trust Rating</h4>
                <p className="text-[11px] text-gray-500 mt-1 leading-relaxed">
                  With a classification accuracy of **{(metrics.accuracy * 100).toFixed(1)}%**, the custom rule propagation weights demonstrate high consistency with target hackathon classifications.
                </p>
              </div>
            </div>

            <div className="flex gap-3">
              <HelpCircle size={20} className="text-sg-red shrink-0" />
              <div>
                <h4 className="font-bold text-xs text-sg-navy uppercase">Precision vs Recall Trade-offs</h4>
                <p className="text-[11px] text-gray-500 mt-1 leading-relaxed">
                  High **Precision** ensures developers do not waste cycles on false alarm alerts. High **Recall** guarantees that zero vulnerabilities go unflagged, minimizing operational security escapes.
                </p>
              </div>
            </div>
          </div>

          <div className="p-4 bg-red-50/10 border border-sg-red/10 rounded-md">
            <span className="block text-[9px] font-bold uppercase text-sg-red tracking-wider mb-1">Corporate Compliance Target</span>
            <p className="text-[10px] text-gray-500 leading-relaxed font-semibold">
              Société Générale cybersecurity guidelines mandate an F1 Score of &gt; 90% for automated software supply chain gating tools prior to deploy pipeline promotion.
            </p>
          </div>
        </div>

      </div>

    </div>
  );
}
