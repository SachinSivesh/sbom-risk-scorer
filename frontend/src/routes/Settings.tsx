import { Sliders, Shield, Scale, Cpu } from 'lucide-react';

export default function Settings() {
  return (
    <div className="page-container">
      <h1 className="mb-4">Scoring Engine Policy Settings</h1>
      <p className="text-muted mb-4">
        Review static analysis thresholds, compliance rules, and API endpoints. Policies are currently evaluated server-side.
      </p>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        {/* Risk Categories */}
        <div className="glass-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem', color: 'var(--color-primary)' }}>
            <Sliders size={20} />
            <h3 className="m-0">Risk Score Weights</h3>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', fontSize: '0.9rem' }}>
            <div className="flex justify-between">
              <span>Security Vulnerabilities (CVE/OSV) Weight</span>
              <strong>50%</strong>
            </div>
            <div className="flex justify-between">
              <span>License Compatibility Compliance Weight</span>
              <strong>30%</strong>
            </div>
            <div className="flex justify-between">
              <span>Maintenance & Project Health Weight</span>
              <strong>20%</strong>
            </div>
          </div>
        </div>

        {/* CVSS Thresholds */}
        <div className="glass-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem', color: 'var(--color-primary)' }}>
            <Shield size={20} />
            <h3 className="m-0">Vulnerability Severity Policies</h3>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', fontSize: '0.9rem' }}>
            <div className="flex justify-between">
              <span>Critical Severity CVE (CVSS 9.0+)</span>
              <span>Subscore Contribution: <strong>100</strong></span>
            </div>
            <div className="flex justify-between">
              <span>High Severity CVE (CVSS 7.0 - 8.9)</span>
              <span>Subscore Contribution: <strong>75</strong></span>
            </div>
            <div className="flex justify-between">
              <span>Medium Severity CVE (CVSS 4.0 - 6.9)</span>
              <span>Subscore Contribution: <strong>50</strong></span>
            </div>
            <div className="flex justify-between">
              <span>Low Severity CVE (CVSS 0.1 - 3.9)</span>
              <span>Subscore Contribution: <strong>25</strong></span>
            </div>
            <div className="flex justify-between">
              <span>Unknown Severity (Fallback Default)</span>
              <span>Subscore Contribution: <strong>50</strong></span>
            </div>
          </div>
        </div>

        {/* License Policy */}
        <div className="glass-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem', color: 'var(--color-primary)' }}>
            <Scale size={20} />
            <h3 className="m-0">License Risk Classifications</h3>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', fontSize: '0.9rem' }}>
            <div className="flex justify-between">
              <span>Permissive Licenses (MIT, Apache-2.0, BSD)</span>
              <span className="badge badge-low">NONE RISK (0)</span>
            </div>
            <div className="flex justify-between">
              <span>Weak Copyleft Licenses (LGPL, MPL, EPL)</span>
              <span className="badge badge-medium">LOW RISK (30)</span>
            </div>
            <div className="flex justify-between">
              <span>Commercial/Proprietary Markers</span>
              <span className="badge badge-high">MEDIUM RISK (60)</span>
            </div>
            <div className="flex justify-between">
              <span>Strong Copyleft (GPL, AGPL, SSPL)</span>
              <span className="badge badge-critical">HIGH RISK (90)</span>
            </div>
            <div className="flex justify-between">
              <span>Undeclared License</span>
              <span className="badge badge-critical">HIGH RISK (90)</span>
            </div>
          </div>
        </div>

        {/* System Settings */}
        <div className="glass-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem', color: 'var(--color-primary)' }}>
            <Cpu size={20} />
            <h3 className="m-0">Static Engine Defaults</h3>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', fontSize: '0.9rem' }}>
            <div className="flex justify-between">
              <span>Maximum Dependency Graph Traversal Depth</span>
              <span>50 levels</span>
            </div>
            <div className="flex justify-between">
              <span>Vulnerability Database API</span>
              <span>https://api.osv.dev/v1/querybatch</span>
            </div>
            <div className="flex justify-between">
              <span>GitHub API Cache Expiration (TTL)</span>
              <span>6 Hours</span>
            </div>
            <div className="flex justify-between">
              <span>OSV Vulnerability Cache Expiration (TTL)</span>
              <span>24 Hours</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
