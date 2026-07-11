import { Sliders, Shield, Scale, Cpu } from 'lucide-react';

export default function Settings() {
  return (
    <div className="max-w-7xl mx-auto w-full px-8 py-10">
      
      {/* Page header */}
      <div className="mb-8">
        <h1 className="text-3xl font-extrabold text-sg-navy tracking-tight uppercase">
          Scoring Engine Policy
        </h1>
        <p className="text-gray-500 text-sm mt-1">
          Review the static analysis thresholds, licensing compliance matrices, and threat subscore models evaluated server-side.
        </p>
      </div>

      <div className="space-y-6 max-w-4xl">
        {/* Risk Categories */}
        <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
          <div className="flex items-center gap-2.5 mb-4 text-sg-navy border-b border-gray-100 pb-3">
            <Sliders size={20} className="text-sg-red" />
            <h3 className="text-sm font-bold uppercase tracking-wider">Risk Score Weight Ratios</h3>
          </div>
          <div className="space-y-3.5 text-xs text-gray-600 font-semibold">
            <div className="flex justify-between items-center">
              <span>Security Vulnerabilities (CVE/OSV) Weight</span>
              <span className="font-extrabold text-sg-navy font-mono">50%</span>
            </div>
            <div className="flex justify-between items-center">
              <span>License Compatibility Compliance Weight</span>
              <span className="font-extrabold text-sg-navy font-mono">30%</span>
            </div>
            <div className="flex justify-between items-center">
              <span>Maintenance & Project Health Weight</span>
              <span className="font-extrabold text-sg-navy font-mono">20%</span>
            </div>
          </div>
        </div>

        {/* CVSS Thresholds */}
        <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
          <div className="flex items-center gap-2.5 mb-4 text-sg-navy border-b border-gray-100 pb-3">
            <Shield size={20} className="text-sg-red" />
            <h3 className="text-sm font-bold uppercase tracking-wider">Vulnerability Severity Weights</h3>
          </div>
          <div className="space-y-3.5 text-xs text-gray-600 font-semibold">
            <div className="flex justify-between items-center">
              <span>Critical Severity CVE (CVSS 9.0+)</span>
              <span>Subscore Impact: <strong className="font-extrabold text-sg-navy font-mono">100</strong></span>
            </div>
            <div className="flex justify-between items-center">
              <span>High Severity CVE (CVSS 7.0 - 8.9)</span>
              <span>Subscore Impact: <strong className="font-extrabold text-sg-navy font-mono">75</strong></span>
            </div>
            <div className="flex justify-between items-center">
              <span>Medium Severity CVE (CVSS 4.0 - 6.9)</span>
              <span>Subscore Impact: <strong className="font-extrabold text-sg-navy font-mono">50</strong></span>
            </div>
            <div className="flex justify-between items-center">
              <span>Low Severity CVE (CVSS 0.1 - 3.9)</span>
              <span>Subscore Impact: <strong className="font-extrabold text-sg-navy font-mono">25</strong></span>
            </div>
            <div className="flex justify-between items-center">
              <span>Unknown Severity (Fallback Default)</span>
              <span>Subscore Impact: <strong className="font-extrabold text-sg-navy font-mono">50</strong></span>
            </div>
          </div>
        </div>

        {/* License Policy */}
        <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
          <div className="flex items-center gap-2.5 mb-4 text-sg-navy border-b border-gray-100 pb-3">
            <Scale size={20} className="text-sg-red" />
            <h3 className="text-sm font-bold uppercase tracking-wider">License Risk Classifications</h3>
          </div>
          <div className="space-y-3.5 text-xs text-gray-600 font-semibold">
            <div className="flex justify-between items-center">
              <span>Permissive Licenses (MIT, Apache-2.0, BSD)</span>
              <span className="inline-block rounded bg-green-50 px-2 py-0.5 font-extrabold uppercase text-[10px] text-sg-success border border-sg-success/30">NONE RISK (0)</span>
            </div>
            <div className="flex justify-between items-center">
              <span>Weak Copyleft Licenses (LGPL, MPL, EPL)</span>
              <span className="inline-block rounded bg-yellow-50 px-2 py-0.5 font-extrabold uppercase text-[10px] text-yellow-600 border border-yellow-500/30">LOW RISK (30)</span>
            </div>
            <div className="flex justify-between items-center">
              <span>Commercial/Proprietary Markers</span>
              <span className="inline-block rounded bg-amber-50 px-2 py-0.5 font-extrabold uppercase text-[10px] text-sg-warning border border-sg-warning/30">MEDIUM RISK (60)</span>
            </div>
            <div className="flex justify-between items-center">
              <span>Strong Copyleft (GPL, AGPL, SSPL)</span>
              <span className="inline-block rounded bg-red-50 px-2 py-0.5 font-extrabold uppercase text-[10px] text-sg-danger border border-sg-danger/30">HIGH RISK (90)</span>
            </div>
            <div className="flex justify-between items-center">
              <span>Undeclared License</span>
              <span className="inline-block rounded bg-red-50 px-2 py-0.5 font-extrabold uppercase text-[10px] text-sg-danger border border-sg-danger/30">HIGH RISK (90)</span>
            </div>
          </div>
        </div>

        {/* System Settings */}
        <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
          <div className="flex items-center gap-2.5 mb-4 text-sg-navy border-b border-gray-100 pb-3">
            <Cpu size={20} className="text-sg-red" />
            <h3 className="text-sm font-bold uppercase tracking-wider">Static Engine Threshold Defaults</h3>
          </div>
          <div className="space-y-3.5 text-xs text-gray-600 font-semibold">
            <div className="flex justify-between items-center">
              <span>Maximum Dependency Graph Traversal Depth</span>
              <span className="font-mono text-sg-navy">50 levels</span>
            </div>
            <div className="flex justify-between items-center">
              <span>Vulnerability Database API</span>
              <span className="font-mono text-gray-400">https://api.osv.dev/v1/querybatch</span>
            </div>
            <div className="flex justify-between items-center">
              <span>GitHub API Cache Expiration (TTL)</span>
              <span className="font-mono text-sg-navy">6 Hours</span>
            </div>
            <div className="flex justify-between items-center">
              <span>OSV Vulnerability Cache Expiration (TTL)</span>
              <span className="font-mono text-sg-navy">24 Hours</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
