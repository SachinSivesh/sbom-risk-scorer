import { useParams, useNavigate } from 'react-router-dom';
import { useRiskReport } from '../hooks/useRiskReport';
import { ArrowLeft, Printer, Percent, ShieldCheck, Scale, Award } from 'lucide-react';

export default function RiskReportPage() {
  const { sbomId } = useParams<{ sbomId: string }>();
  const navigate = useNavigate();
  const { data: report, isLoading, error } = useRiskReport(sbomId || '');

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto w-full px-8 py-16 flex items-center justify-center">
        <span className="text-gray-400 font-semibold text-sm">Generating Audit Report...</span>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="max-w-7xl mx-auto w-full px-8 py-10">
        <div className="bg-white border border-gray-200 rounded-lg p-12 text-center text-sg-danger shadow-sm">
          <ArrowLeft size={48} className="mx-auto mb-4 text-sg-red" />
          <h3 className="text-lg font-bold">Report Load Failed</h3>
          <p className="text-gray-500 text-sm mt-1">Could not fetch report details for this SBOM.</p>
        </div>
      </div>
    );
  }

  const handlePrint = () => {
    window.print();
  };

  const getScoreBadgeClass = (s: number | null) => {
    if (s === null) return 'bg-gray-100 text-gray-500 border border-gray-200';
    if (s >= 75) return 'bg-red-100 text-sg-danger border border-sg-danger/20';
    if (s >= 50) return 'bg-amber-100 text-sg-warning border border-sg-warning/20';
    if (s >= 25) return 'bg-yellow-100 text-yellow-700 border border-yellow-500/20';
    return 'bg-green-100 text-sg-success border border-sg-success/20';
  };

  const getScoreColor = (s: number | null) => {
    if (s === null) return 'text-gray-400';
    if (s >= 75) return 'text-sg-danger';
    if (s >= 50) return 'text-sg-warning';
    if (s >= 25) return 'text-yellow-600';
    return 'text-sg-success';
  };

  return (
    <div className="max-w-7xl mx-auto w-full px-8 py-10 print:p-0">
      
      {/* Top action bar */}
      <div className="flex justify-between items-center mb-6 print:hidden">
        <button
          onClick={() => navigate(-1)}
          className="inline-flex items-center gap-1.5 rounded-md border border-gray-200 bg-white px-4 py-2 text-xs font-bold text-gray-500 hover:bg-gray-50 cursor-pointer shadow-sm"
        >
          <ArrowLeft size={14} /> Back
        </button>
        <button
          onClick={handlePrint}
          className="inline-flex items-center gap-1.5 rounded-md border border-gray-200 bg-white px-4 py-2 text-xs font-bold text-sg-navy hover:bg-gray-50 cursor-pointer shadow-sm"
        >
          <Printer size={14} /> Print Report
        </button>
      </div>

      {/* Audit Report Container */}
      <div className="bg-white border border-gray-200 rounded-lg p-10 shadow-sm print:border-none print:shadow-none">
        
        {/* Report Header */}
        <div className="border-b border-gray-200 pb-6 mb-8">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-extrabold text-sg-navy uppercase tracking-tight">
                Security & Compliance Audit Report
              </h1>
              <p className="text-xs text-gray-400 font-semibold font-mono mt-1">SBOM UUID: {report.sbom_id}</p>
            </div>
            <div className="text-right">
              <div className="text-3xl font-extrabold text-sg-red font-mono">{report.overall_score}/100</div>
              <span className={`inline-block rounded px-2.5 py-0.5 text-[10px] font-extrabold uppercase mt-1 border ${getScoreBadgeClass(report.overall_score)}`}>
                {report.category} RISK
              </span>
            </div>
          </div>
        </div>

        {/* Audit Details */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-10">
          <div>
            <div className="flex items-center gap-2 text-sg-red mb-2">
              <ShieldCheck size={18} />
              <h4 className="text-xs font-bold uppercase tracking-wider">Vulnerabilities Subscore</h4>
            </div>
            <div className={`text-2xl font-extrabold font-mono ${getScoreColor(report.vulnerability_subscore)}`}>
              {report.vulnerability_subscore}/100
            </div>
            <p className="text-xs text-gray-400 mt-1">Weighted average of the maximum CVSS score per dependency.</p>
          </div>

          <div>
            <div className="flex items-center gap-2 text-sg-red mb-2">
              <Scale size={18} />
              <h4 className="text-xs font-bold uppercase tracking-wider">License Subscore</h4>
            </div>
            <div className={`text-2xl font-extrabold font-mono ${getScoreColor(report.license_subscore)}`}>
              {report.license_subscore}/100
            </div>
            <p className="text-xs text-gray-400 mt-1">Risk evaluation parsed from static conflict compatibility matrix mapping.</p>
          </div>

          <div>
            <div className="flex items-center gap-2 text-sg-red mb-2">
              <Award size={18} />
              <h4 className="text-xs font-bold uppercase tracking-wider">Maintenance Subscore</h4>
            </div>
            <div className={`text-2xl font-extrabold font-mono ${getScoreColor(report.maintenance_subscore)}`}>
              {report.maintenance_subscore}/100
            </div>
            <p className="text-xs text-gray-400 mt-1">GitHub repository metrics tracking commit activity, stars, and release frequency.</p>
          </div>
        </div>

        {/* Formula breakdown */}
        <div className="bg-gray-50 border border-gray-100 rounded-md p-5 mb-8">
          <div className="flex items-center gap-2 mb-2 text-sg-navy">
            <Percent size={16} className="text-sg-red" />
            <h4 className="text-xs font-bold uppercase tracking-wider">Scoring Formula Matrix</h4>
          </div>
          <p className="text-xs text-gray-500 leading-relaxed">
            Overall risk score is calculated deterministically using direct vs transitive weight ratios: 
            <code className="bg-gray-200 px-1 py-0.5 rounded mx-1 font-bold text-sg-navy">0.5 * Vulnerability + 0.3 * License + 0.2 * Maintenance</code>. 
            Weights are normalized for missing data points. Direct dependencies carry a 2x weight multiplier.
          </p>
        </div>

        {/* Audit Log Breakdown */}
        {report.breakdown && (
          <div>
            <h3 className="text-base font-bold text-sg-navy mb-4">Top Contributing Risk Nodes</h3>
            <div className="overflow-x-auto border border-gray-200 rounded-md">
              <table className="min-w-full divide-y divide-gray-200 text-left">
                <thead className="bg-gray-50">
                  <tr className="text-xs font-bold text-gray-500 uppercase tracking-wider">
                    <th className="px-4 py-3">Component Name</th>
                    <th className="px-4 py-3">Version</th>
                    <th className="px-4 py-3">Scope</th>
                    <th className="px-4 py-3">Security Risk</th>
                    <th className="px-4 py-3">License Risk</th>
                    <th className="px-4 py-3">Weighted Contribution</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 text-xs">
                  {report.breakdown.top_contributing_dependencies?.map((dep: any, idx: number) => (
                    <tr key={idx} className="hover:bg-gray-50/50 transition-all">
                      <td className="px-4 py-3 font-bold text-sg-navy">{dep.name}</td>
                      <td className="px-4 py-3 font-mono">{dep.version}</td>
                      <td className="px-4 py-3">
                        <span className={`inline-block rounded px-2 py-0.5 text-[9px] font-extrabold uppercase ${
                          dep.is_direct ? 'bg-red-50 text-sg-red border border-sg-red/20' : 'bg-gray-100 text-gray-400'
                        }`}>
                          {dep.is_direct ? 'Direct' : 'Transitive'}
                        </span>
                      </td>
                      <td className={`px-4 py-3 font-semibold ${getScoreColor(dep.vuln_score)}`}>{dep.vuln_score}</td>
                      <td className={`px-4 py-3 font-semibold ${getScoreColor(dep.license_score)}`}>{dep.license_score}</td>
                      <td className="px-4 py-3 font-extrabold text-sg-navy font-mono">{dep.weighted_contribution}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
