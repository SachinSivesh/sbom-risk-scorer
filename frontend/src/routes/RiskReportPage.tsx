import { useParams, Link } from 'react-router-dom';
import { useRiskReport } from '../hooks/useRiskReport';
import { ArrowLeft, Printer, Percent, ShieldCheck, Scale, Award } from 'lucide-react';

export default function RiskReportPage() {
  const { sbomId } = useParams<{ sbomId: string }>();
  const { data: report, isLoading, error } = useRiskReport(sbomId || '');

  if (isLoading) {
    return (
      <div className="page-container flex align-center justify-between" style={{ height: '300px' }}>
        <span className="text-muted" style={{ margin: 'auto' }}>Generating Audit Report...</span>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="page-container">
        <div className="glass-card text-center" style={{ padding: '3rem', color: 'var(--color-critical)' }}>
          <h3>Report Unavailable</h3>
          <p className="text-muted mt-4">Could not generate the audit score details.</p>
        </div>
      </div>
    );
  }

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="page-container">
      {/* Top action bar */}
      <div className="flex justify-between align-center mb-4">
        <Link to={`/application/${report.application_id}`} className="btn btn-secondary">
          <ArrowLeft size={16} /> Back to Details
        </Link>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button className="btn btn-secondary" onClick={handlePrint}>
            <Printer size={16} /> Print Report
          </button>
        </div>
      </div>

      {/* Audit Report Container */}
      <div className="glass-card" style={{ padding: '3rem', background: '#11131c', border: '1px solid var(--border-color-hover)' }}>
        {/* Report Header */}
        <div style={{ borderBottom: '2px solid var(--border-color)', paddingBottom: '2rem', marginBottom: '2rem' }}>
          <div className="flex justify-between align-center">
            <div>
              <h1 className="m-0" style={{ fontSize: '1.75rem' }}>Security & Licensing Compliance Report</h1>
              <p className="text-muted" style={{ marginTop: '0.5rem' }}>SBOM ID: {report.sbom_id}</p>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--color-primary)' }}>{report.overall_score}/100</div>
              <span className={`badge ${report.category === 'CRITICAL' ? 'badge-critical' : report.category === 'HIGH' ? 'badge-high' : report.category === 'MEDIUM' ? 'badge-medium' : 'badge-low'}`}>
                {report.category} RISK
              </span>
            </div>
          </div>
        </div>

        {/* Audit Details */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '2rem', marginBottom: '3rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--color-primary)', marginBottom: '0.5rem' }}>
              <ShieldCheck size={18} />
              <h4 style={{ margin: 0 }}>Vulnerabilities Subscore</h4>
            </div>
            <div style={{ fontSize: '1.5rem', fontWeight: 700 }}>{report.vulnerability_subscore}/100</div>
            <p className="text-muted" style={{ fontSize: '0.8rem', marginTop: '0.25rem' }}>Weighted average of maximum CVSS score per dependency.</p>
          </div>

          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--color-primary)', marginBottom: '0.5rem' }}>
              <Scale size={18} />
              <h4 style={{ margin: 0 }}>License Subscore</h4>
            </div>
            <div style={{ fontSize: '1.5rem', fontWeight: 700 }}>{report.license_subscore}/100</div>
            <p className="text-muted" style={{ fontSize: '0.8rem', marginTop: '0.25rem' }}>Risk level evaluated from static conflict matrix mapping.</p>
          </div>

          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--color-primary)', marginBottom: '0.5rem' }}>
              <Award size={18} />
              <h4 style={{ margin: 0 }}>Maintenance Subscore</h4>
            </div>
            <div style={{ fontSize: '1.5rem', fontWeight: 700 }}>{report.maintenance_subscore}/100</div>
            <p className="text-muted" style={{ fontSize: '0.8rem', marginTop: '0.25rem' }}>GitHub repository stars, pushes and releases frequency signals.</p>
          </div>
        </div>

        {/* Math explanation */}
        <div className="glass-card mb-4" style={{ background: 'rgba(255,255,255,0.01)', padding: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
            <Percent size={16} style={{ color: 'var(--color-primary)' }} />
            <h4 style={{ margin: 0 }}>Deterministic Scoring Logic Formula</h4>
          </div>
          <p style={{ fontSize: '0.85rem', lineHeight: 1.6 }}>
            Overall score = 0.5 * Vulnerability Subscore + 0.3 * License Subscore + 0.2 * Maintenance Subscore.
            Weights are re-normalized if a category is missing. Direct dependencies get 2x weight multiplier, transitive dependencies get 1x.
          </p>
        </div>

        {/* Audit Log Breakdown */}
        {report.breakdown && (
          <div>
            <h3 style={{ fontSize: '1.2rem', marginBottom: '1rem' }}>Top Contributing Risks Audit Log</h3>
            <div className="table-wrapper">
              <table className="custom-table">
                <thead>
                  <tr>
                    <th>Package Name</th>
                    <th>Version</th>
                    <th>Direct?</th>
                    <th>Vulnerability Subscore</th>
                    <th>License Subscore</th>
                    <th>Weighted Contribution</th>
                  </tr>
                </thead>
                <tbody>
                  {report.breakdown.top_contributing_dependencies?.map((dep: any, idx: number) => (
                    <tr key={idx}>
                      <td style={{ fontWeight: 600 }}>{dep.name}</td>
                      <td>{dep.version}</td>
                      <td>{dep.is_direct ? 'Direct' : 'Transitive'}</td>
                      <td>{dep.vuln_score}</td>
                      <td>{dep.license_score}</td>
                      <td>{dep.weighted_contribution}</td>
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
