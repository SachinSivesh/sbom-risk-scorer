import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { useApplication } from '../hooks/useApplications';
import { useRiskReport, useAIReport } from '../hooks/useRiskReport';
import { applicationsApi } from '../services/apiClient';
import { useUiStore } from '../store/uiStore';
import {
  Upload,
  ShieldAlert,
  Sparkles,
  ArrowLeft,
  Loader2,
  AlertTriangle,
  Info,
  CheckCircle,
  ExternalLink,
  TrendingUp,
  ChevronDown,
  ChevronUp,
  AlertOctagon,
  FileText,
  Layers,
  Activity,
  Archive,
  AlertCircle,
  Search
} from 'lucide-react';
import { BarChart, Bar, Cell, PieChart, Pie, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend, LineChart, Line } from 'recharts';
import DependencyGraphView from '../components/graph/DependencyGraphView';

export default function ApplicationDetail() {
  const { id } = useParams<{ id: string }>();
  const appId = id || '';

  const {
    setCurrentSbomId,
    setCurrentApplicationName,
    setSelectedApplicationId,
    setIsUploadOpen
  } = useUiStore();

  // Get application metadata & SBOM list
  const { data: application, isLoading: appLoading, error: appError } = useApplication(appId);

  // Selected SBOM ID state - default to first completed SBOM
  const [selectedSbomId, setSelectedSbomId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'summary' | 'vulnerabilities' | 'dependencies' | 'licenses' | 'graph' | 'trend'>('summary');
  
  // Vulnerabilities table state
  const [vulnSearch, setVulnSearch] = useState('');
  const [vulnSeverityFilter, setVulnSeverityFilter] = useState<string>('ALL');
  const [vulnSortField, setVulnSortField] = useState<'id' | 'package' | 'severity'>('severity');
  const [vulnSortOrder, setVulnSortOrder] = useState<'asc' | 'desc'>('desc');
  const [vulnPage, setVulnPage] = useState(1);
  const vulnPageSize = 8;

  // AI accordion state
  const [expandedActionIdx, setExpandedActionIdx] = useState<number | null>(0);

  const formatAppName = (name: string) => {
    if (!name) return '';
    return name
      .replace(/([a-z0-9])([A-Z])/g, '$1 $2')
      .replace(/([A-Z])([A-Z][a-z])/g, '$1 $2')
      .trim();
  };

  const formatSummaryText = (text: string) => {
    if (!text) return null;
    
    // Replace CamelCase dataset names with spaced names
    const cleanedText = text
      .replace(/ComplianceEngine/g, 'Compliance Engine')
      .replace(/PaymentService/g, 'Payment Service')
      .replace(/CustomerPortal/g, 'Customer Portal')
      .replace(/AnalyticsDashboard/g, 'Analytics Dashboard')
      .replace(/InternalAPI/g, 'Internal API')
      .replace(/HRPortal/g, 'HR Portal')
      .replace(/MobileBackend/g, 'Mobile Backend')
      .replace(/DevToolkit/g, 'Dev Toolkit')
      .replace(/NotificationService/g, 'Notification Service')
      .replace(/VendorGateway/g, 'Vendor Gateway');

    const lines = cleanedText.split('\n');
    return (
      <div className="space-y-2.5 font-sans leading-relaxed text-gray-600">
        {lines.map((line, idx) => {
          const trimmed = line.trim();
          if (!trimmed) return <div key={idx} className="h-1" />;
          
          const parseInline = (str: string) => {
            const parts = str.split(/(\*\*.*?\*\*|'.*?')/g);
            return parts.map((part, pIdx) => {
              if (part.startsWith('**') && part.endsWith('**')) {
                return (
                  <strong key={pIdx} className="font-bold text-sg-navy text-xs">
                    {part.slice(2, -2)}
                  </strong>
                );
              }
              if (part.startsWith("'") && part.endsWith("'")) {
                return (
                  <code key={pIdx} className="bg-red-50 text-sg-red font-extrabold font-mono px-1 py-0.5 rounded border border-sg-red/10 text-[10px]">
                    {part.slice(1, -1)}
                  </code>
                );
              }
              return part;
            });
          };

          if (trimmed.startsWith('### ')) {
            return (
              <h4 key={idx} className="text-xs font-extrabold text-sg-navy mt-4 mb-1.5 uppercase tracking-wider border-b border-gray-100 pb-1 shrink-0">
                {trimmed.substring(4)}
              </h4>
            );
          }
          
          if (trimmed.startsWith('* ') || trimmed.startsWith('- ')) {
            const content = trimmed.substring(2);
            return (
              <div key={idx} className="flex items-start gap-2 text-xs pl-2.5 mt-1 text-gray-600">
                <span className="text-sg-red font-bold mt-0.5">&bull;</span>
                <span>{parseInline(content)}</span>
              </div>
            );
          }
          
          const numMatch = trimmed.match(/^(\d+)\.\s+(.*)/);
          if (numMatch) {
            return (
              <div key={idx} className="flex items-start gap-2 text-xs pl-2.5 mt-1 text-gray-600">
                <span className="text-sg-red font-bold font-mono">{numMatch[1]}.</span>
                <span>{parseInline(numMatch[2])}</span>
              </div>
            );
          }
          
          return (
            <p key={idx} className="text-xs text-gray-600 leading-relaxed">
              {parseInline(trimmed)}
            </p>
          );
        })}
      </div>
    );
  };

  // Fetch trend data
  const { data: trendData, isLoading: trendLoading } = useQuery<any[]>({
    queryKey: ['trend', appId],
    queryFn: () => applicationsApi.trend(appId),
    enabled: !!appId,
  });

  // Track active application context in global UI store
  useEffect(() => {
    if (application) {
      setCurrentApplicationName(application.name);
      setSelectedApplicationId(application.id);
    }
    return () => {
      setCurrentApplicationName(null);
      setSelectedApplicationId(null);
      setCurrentSbomId(null);
    };
  }, [application, setCurrentApplicationName, setSelectedApplicationId, setCurrentSbomId]);

  // Automatically select the latest completed SBOM on load
  useEffect(() => {
    if (application?.sboms && application.sboms.length > 0) {
      const completedSbom = application.sboms.find(s => s.status === 'completed');
      if (completedSbom && !selectedSbomId) {
        setSelectedSbomId(completedSbom.id);
        setCurrentSbomId(completedSbom.id);
      }
    }
  }, [application, selectedSbomId, setCurrentSbomId]);

  // Fetch Risk Report and AI summary for the selected SBOM
  const { data: report, isLoading: reportLoading, error: reportError, refetch: refetchReport } = useRiskReport(selectedSbomId || '');
  const { data: aiReport, isLoading: aiLoading } = useAIReport(selectedSbomId || '');

  // Synchronize active SBOM with PDF export button context
  useEffect(() => {
    if (selectedSbomId) {
      setCurrentSbomId(selectedSbomId);
    }
  }, [selectedSbomId, setCurrentSbomId]);

  if (appLoading) {
    return (
      <div className="flex h-[calc(100vh-4rem)] items-center justify-center bg-sg-bg">
        <Loader2 size={36} className="animate-spin text-sg-red" />
      </div>
    );
  }

  if (appError || !application) {
    return (
      <div className="max-w-7xl mx-auto w-full px-8 py-10">
        <div className="bg-white border border-gray-200 rounded-lg p-12 text-center text-sg-danger shadow-sm">
          <ShieldAlert size={48} className="mx-auto mb-4 text-sg-red" />
          <h3 className="text-lg font-bold">Application Asset Not Found</h3>
          <p className="text-gray-500 text-sm mt-1">The requested application record could not be loaded.</p>
          <Link to="/" className="inline-flex items-center gap-2 rounded-md bg-sg-navy px-4 py-2 text-xs font-bold text-white hover:bg-sg-navy/90 no-underline mt-6">
            <ArrowLeft size={14} /> Back to Portfolio
          </Link>
        </div>
      </div>
    );
  }

  // ── Metrics Computations ──────────────────────────────────────
  const allDeps = report?.dependencies || [];
  const allVulns = allDeps.flatMap(d => d.vulnerabilities.map(v => ({ ...v, packageName: d.name, packageVersion: d.version })));
  
  const criticalCount = allVulns.filter(v => v.severity === 'CRITICAL').length;
  const highCount = allVulns.filter(v => v.severity === 'HIGH').length;
  const mediumCount = allVulns.filter(v => v.severity === 'MEDIUM').length;
  const lowCount = allVulns.filter(v => v.severity === 'LOW').length;

  const licenseViolationsCount = allDeps.filter(d => d.license_risk === 'HIGH').length;
  
  // Maintenance signals indicators
  const deprecatedCount = allDeps.filter(d => d.maintenance_status === 'DEPRECATED' || d.maintenance_status === 'INACTIVE').length;
  const archivedCount = allDeps.filter(d => d.maintenance_status === 'ARCHIVED').length;

  // ── Color mappings and scores helpers ─────────────────────────
  const score = report?.overall_score ?? null;

  const getScoreBadgeClass = (s: number | null) => {
    if (s === null) return 'bg-gray-100 text-gray-500 border border-gray-200';
    if (s >= 75) return 'bg-red-100 text-sg-danger border border-sg-danger/20';
    if (s >= 50) return 'bg-amber-100 text-sg-warning border border-sg-warning/20';
    if (s >= 25) return 'bg-yellow-100 text-yellow-700 border border-yellow-500/20';
    return 'bg-green-100 text-sg-success border border-sg-success/20';
  };

  const getScoreStrokeColor = (s: number | null) => {
    if (s === null) return '#CBD5E1';
    if (s >= 75) return '#EF4444'; // Danger
    if (s >= 50) return '#F59E0B'; // Warning
    if (s >= 25) return '#EAB308'; // Medium Warning
    return '#22C55E'; // Success
  };

  // ── Recharts Chart Models ─────────────────────────────────────
  const barChartData = report ? [
    { name: 'Security Score', value: report.vulnerability_subscore, fill: getScoreStrokeColor(report.vulnerability_subscore) },
    { name: 'License Compliance', value: report.license_subscore, fill: getScoreStrokeColor(report.license_subscore) },
    { name: 'Maintenance Health', value: report.maintenance_subscore, fill: getScoreStrokeColor(report.maintenance_subscore) }
  ] : [];

  const pieChartData = [
    { name: 'Critical', value: criticalCount, fill: '#EF4444' },
    { name: 'High', value: highCount, fill: '#F59E0B' },
    { name: 'Medium', value: mediumCount, fill: '#EAB308' },
    { name: 'Low', value: lowCount, fill: '#22C55E' }
  ].filter(item => item.value > 0);

  // ── Vulnerability Sorting and Filtering ────────────────────────
  const filteredVulns = allVulns.filter(v => {
    const matchesSearch = v.vuln_id.toLowerCase().includes(vulnSearch.toLowerCase()) || v.packageName.toLowerCase().includes(vulnSearch.toLowerCase()) || v.summary.toLowerCase().includes(vulnSearch.toLowerCase());
    const matchesSeverity = vulnSeverityFilter === 'ALL' || v.severity === vulnSeverityFilter;
    return matchesSearch && matchesSeverity;
  }).sort((a, b) => {
    let comp = 0;
    if (vulnSortField === 'id') comp = a.vuln_id.localeCompare(b.vuln_id);
    else if (vulnSortField === 'package') comp = a.packageName.localeCompare(b.packageName);
    else {
      const severityWeights = { CRITICAL: 4, HIGH: 3, MEDIUM: 2, LOW: 1, UNKNOWN: 0 };
      comp = (severityWeights[a.severity] || 0) - (severityWeights[b.severity] || 0);
    }
    return vulnSortOrder === 'asc' ? comp : -comp;
  });

  const totalVulnPages = Math.ceil(filteredVulns.length / vulnPageSize);
  const pagedVulns = filteredVulns.slice((vulnPage - 1) * vulnPageSize, vulnPage * vulnPageSize);

  // SVG Gauge variables
  const radius = 60;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - ((score ?? 0) / 100) * circumference;

  return (
    <div className="max-w-7xl mx-auto w-full px-8 py-10 print:px-0 print:py-0">
      
      {/* Back button */}
      <Link to="/" className="inline-flex items-center gap-1.5 rounded-md border border-gray-200 bg-white px-4 py-2 text-xs font-bold text-gray-500 hover:bg-gray-50 no-underline mb-6 shadow-sm print:hidden">
        <ArrowLeft size={14} /> BACK TO PORTFOLIO
      </Link>

      {/* Main Header Card */}
      <div className="bg-white border border-gray-200 rounded-lg p-8 flex flex-col md:flex-row justify-between items-start md:items-center gap-6 mb-8 shadow-sm">
        <div>
          <h1 className="text-3xl font-extrabold text-sg-navy tracking-tight uppercase print:text-xl">
            {formatAppName(application.name)}
          </h1>
          <p className="text-gray-500 text-sm mt-1 max-w-3xl leading-relaxed">
            {application.description || 'No description configured for this software repository.'}
          </p>
        </div>
        <button
          onClick={() => setIsUploadOpen(true)}
          className="inline-flex items-center gap-2 rounded-md bg-sg-red px-5 py-2.5 text-sm font-bold text-white shadow-sm transition-all hover:bg-red-600 focus:outline-none focus:ring-2 focus:ring-sg-red/30 active:scale-95 print:hidden"
        >
          <Upload size={16} /> UPLOAD NEW SBOM
        </button>
      </div>

      {application.sboms.length === 0 ? (
        <div className="bg-white border border-gray-200 rounded-lg p-16 text-center shadow-sm">
          <Upload size={48} className="mx-auto mb-4 text-sg-navy/30" />
          <h2 className="text-xl font-bold text-sg-navy">No SBOM Uploaded</h2>
          <p className="text-gray-500 text-sm max-w-md mx-auto mt-2 mb-6">
            Upload a CycloneDX or SPDX JSON SBOM schema file to run vulnerability, license compliance, and maintenance analysis.
          </p>
          <button
            onClick={() => setIsUploadOpen(true)}
            className="inline-flex items-center gap-2 rounded-md bg-sg-red px-6 py-3 text-sm font-bold text-white shadow-sm hover:bg-red-600 transition-all"
          >
            <Upload size={16} /> UPLOAD FIRST SBOM
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          
          {/* 1. LEFT SIDEBAR PANEL (1 Column) */}
          <div className="lg:col-span-1 space-y-6 print:hidden">
            
            {/* Circular Gauge Card */}
            <div className="bg-white border border-gray-200 rounded-lg p-6 text-center shadow-sm flex flex-col items-center">
              <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-4">Overall Risk Score</h3>
              <div className="relative w-36 h-36 flex items-center justify-center mb-4">
                <svg className="w-full h-full transform -rotate-90">
                  <circle cx="72" cy="72" r={radius} fill="transparent" stroke="#E2E8F0" strokeWidth="12" />
                  <circle
                    cx="72"
                    cy="72"
                    r={radius}
                    fill="transparent"
                    stroke={getScoreStrokeColor(score)}
                    strokeWidth="12"
                    strokeDasharray={circumference}
                    strokeDashoffset={score !== null ? strokeDashoffset : circumference}
                    strokeLinecap="round"
                    className="transition-all duration-1000 ease-out"
                  />
                </svg>
                <div className="absolute flex flex-col items-center justify-center">
                  <span className="text-4xl font-extrabold tracking-tighter text-sg-navy font-mono">
                    {score !== null ? score : '—'}
                  </span>
                  <span className="text-[9px] font-bold text-gray-400 uppercase tracking-widest mt-0.5">RISK INDEX</span>
                </div>
              </div>
              <span className={`inline-block rounded px-4 py-1.5 text-xs font-black uppercase tracking-wider border shadow-xs ${getScoreBadgeClass(score)}`}>
                {report?.category ? `${report.category} RISK` : 'UNKNOWN'}
              </span>
            </div>

            {/* Policy Compliance Gate Card */}
            {report && report.breakdown && report.breakdown.policy_evaluation && (
              <div className={`border rounded-lg p-5 shadow-sm flex flex-col items-center text-center ${
                report.breakdown.policy_evaluation.status === 'PASSED'
                  ? 'bg-green-50/40 border-green-200 text-green-800'
                  : 'bg-red-50/40 border-red-200 text-red-800'
              }`}>
                <h3 className="text-xs font-bold uppercase tracking-wider mb-2 text-gray-400">Compliance Status</h3>
                <div className="flex items-center gap-1.5 mb-2">
                  <span className={`h-2.5 w-2.5 rounded-full ${
                    report.breakdown.policy_evaluation.status === 'PASSED' ? 'bg-green-500 animate-pulse' : 'bg-red-500 animate-pulse'
                  }`} />
                  <span className="text-xs font-extrabold uppercase tracking-tight">
                    {report.breakdown.policy_evaluation.status === 'PASSED' ? 'PASSED (SECURE)' : 'DEPLOYMENT REJECTED'}
                  </span>
                </div>
                
                {report.breakdown.policy_evaluation.violations.length > 0 ? (
                  <div className="w-full text-left space-y-1.5 mt-2">
                    <span className="text-[9px] font-black uppercase tracking-widest text-red-600 block mb-1">Gate Failures:</span>
                    {report.breakdown.policy_evaluation.violations.map((v, i) => (
                      <div key={i} className="text-[10px] text-red-700 bg-red-100/30 p-2 rounded border border-red-100/60 flex items-start gap-1 font-semibold leading-relaxed">
                        <span className="text-red-500 font-bold">•</span>
                        <span>{v.description}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-[10px] text-green-700 font-semibold leading-relaxed mt-1">
                    All enterprise security and open-source license governance policies are fully satisfied.
                  </p>
                )}
              </div>
            )}

            {/* Risk Sub-dimensions list */}
            {report && (
              <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm space-y-4">
                <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider border-b border-gray-100 pb-3">Score Breakdown</h3>
                
                {[
                  { name: 'Vulnerability Risk', value: report.vulnerability_subscore },
                  { name: 'License Compliance', value: report.license_subscore },
                  { name: 'Maintenance Health', value: report.maintenance_subscore }
                ].map((item) => (
                  <div key={item.name} className="space-y-1.5">
                    <div className="flex justify-between items-center text-xs">
                      <span className="font-semibold text-gray-500">{item.name}</span>
                      <span className="font-bold text-sg-navy">{item.value}/100</span>
                    </div>
                    <div className="h-2 w-full bg-gray-100 rounded-full overflow-hidden">
                      <div className="h-full rounded-full transition-all duration-500" style={{ width: `${item.value}%`, backgroundColor: getScoreStrokeColor(item.value) }} />
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Explainable Contributions block */}
            {report && report.breakdown && report.breakdown.contributions && (
              <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm space-y-3">
                <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider border-b border-gray-100 pb-3">Risk Contributions</h3>
                <div className="space-y-2 text-xs font-semibold text-gray-500">
                  <div className="flex justify-between items-center">
                    <span>Security Vulnerabilities:</span>
                    <span className="text-sg-navy font-bold font-mono">+{report.breakdown.contributions.vulnerability}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>License Risk:</span>
                    <span className="text-sg-navy font-bold font-mono">+{report.breakdown.contributions.license}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>Maintenance Health:</span>
                    <span className="text-sg-navy font-bold font-mono">+{report.breakdown.contributions.maintenance}</span>
                  </div>
                  <div className="flex justify-between items-center pb-2 border-b border-dashed">
                    <span>Business Criticality:</span>
                    <span className={`${
                      report.breakdown.contributions.business_criticality >= 0 ? 'text-sg-red' : 'text-green-600'
                    } font-bold font-mono`}>
                      {report.breakdown.contributions.business_criticality >= 0 ? '+' : ''}
                      {report.breakdown.contributions.business_criticality}
                    </span>
                  </div>
                  <div className="flex justify-between items-center pt-1 text-xs font-extrabold">
                    <span className="text-sg-navy uppercase">Total Risk Index:</span>
                    <span className="text-sg-red font-mono text-sm">{score}</span>
                  </div>
                </div>
              </div>
            )}

            {/* SBOM Artifact Version History */}
            <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
              <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider border-b border-gray-100 pb-3 mb-4">Uploaded Artifacts</h3>
              <div className="space-y-2">
                {application.sboms.map((sbom) => {
                  const isActive = selectedSbomId === sbom.id;
                  return (
                    <button
                      key={sbom.id}
                      onClick={() => {
                        setSelectedSbomId(sbom.id);
                        refetchReport();
                      }}
                      className={`w-full text-left p-3.5 rounded-md border text-xs flex flex-col justify-between transition-all cursor-pointer ${
                        isActive
                          ? 'border-sg-red bg-red-50/10 text-sg-navy shadow-xs font-extrabold'
                          : 'border-gray-200 bg-white hover:bg-gray-50 text-gray-400 font-semibold'
                      }`}
                    >
                      <div className="flex justify-between items-start w-full gap-2 mb-2">
                        <span className={`font-bold truncate ${isActive ? 'text-sg-navy font-extrabold' : 'text-gray-500 font-semibold'}`} title={sbom.original_filename}>
                          {sbom.original_filename}
                        </span>
                        {sbom.status !== 'completed' && (
                          <span className="inline-block rounded bg-yellow-50 px-1.5 py-0.5 text-[8px] font-bold text-sg-warning border border-sg-warning/20 shrink-0">
                            {sbom.status.toUpperCase()}
                          </span>
                        )}
                      </div>
                      <div className="grid grid-cols-2 gap-y-1.5 gap-x-2 text-[10px] text-gray-400 mt-2 border-t border-gray-100/50 pt-2 font-medium">
                        <div>Format: <span className="font-bold text-gray-500 uppercase">{sbom.format}</span></div>
                        <div className="text-right">Components: <span className="font-bold text-gray-500 font-mono">{sbom.component_count || '—'}</span></div>
                        <div className="col-span-2">Uploaded: <span className="font-bold text-gray-500">{new Date(sbom.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}</span></div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

          </div>

          {/* 2. RIGHT MAIN PANELS (3 Columns) */}
          <div className="lg:col-span-3 space-y-6">
            
            {/* Tab Swapping Header */}
            <div className="flex border-b border-gray-200 overflow-x-auto print:hidden">
              {[
                { key: 'summary', name: 'Executive Summary' },
                { key: 'vulnerabilities', name: `CVE Vulnerabilities (${allVulns.length})` },
                { key: 'dependencies', name: `Dependencies Tree (${allDeps.length})` },
                { key: 'licenses', name: 'License Audits' },
                { key: 'graph', name: 'Graph Explorer' },
                { key: 'trend', name: 'Score History' }
              ].map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key as any)}
                  className={`px-5 py-3 font-bold text-xs border-b-2 whitespace-nowrap transition-all ${
                    activeTab === tab.key
                      ? 'border-sg-red text-sg-red'
                      : 'border-transparent text-gray-400 hover:text-sg-navy'
                  }`}
                >
                  {tab.name}
                </button>
              ))}
            </div>

            {/* TAB PANELS */}
            {reportLoading ? (
              <div className="bg-white border border-gray-200 rounded-lg p-16 text-center shadow-sm flex items-center justify-center h-96">
                <Loader2 size={36} className="animate-spin text-sg-red" />
              </div>
            ) : reportError ? (
              <div className="bg-white border border-gray-200 rounded-lg p-16 text-center text-sg-danger shadow-sm">
                <AlertCircle size={48} className="mx-auto mb-4 text-sg-red" />
                <h3 className="text-lg font-bold">Report Load Failed</h3>
                <p className="text-gray-500 text-sm mt-1">Vulnerability assessment metrics are currently unavailable.</p>
              </div>
            ) : (
              <>
                {/* A. Executive Summary Tab */}
                {activeTab === 'summary' && (
                  <div className="space-y-6">
                    
                    {/* Enterprise KPI Metrics Grid (Section 13) */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      {[
                        { title: 'Critical Vulns', value: criticalCount, icon: AlertOctagon, color: criticalCount > 0 ? 'text-sg-danger bg-red-50/50' : 'text-gray-400 bg-gray-50' },
                        { title: 'High Vulns', value: highCount, icon: ShieldAlert, color: highCount > 0 ? 'text-sg-warning bg-amber-50/50' : 'text-gray-400 bg-gray-50' },
                        { title: 'Medium Vulns', value: mediumCount, icon: AlertTriangle, color: mediumCount > 0 ? 'text-yellow-600 bg-yellow-50/50' : 'text-gray-400 bg-gray-50' },
                        { title: 'Low Vulns', value: lowCount, icon: Info, color: lowCount > 0 ? 'text-sg-success bg-green-50/50' : 'text-gray-400 bg-gray-50' },
                        { title: 'Total Components', value: allDeps.length, icon: Layers, color: 'text-sg-navy bg-gray-50' },
                        { title: 'License Conflicts', value: licenseViolationsCount, icon: FileText, color: licenseViolationsCount > 0 ? 'text-sg-danger bg-red-50/50' : 'text-gray-400 bg-gray-50' },
                        { title: 'Deprecated Packages', value: deprecatedCount, icon: Activity, color: deprecatedCount > 0 ? 'text-sg-warning bg-amber-50/50' : 'text-gray-400 bg-gray-50' },
                        { title: 'Archived Repos', value: archivedCount, icon: Archive, color: archivedCount > 0 ? 'text-orange-600 bg-orange-50/50' : 'text-gray-400 bg-gray-50' }
                      ].map((card, idx) => (
                        <div key={idx} className="bg-white border border-gray-200 rounded-lg p-5 flex items-center gap-4 shadow-sm">
                          <div className={`p-2.5 rounded-md ${card.color} shrink-0`}>
                            <card.icon size={20} />
                          </div>
                          <div>
                            <span className="block text-[10px] font-bold uppercase text-gray-400 tracking-wider">{card.title}</span>
                            <span className="text-xl font-extrabold text-sg-navy font-mono mt-0.5">{card.value}</span>
                          </div>
                        </div>
                      ))}
                    </div>

                    {/* Chart Visualizations Row */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      
                      {/* Sub-scores horizontal bar chart */}
                      <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
                        <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-4 border-b border-gray-100 pb-3">Sub-Scores Risk breakdown</h3>
                        <div className="h-64">
                          <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={barChartData} layout="vertical" margin={{ left: 10, right: 30, top: 10, bottom: 10 }}>
                              <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                              <XAxis type="number" domain={[0, 100]} stroke="#94A3B8" style={{ fontSize: '10px' }} />
                              <YAxis dataKey="name" type="category" stroke="#94A3B8" style={{ fontSize: '10px' }} width={120} />
                              <Tooltip cursor={{ fill: 'rgba(0,0,0,0.01)' }} />
                              <Bar dataKey="value" radius={[0, 4, 4, 0]} barSize={16}>
                                {barChartData.map((entry, index) => (
                                  <Cell key={`cell-${index}`} fill={entry.fill} />
                                ))}
                              </Bar>
                            </BarChart>
                          </ResponsiveContainer>
                        </div>
                      </div>

                      {/* Pie chart vulnerability distribution */}
                      <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
                        <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-4 border-b border-gray-100 pb-3">Vulnerabilities Severity Distribution</h3>
                        <div className="h-64 flex items-center justify-center">
                          {pieChartData.length > 0 ? (
                            <ResponsiveContainer width="100%" height="100%">
                              <PieChart>
                                <Pie
                                  data={pieChartData}
                                  cx="50%"
                                  cy="50%"
                                  innerRadius={50}
                                  outerRadius={75}
                                  paddingAngle={3}
                                  dataKey="value"
                                >
                                  {pieChartData.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={entry.fill} />
                                  ))}
                                </Pie>
                                <Tooltip formatter={(val) => [`${val} CVEs`, 'Count']} />
                                <Legend verticalAlign="bottom" height={36} iconType="circle" wrapperStyle={{ fontSize: '10px' }} />
                              </PieChart>
                            </ResponsiveContainer>
                          ) : (
                            <div className="text-center text-xs text-gray-400 py-12 flex flex-col items-center justify-center gap-2">
                              <CheckCircle size={24} className="text-sg-success" />
                              <span className="font-bold text-sg-navy">No known vulnerabilities detected.</span>
                              <span>This application currently has a healthy vulnerability profile.</span>
                            </div>
                          )}
                        </div>
                      </div>

                    </div>

                    {/* AI Executive Summary Card */}
                    <div className="bg-white border border-gray-200 border-l-4 border-l-sg-red rounded-lg p-6 shadow-sm">
                      <div className="flex items-center gap-2 text-sg-red mb-4">
                        <Sparkles size={18} />
                        <h3 className="text-sm font-bold uppercase tracking-wider">AI Executive summary (Gemini)</h3>
                      </div>
                      
                      {aiLoading ? (
                        <div className="space-y-2">
                          <div className="shimmer h-4 w-11/12 rounded" />
                          <div className="shimmer h-4 w-full rounded" />
                          <div className="shimmer h-4 w-2/3 rounded" />
                        </div>
                      ) : aiReport ? (
                        <div className="space-y-6">
                          <p className="text-sm text-sg-navy leading-relaxed font-sans border-b border-gray-100 pb-5">
                            {formatSummaryText(aiReport.summary)}
                          </p>

                          {/* AI Remediation Accordion (Issue, Root cause, Recommended upgrade, Steps, Risk reduction) */}
                          <div className="space-y-3 mt-6">
                            <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Detailed Remediation Playbooks</h4>
                            {aiReport.top_actions.map((action, idx) => {
                              const isExpanded = expandedActionIdx === idx;
                              return (
                                <div key={idx} className="border border-gray-200 rounded-md overflow-hidden bg-gray-50/50">
                                  {/* Accordion Trigger */}
                                  <button
                                    onClick={() => setExpandedActionIdx(isExpanded ? null : idx)}
                                    className="w-full flex justify-between items-center p-4 text-left font-bold text-xs text-sg-navy hover:bg-gray-50 transition-all cursor-pointer"
                                  >
                                    <div className="flex items-center gap-2">
                                      <span className={`inline-block rounded px-2 py-0.5 text-[9px] font-extrabold ${
                                        action.priority === 'HIGH' ? 'bg-red-100 text-sg-danger' : action.priority === 'MEDIUM' ? 'bg-amber-100 text-sg-warning' : 'bg-green-100 text-sg-success'
                                      }`}>
                                        {action.priority} PRIORITY
                                      </span>
                                      <span className="truncate max-w-[280px] md:max-w-md">{action.title}</span>
                                    </div>
                                    {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                                  </button>

                                  {/* Accordion Content */}
                                  {isExpanded && (
                                    <div className="p-5 bg-white border-t border-gray-100 text-xs space-y-4 leading-relaxed text-gray-600">
                                      <div>
                                        <span className="block font-bold text-sg-navy text-[10px] uppercase tracking-wider mb-1">Issue Overview</span>
                                        <p>{action.description}</p>
                                      </div>
                                      
                                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        <div>
                                          <span className="block font-bold text-sg-navy text-[10px] uppercase tracking-wider mb-1">Root Cause Analysis</span>
                                          <p>Vulnerability signatures detected in upstream SBOM dependencies matching threat scoring parameters.</p>
                                        </div>
                                        <div>
                                          <span className="block font-bold text-sg-navy text-[10px] uppercase tracking-wider mb-1">Risk Reduction</span>
                                          <p>Updating components will remove direct CVE signatures and remediate subscore exposure.</p>
                                        </div>
                                      </div>

                                      <div>
                                        <span className="block font-bold text-sg-navy text-[10px] uppercase tracking-wider mb-1.5">Recommended Actions</span>
                                        <ol className="list-decimal pl-4 space-y-1.5 font-mono text-[11px] text-gray-500 bg-gray-50 p-3.5 rounded border border-gray-100">
                                          <li>Verify build compatibility with upgraded libraries.</li>
                                          <li>Execute: <code className="bg-gray-200 px-1 py-0.5 rounded font-bold text-sg-navy">npm install {action.title.split(' ')[1] || 'dependency'}@latest</code></li>
                                          <li>Deploy code changes to secure sandbox environment to run automated regressions.</li>
                                        </ol>
                                      </div>
                                    </div>
                                  )}
                                </div>
                              );
                            })}
                          </div>

                        </div>
                      ) : (
                        <p className="text-xs text-gray-400">Security summaries not computed.</p>
                      )}
                    </div>

                  </div>
                )}

                {/* B. Vulnerabilities Tab */}
                {activeTab === 'vulnerabilities' && (
                  <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm space-y-4">
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-2">
                      <h3 className="text-base font-bold text-sg-navy">CVE Vulnerabilities Directory</h3>
                      
                      <div className="flex items-center gap-3">
                        <div className="relative w-48">
                          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                          <input
                            type="text"
                            placeholder="Filter by CVE..."
                            value={vulnSearch}
                            onChange={(e) => { setVulnSearch(e.target.value); setVulnPage(1); }}
                            className="w-full pl-8 pr-3 py-1.5 border border-gray-200 rounded text-xs focus:outline-none focus:border-sg-red"
                          />
                        </div>
                        <select
                          value={vulnSeverityFilter}
                          onChange={(e) => { setVulnSeverityFilter(e.target.value); setVulnPage(1); }}
                          className="px-3 py-1.5 border border-gray-200 rounded text-xs text-sg-navy bg-white focus:outline-none focus:border-sg-red"
                        >
                          <option value="ALL">All Severities</option>
                          <option value="CRITICAL">Critical</option>
                          <option value="HIGH">High</option>
                          <option value="MEDIUM">Medium</option>
                          <option value="LOW">Low</option>
                        </select>
                      </div>
                    </div>

                    {filteredVulns.length === 0 ? (
                      <div className="text-center py-16 text-gray-400 flex flex-col items-center justify-center gap-3">
                        <CheckCircle size={48} className="text-sg-success" />
                        <h4 className="font-bold text-sg-navy text-sm">No known vulnerabilities detected.</h4>
                        <p className="text-xs text-gray-400 max-w-sm">This application currently has a healthy vulnerability profile with zero active CVE threats.</p>
                      </div>
                    ) : (
                      <>
                        <div className="overflow-x-auto border border-gray-200 rounded-md">
                          <table className="min-w-full divide-y divide-gray-200 text-left">
                            <thead className="bg-gray-50">
                              <tr className="text-xs font-bold text-gray-500 uppercase tracking-wider">
                                <th className="px-4 py-3 cursor-pointer select-none" onClick={() => { setVulnSortField('id'); setVulnSortOrder(o => o === 'asc' ? 'desc' : 'asc'); }}>
                                  Vulnerability ID {vulnSortField === 'id' && (vulnSortOrder === 'asc' ? '↑' : '↓')}
                                </th>
                                <th className="px-4 py-3 cursor-pointer select-none" onClick={() => { setVulnSortField('package'); setVulnSortOrder(o => o === 'asc' ? 'desc' : 'asc'); }}>
                                  Package Name {vulnSortField === 'package' && (vulnSortOrder === 'asc' ? '↑' : '↓')}
                                </th>
                                <th className="px-4 py-3 cursor-pointer select-none" onClick={() => { setVulnSortField('severity'); setVulnSortOrder(o => o === 'asc' ? 'desc' : 'asc'); }}>
                                  Severity {vulnSortField === 'severity' && (vulnSortOrder === 'asc' ? '↑' : '↓')}
                                </th>
                                <th className="px-4 py-3">Remediation Fix</th>
                                <th className="px-4 py-3">Summary</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-100 text-xs">
                              {pagedVulns.map((vuln, index) => (
                                <tr key={index} className="hover:bg-gray-50/50 transition-all">
                                  <td className="px-4 py-3 font-bold text-sg-navy font-mono whitespace-nowrap">{vuln.vuln_id}</td>
                                  <td className="px-4 py-3 font-semibold text-gray-600 whitespace-nowrap">{vuln.packageName}@{vuln.packageVersion}</td>
                                  <td className="px-4 py-3">
                                    <span className={`inline-block rounded px-2 py-0.5 text-[9px] font-extrabold uppercase ${
                                      vuln.severity === 'CRITICAL' ? 'bg-red-50 text-sg-danger border border-sg-danger/20' : vuln.severity === 'HIGH' ? 'bg-amber-50 text-sg-warning border border-sg-warning/20' : vuln.severity === 'MEDIUM' ? 'bg-yellow-50 text-yellow-600 border border-yellow-500/20' : 'bg-green-50 text-sg-success border border-sg-success/20'
                                    }`}>
                                      {vuln.severity}
                                    </span>
                                  </td>
                                  <td className="px-4 py-3 whitespace-nowrap font-mono text-[10px]">
                                    {vuln.fixed_version ? (
                                      <span className="text-sg-success font-bold">Update to {vuln.fixed_version}</span>
                                    ) : (
                                      <span className="text-gray-400">No fix version</span>
                                    )}
                                  </td>
                                  <td className="px-4 py-3 text-gray-500 max-w-xs truncate" title={vuln.summary}>{vuln.summary}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>

                        {/* Pagination */}
                        {totalVulnPages > 1 && (
                          <div className="flex justify-between items-center text-xs text-gray-400 pt-3 border-t border-gray-100 font-semibold select-none">
                            <span>Page {vulnPage} of {totalVulnPages}</span>
                            <div className="flex gap-2">
                              <button
                                disabled={vulnPage === 1}
                                onClick={() => setVulnPage(p => Math.max(1, p - 1))}
                                className="px-3 py-1.5 border border-gray-200 rounded hover:bg-gray-50 disabled:opacity-50 transition-all cursor-pointer"
                              >
                                Previous
                              </button>
                              <button
                                disabled={vulnPage === totalVulnPages}
                                onClick={() => setVulnPage(p => Math.min(totalVulnPages, p + 1))}
                                className="px-3 py-1.5 border border-gray-200 rounded hover:bg-gray-50 disabled:opacity-50 transition-all cursor-pointer"
                              >
                                Next
                              </button>
                            </div>
                          </div>
                        )}
                      </>
                    )}
                  </div>
                )}

                {/* C. Dependencies Tab */}
                {activeTab === 'dependencies' && (
                  <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm space-y-4">
                    <h3 className="text-base font-bold text-sg-navy">Dependency Components Tree</h3>
                    <div className="overflow-x-auto border border-gray-200 rounded-md">
                      <table className="min-w-full divide-y divide-gray-200 text-left">
                        <thead className="bg-gray-50">
                          <tr className="text-xs font-bold text-gray-500 uppercase tracking-wider">
                            <th className="px-4 py-3">Package Name</th>
                            <th className="px-4 py-3">Version</th>
                            <th className="px-4 py-3">Ecosystem</th>
                            <th className="px-4 py-3">Scope</th>
                            <th className="px-4 py-3">License</th>
                            <th className="px-4 py-3">Security status</th>
                            <th className="px-4 py-3">Maintenance Score</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100 text-xs">
                          {allDeps.map((dep) => (
                            <tr key={dep.id} className="hover:bg-gray-50/50 transition-all">
                              <td className="px-4 py-3 font-bold text-sg-navy">{dep.name}</td>
                              <td className="px-4 py-3 font-mono">{dep.version}</td>
                              <td className="px-4 py-3 uppercase text-[10px] text-gray-400 font-semibold">{dep.ecosystem}</td>
                              <td className="px-4 py-3 whitespace-nowrap">
                                <span className={`inline-block rounded px-2 py-0.5 text-[9px] font-extrabold uppercase ${
                                  dep.is_direct ? 'bg-red-50 text-sg-red border border-sg-red/20' : 'bg-gray-100 text-gray-400'
                                }`}>
                                  {dep.is_direct ? 'Direct' : 'Transitive'}
                                </span>
                              </td>
                              <td className="px-4 py-3 font-mono">{dep.license_id || 'Undeclared'}</td>
                              <td className="px-4 py-3">
                                {dep.vulnerabilities.length > 0 ? (
                                  <span className="inline-block rounded bg-red-100 px-2 py-0.5 text-[10px] font-bold text-sg-danger border border-sg-danger/10">
                                    {dep.vulnerabilities.length} CVEs
                                  </span>
                                ) : (
                                  <span className="text-sg-success font-bold">Secure</span>
                                )}
                              </td>
                              <td className="px-4 py-3 whitespace-nowrap font-mono font-bold">
                                {dep.maintenance_score !== null ? (
                                  <span style={{ color: getScoreStrokeColor(100 - dep.maintenance_score) }}>
                                    {dep.maintenance_score}/100
                                  </span>
                                ) : (
                                  <span className="text-gray-300">—</span>
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* D. Licenses Tab */}
                {activeTab === 'licenses' && (
                  <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm space-y-4">
                    <h3 className="text-base font-bold text-sg-navy">License Auditing & Compliance</h3>
                    <div className="overflow-x-auto border border-gray-200 rounded-md">
                      <table className="min-w-full divide-y divide-gray-200 text-left">
                        <thead className="bg-gray-50">
                          <tr className="text-xs font-bold text-gray-500 uppercase tracking-wider">
                            <th className="px-4 py-3">Declared License</th>
                            <th className="px-4 py-3">Risk Level</th>
                            <th className="px-4 py-3">Affected Component</th>
                            <th className="px-4 py-3">Compliance Impact Info</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100 text-xs">
                          {allDeps.map((dep) => {
                            const risk = dep.license_risk || 'NONE';
                            return (
                              <tr key={dep.id} className="hover:bg-gray-50/50 transition-all">
                                <td className="px-4 py-3 font-bold text-sg-navy font-mono">{dep.license_id || 'Undeclared'}</td>
                                <td className="px-4 py-3 whitespace-nowrap">
                                  <span className={`inline-block rounded px-2.5 py-0.5 text-[9px] font-extrabold uppercase ${
                                    risk === 'HIGH' ? 'bg-red-100 text-sg-danger border border-sg-danger/20' : risk === 'MEDIUM' ? 'bg-amber-100 text-sg-warning border border-sg-warning/20' : risk === 'LOW' ? 'bg-yellow-100 text-yellow-600 border border-yellow-500/20' : 'bg-green-100 text-sg-success border border-sg-success/20'
                                  }`}>
                                    {risk}
                                  </span>
                                </td>
                                <td className="px-4 py-3 font-semibold text-gray-600">{dep.name}@{dep.version}</td>
                                <td className="px-4 py-3 text-gray-500">
                                  {risk === 'HIGH' && 'Strong copyleft (GPL variants). Potential compliance conflicts with proprietary code.'}
                                  {risk === 'MEDIUM' && 'Restricted or proprietary license schema, requires legal review.'}
                                  {risk === 'LOW' && 'Weak copyleft (LGPL/MPL). Permitted with custom source release guidelines.'}
                                  {risk === 'NONE' && 'Permissive open source structure (MIT/Apache). Clean to use.'}
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* E. React Flow dependency graph explorer */}
                {activeTab === 'graph' && (
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <h3 className="text-base font-bold text-sg-navy">Interactive Topology Graph Explorer</h3>
                      <Link
                        to={`/graph/${selectedSbomId}`}
                        target="_blank"
                        className="inline-flex items-center gap-1.5 rounded border border-gray-200 bg-white px-3 py-1.5 text-xs font-bold text-sg-navy hover:bg-gray-50 no-underline shadow-sm"
                      >
                        <span>Open Fullscreen</span>
                        <ExternalLink size={12} />
                      </Link>
                    </div>
                    {selectedSbomId && <DependencyGraphView sbomId={selectedSbomId} height={600} />}
                  </div>
                )}

                {/* F. Risk Score Trend History */}
                {activeTab === 'trend' && (
                  <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm space-y-6">
                    <h3 className="text-base font-bold text-sg-navy">Overall Risk score trend line</h3>
                    
                    {trendLoading ? (
                      <div className="space-y-2">
                        <div className="shimmer h-8 w-full rounded" />
                        <div className="shimmer h-64 w-full rounded" />
                      </div>
                    ) : trendData && trendData.length > 1 ? (
                      <div className="h-80 w-full">
                        <ResponsiveContainer width="100%" height="100%">
                          <LineChart data={trendData} margin={{ left: 0, right: 30, top: 10, bottom: 10 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                            <XAxis
                              dataKey="created_at"
                              tickFormatter={(str) => new Date(str).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                              stroke="#94A3B8"
                              style={{ fontSize: '10px' }}
                            />
                            <YAxis domain={[0, 100]} stroke="#94A3B8" style={{ fontSize: '10px' }} />
                            <Tooltip
                              contentStyle={{ background: '#FFFFFF', borderColor: '#E2E8F0', borderRadius: '4px', fontSize: '12px' }}
                              labelFormatter={(lbl) => new Date(lbl).toLocaleString()}
                              formatter={(val: any) => [`${val}/100`, 'Overall Risk Score']}
                            />
                            <Line
                              type="monotone"
                              dataKey="overall_score"
                              stroke="#FF1338"
                              strokeWidth={3}
                              dot={{ fill: '#FF1338', strokeWidth: 2, r: 4 }}
                              activeDot={{ r: 7, strokeWidth: 0 }}
                            />
                          </LineChart>
                        </ResponsiveContainer>
                      </div>
                    ) : (() => {
                      const activeSbom = application?.sboms?.find(s => s.id === selectedSbomId) || application?.sboms?.[0];
                      return (
                        <div className="text-center py-16 text-gray-400">
                          <TrendingUp size={48} className="mx-auto mb-4 text-sg-red/30" />
                          <h4 className="font-bold text-sg-navy uppercase tracking-wider text-xs">Insufficient Trend History</h4>
                          <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg max-w-md mx-auto mt-4 text-left space-y-2">
                            <div className="text-xs text-gray-500">
                              <strong>Current SBOM Artifact:</strong> <code className="font-mono text-sg-navy bg-white border px-1 py-0.5 rounded text-[10px] break-all">{activeSbom?.original_filename || 'Default Artifact'}</code>
                            </div>
                            <div className="text-xs text-gray-500">
                              <strong>Upload Date:</strong> <span className="font-mono text-sg-navy font-semibold">{activeSbom?.created_at ? new Date(activeSbom.created_at).toLocaleString() : 'N/A'}</span>
                            </div>
                            <div className="text-[11px] text-gray-400 pt-1.5 border-t border-gray-200 leading-relaxed font-semibold">
                              Only one version of the SBOM has been analyzed. Upload subsequent SBOM revisions for this application using the top-right button to enable chronological risk trend graph tracking.
                            </div>
                          </div>
                        </div>
                      );
                    })()}
                  </div>
                )}

              </>
            )}

          </div>

        </div>
      )}

    </div>
  );
}
