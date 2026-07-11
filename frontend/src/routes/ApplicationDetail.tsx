import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { useApplication } from '../hooks/useApplications';
import { useRiskReport, useAIReport } from '../hooks/useRiskReport';
import { useSbomUpload } from '../hooks/useSbomUpload';
import { applicationsApi, sbomsApi } from '../services/apiClient';
import { useDropzone } from 'react-dropzone';
import {
  Upload,
  ShieldAlert,
  Clock,
  Sparkles,
  ArrowLeft,
  Loader2,
  AlertTriangle,
  Info,
  CheckCircle,
  ExternalLink,
  TrendingUp,
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import DependencyGraphView from '../components/graph/DependencyGraphView';

export default function ApplicationDetail() {
  const { id } = useParams<{ id: string }>();
  const appId = id || '';

  // Get application metadata & SBOM list
  const { data: application, isLoading: appLoading, error: appError, refetch: refetchApp } = useApplication(appId);

  // Selected SBOM ID state - default to first completed SBOM
  const [selectedSbomId, setSelectedSbomId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'summary' | 'vulnerabilities' | 'dependencies' | 'licenses' | 'graph' | 'trend'>('summary');
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<'idle' | 'uploading' | 'polling' | 'success' | 'error'>('idle');
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [newSbomId, setNewSbomId] = useState<string | null>(null);
  const [pollingStatus, setPollingStatus] = useState<string>('');

  // Fetch trend data
  const { data: trendData, isLoading: trendLoading } = useQuery<any[]>({
    queryKey: ['trend', appId],
    queryFn: () => applicationsApi.trend(appId),
    enabled: !!appId,
  });

  // Automatically select the latest completed SBOM on load/update
  useEffect(() => {
    if (application?.sboms && application.sboms.length > 0) {
      const completedSbom = application.sboms.find(s => s.status === 'completed');
      if (completedSbom && !selectedSbomId) {
        setSelectedSbomId(completedSbom.id);
      }
    }
  }, [application, selectedSbomId]);

  // Fetch Risk Report and AI summary for the selected SBOM
  const { data: report, isLoading: reportLoading, error: reportError, refetch: refetchReport } = useRiskReport(selectedSbomId || '');
  const { data: aiReport, isLoading: aiLoading } = useAIReport(selectedSbomId || '');

  // SBOM upload mutation
  const uploadMutation = useSbomUpload();

  // Dropzone config
  const onDrop = async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;
    const file = acceptedFiles[0];

    setUploadProgress('uploading');
    setUploadError(null);

    try {
      const res = await uploadMutation.mutateAsync({
        applicationId: appId,
        file,
      });

      setNewSbomId(res.sbom_id);
      setUploadProgress('polling');
      setPollingStatus('Queued for analysis...');
    } catch (err: any) {
      setUploadProgress('error');
      setUploadError(err.message || 'Failed to upload SBOM');
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/json': ['.json'],
    },
    maxFiles: 1,
  });

  // Poll SBOM status while parsing/analyzing
  useEffect(() => {
    if (uploadProgress !== 'polling' || !newSbomId) return;

    let intervalId: any = null;
    const checkStatus = async () => {
      try {
        const res = await sbomsApi.status(newSbomId);
        setPollingStatus(res.status === 'parsing' ? 'Parsing SBOM contents...' : res.status === 'analyzing' ? 'Running vulnerability & maintenance checks...' : res.status);
        
        if (res.status === 'completed') {
          clearInterval(intervalId);
          setUploadProgress('success');
          setSelectedSbomId(newSbomId);
          await refetchApp();
          setIsUploadOpen(false);
          setUploadProgress('idle');
          setNewSbomId(null);
        } else if (res.status === 'failed' || res.status === 'parse_failed') {
          clearInterval(intervalId);
          setUploadProgress('error');
          setUploadError(res.error_detail || 'Analysis job failed');
        }
      } catch (err: any) {
        clearInterval(intervalId);
        setUploadProgress('error');
        setUploadError(err.message || 'Polling error');
      }
    };

    intervalId = setInterval(checkStatus, 2000);
    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [uploadProgress, newSbomId, refetchApp]);

  if (appLoading) {
    return (
      <div className="page-container flex align-center justify-between" style={{ height: '300px' }}>
        <Loader2 size={36} className="animate-spin" style={{ margin: 'auto', color: 'var(--color-primary)' }} />
      </div>
    );
  }

  if (appError || !application) {
    return (
      <div className="page-container">
        <div className="glass-card text-center" style={{ padding: '3rem', color: 'var(--color-critical)' }}>
          <ShieldAlert size={48} style={{ marginBottom: '1rem', marginInline: 'auto' }} />
          <h3>Application Not Found</h3>
          <p className="text-muted mt-4">The application might have been deleted.</p>
          <Link to="/" className="btn btn-secondary mt-4">
            <ArrowLeft size={16} /> Back to Portfolio
          </Link>
        </div>
      </div>
    );
  }

  // Helper variables for styling
  const score = report?.overall_score ?? null;
  const getScoreColor = (s: number | null) => {
    if (s === null) return 'var(--color-none)';
    if (s >= 75) return 'var(--color-critical)';
    if (s >= 50) return 'var(--color-high)';
    if (s >= 25) return 'var(--color-medium)';
    return 'var(--color-low)';
  };

  const getScoreBadge = (s: number | null) => {
    if (s === null) return 'badge-none';
    if (s >= 75) return 'badge-critical';
    if (s >= 50) return 'badge-high';
    if (s >= 25) return 'badge-medium';
    return 'badge-low';
  };

  // SVG Gauge computation
  const radius = 65;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - ((score ?? 0) / 100) * circumference;

  return (
    <div className="page-container">
      {/* Navigation */}
      <Link to="/" className="btn btn-secondary" style={{ marginBottom: '1.5rem', display: 'inline-flex' }}>
        <ArrowLeft size={16} /> Back to Portfolio
      </Link>

      {/* Main Header Card */}
      <div className="glass-card mb-4 flex justify-between align-center" style={{ padding: '2rem' }}>
        <div>
          <h1 className="m-0" style={{ fontSize: '2rem' }}>{application.name}</h1>
          <p className="text-muted" style={{ marginTop: '0.5rem', fontSize: '0.95rem', maxWidth: '800px' }}>
            {application.description || 'No description provided.'}
          </p>
        </div>
        <button className="btn btn-primary" onClick={() => setIsUploadOpen(true)}>
          <Upload size={16} /> Upload SBOM version
        </button>
      </div>

      {application.sboms.length === 0 ? (
        <div className="glass-card text-center" style={{ padding: '5rem 2rem' }}>
          <Upload size={48} style={{ color: 'var(--color-primary)', marginBottom: '1.5rem', marginInline: 'auto' }} />
          <h2>Upload an SBOM to Start Analysis</h2>
          <p className="text-muted" style={{ maxWidth: '500px', margin: '0.5rem auto 2rem' }}>
            To analyze this application's risks, drop or select a CycloneDX or SPDX JSON SBOM file.
            We will parse and evaluate security, maintenance and compliance posture.
          </p>
          <button className="btn btn-primary btn-lg" onClick={() => setIsUploadOpen(true)}>
            <Upload size={16} /> Upload SBOM
          </button>
        </div>
      ) : (
        <div className="detail-grid">
          {/* LEFT SIDEBAR */}
          <div className="detail-sidebar">
            {/* Risk Gauge Card */}
            <div className="glass-card score-gauge-card">
              <h3>Overall Risk Score</h3>
              <div className="gauge-svg-container">
                <svg viewBox="0 0 160 160" style={{ width: '100%', height: '100%' }}>
                  <circle
                    cx="80"
                    cy="80"
                    r={radius}
                    fill="transparent"
                    stroke="rgba(255, 255, 255, 0.04)"
                    strokeWidth="10"
                  />
                  <circle
                    cx="80"
                    cy="80"
                    r={radius}
                    fill="transparent"
                    stroke={getScoreColor(score)}
                    strokeWidth="10"
                    strokeDasharray={circumference}
                    strokeDashoffset={score !== null ? strokeDashoffset : circumference}
                    strokeLinecap="round"
                    transform="rotate(-90 80 80)"
                    style={{ transition: 'stroke-dashoffset 0.8s ease-in-out' }}
                  />
                </svg>
                <div className="gauge-inner-text">
                  <span className="gauge-score" style={{ color: getScoreColor(score) }}>
                    {score !== null ? score : '—'}
                  </span>
                  <span className="gauge-label">RISK LEVEL</span>
                </div>
              </div>
              <span className={`badge ${getScoreBadge(score)}`} style={{ padding: '0.4rem 1rem' }}>
                {report?.category || 'UNKNOWN'}
              </span>
            </div>

            {/* Subscores breakdowns */}
            {report && (
              <div className="glass-card">
                <h3 style={{ marginBottom: '1.25rem', fontSize: '1.1rem' }}>Risk Dimensions</h3>
                
                <div className="subscore-bar-wrapper">
                  <div className="subscore-label-row">
                    <span>Vulnerability Risk</span>
                    <span style={{ color: getScoreColor(report.vulnerability_subscore) }}>{report.vulnerability_subscore}/100</span>
                  </div>
                  <div className="subscore-bar-bg">
                    <div className="subscore-bar-fill" style={{ width: `${report.vulnerability_subscore}%`, backgroundColor: getScoreColor(report.vulnerability_subscore) }} />
                  </div>
                </div>

                <div className="subscore-bar-wrapper">
                  <div className="subscore-label-row">
                    <span>License Compliance</span>
                    <span style={{ color: getScoreColor(report.license_subscore) }}>{report.license_subscore}/100</span>
                  </div>
                  <div className="subscore-bar-bg">
                    <div className="subscore-bar-fill" style={{ width: `${report.license_subscore}%`, backgroundColor: getScoreColor(report.license_subscore) }} />
                  </div>
                </div>

                <div className="subscore-bar-wrapper" style={{ marginBottom: 0 }}>
                  <div className="subscore-label-row">
                    <span>Maintenance Health</span>
                    <span style={{ color: getScoreColor(report.maintenance_subscore) }}>{report.maintenance_subscore}/100</span>
                  </div>
                  <div className="subscore-bar-bg">
                    <div className="subscore-bar-fill" style={{ width: `${report.maintenance_subscore}%`, backgroundColor: getScoreColor(report.maintenance_subscore) }} />
                  </div>
                </div>
              </div>
            )}

            {/* Version list selector */}
            <div className="glass-card">
              <h3 style={{ marginBottom: '1rem', fontSize: '1.1rem' }}>Artifact History</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {application.sboms.map((sbom) => (
                  <button
                    key={sbom.id}
                    className={`btn pointer text-left w-full`}
                    style={{
                      justifyContent: 'flex-start',
                      padding: '0.75rem',
                      background: selectedSbomId === sbom.id ? 'rgba(139, 92, 246, 0.15)' : 'rgba(255, 255, 255, 0.02)',
                      border: selectedSbomId === sbom.id ? '1px solid var(--color-primary)' : '1px solid var(--border-color)',
                      textAlign: 'left',
                      borderRadius: 'var(--radius-md)',
                      color: selectedSbomId === sbom.id ? 'var(--text-primary)' : 'var(--text-secondary)',
                    }}
                    onClick={() => {
                      setSelectedSbomId(sbom.id);
                      refetchReport();
                    }}
                  >
                    <div style={{ display: 'flex', flexDirection: 'column', width: '100%' }}>
                      <div className="flex justify-between w-full align-center" style={{ gap: '0.5rem' }}>
                        <span style={{ fontWeight: 600, fontSize: '0.85rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {sbom.original_filename}
                        </span>
                        {sbom.status !== 'completed' && (
                          <span className="badge" style={{ background: 'rgba(234, 179, 8, 0.1)', color: '#facc15', fontSize: '0.65rem' }}>
                            {sbom.status}
                          </span>
                        )}
                      </div>
                      <div className="flex justify-between w-full mt-4" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        <span style={{ display: 'flex', alignItems: 'center', gap: '0.2rem' }}>
                          <Clock size={12} />
                          {new Date(sbom.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                        </span>
                        {sbom.component_count && <span>{sbom.component_count} deps</span>}
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* RIGHT MAIN VIEW */}
          <div className="detail-main">
            {/* Tab navigation */}
            <div className="tabs-container">
              <button className={`tab-btn ${activeTab === 'summary' ? 'active' : ''}`} onClick={() => setActiveTab('summary')}>Summary</button>
              <button className={`tab-btn ${activeTab === 'vulnerabilities' ? 'active' : ''}`} onClick={() => setActiveTab('vulnerabilities')}>
                Vulnerabilities ({report?.dependencies.reduce((acc, curr) => acc + curr.vulnerabilities.length, 0) || 0})
              </button>
              <button className={`tab-btn ${activeTab === 'dependencies' ? 'active' : ''}`} onClick={() => setActiveTab('dependencies')}>
                Dependencies ({report?.dependencies.length || 0})
              </button>
              <button className={`tab-btn ${activeTab === 'licenses' ? 'active' : ''}`} onClick={() => setActiveTab('licenses')}>Licenses</button>
              <button className={`tab-btn ${activeTab === 'graph' ? 'active' : ''}`} onClick={() => setActiveTab('graph')}>Graph Explorer</button>
              <button className={`tab-btn ${activeTab === 'trend' ? 'active' : ''}`} onClick={() => setActiveTab('trend')}>Risk Trend</button>
            </div>

            {/* TAB CONTENTS */}
            {reportLoading ? (
              <div className="glass-card flex align-center" style={{ height: '400px' }}>
                <Loader2 size={36} className="animate-spin" style={{ margin: 'auto', color: 'var(--color-primary)' }} />
              </div>
            ) : reportError ? (
              <div className="glass-card text-center" style={{ padding: '3rem', color: 'var(--color-critical)' }}>
                <ShieldAlert size={48} style={{ marginBottom: '1rem', marginInline: 'auto' }} />
                <h3>Risk Report Unavailable</h3>
                <p className="text-muted mt-4">Risk score analysis details could not be parsed.</p>
              </div>
            ) : (
              <>
                {/* 1. Summary Tab */}
                {activeTab === 'summary' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                    {/* Warning Banners if parsing issues or low confidence */}
                    {report?.breakdown && report.breakdown.confidence < 0.6 && (
                      <div className="warning-banner">
                        <Info size={16} />
                        <div>
                          <strong>Low Data Confidence ({Math.round(report.breakdown.confidence * 100)}%):</strong> Many dependencies do not specify repository URLs, making maintenance analysis incomplete.
                        </div>
                      </div>
                    )}

                    {/* AI Summary Card */}
                    <div className="glass-card ai-card">
                      <div className="ai-header">
                        <Sparkles size={20} />
                        <h3 className="m-0" style={{ fontSize: '1.2rem', fontWeight: 700 }}>AI Security Advisor</h3>
                      </div>
                      {aiLoading ? (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', padding: '1rem 0' }}>
                          <div className="skeleton" style={{ height: '16px', width: '90%' }} />
                          <div className="skeleton" style={{ height: '16px', width: '85%' }} />
                          <div className="skeleton" style={{ height: '16px', width: '50%' }} />
                        </div>
                      ) : aiReport ? (
                        <div>
                          <p style={{ lineHeight: 1.6, fontSize: '0.95rem' }}>{aiReport.summary}</p>
                          <div style={{ marginTop: '1.5rem' }}>
                            <h4 style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Prioritized Actions</h4>
                            {aiReport.top_actions.map((action, idx) => (
                              <div key={idx} className="ai-action-item">
                                <span className={`badge ai-action-badge ${action.priority === 'HIGH' ? 'badge-critical' : action.priority === 'MEDIUM' ? 'badge-high' : 'badge-low'}`}>
                                  {action.priority}
                                </span>
                                <div>
                                  <h4 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)' }}>{action.title}</h4>
                                  <p className="text-muted" style={{ fontSize: '0.85rem', marginTop: '0.25rem', lineHeight: 1.5 }}>{action.description}</p>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      ) : (
                        <p className="text-muted">AI Insights could not be loaded.</p>
                      )}
                    </div>

                    {/* Top Contributors Card */}
                    {report?.breakdown?.top_contributing_dependencies && (
                      <div className="glass-card">
                        <h3 style={{ marginBottom: '1rem', fontSize: '1.2rem' }}>Top Risk Contributors</h3>
                        <div className="table-wrapper">
                          <table className="custom-table">
                            <thead>
                              <tr>
                                <th>Package</th>
                                <th>Direct?</th>
                                <th>Vulnerability</th>
                                <th>License</th>
                                <th>Maintenance</th>
                                <th>Contribution</th>
                              </tr>
                            </thead>
                            <tbody>
                              {report.breakdown.top_contributing_dependencies.map((dep: any, idx: number) => (
                                <tr key={idx}>
                                  <td style={{ fontWeight: 600 }}>{dep.name}@{dep.version}</td>
                                  <td>{dep.is_direct ? <span style={{ color: 'var(--color-primary)' }}>Direct</span> : <span className="text-muted">Transitive</span>}</td>
                                  <td><span style={{ color: getScoreColor(dep.vuln_score) }}>{dep.vuln_score}</span></td>
                                  <td><span style={{ color: getScoreColor(dep.license_score) }}>{dep.license_score}</span></td>
                                  <td>{dep.maintenance_score !== null ? <span style={{ color: getScoreColor(100 - dep.maintenance_score) }}>{100 - dep.maintenance_score}</span> : <span className="text-muted">—</span>}</td>
                                  <td><strong style={{ color: getScoreColor(dep.weighted_contribution) }}>{dep.weighted_contribution}</strong></td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* 2. Vulnerabilities Tab */}
                {activeTab === 'vulnerabilities' && (
                  <div className="glass-card">
                    <h3 style={{ marginBottom: '1rem' }}>Security Vulnerabilities</h3>
                    
                    {report?.dependencies.every(d => d.vulnerabilities.length === 0) ? (
                      <div className="text-center" style={{ padding: '3rem' }}>
                        <CheckCircle size={48} style={{ color: 'var(--color-low)', marginBottom: '1rem', marginInline: 'auto' }} />
                        <h3>No Vulnerabilities Found</h3>
                        <p className="text-muted mt-4">All package checks passed. No known CVEs found in this SBOM version.</p>
                      </div>
                    ) : (
                      <div className="table-wrapper">
                        <table className="custom-table">
                          <thead>
                            <tr>
                              <th>Vulnerability ID</th>
                              <th>Affected Package</th>
                              <th>Severity</th>
                              <th>Remediation Fix</th>
                              <th>Summary</th>
                            </tr>
                          </thead>
                          <tbody>
                            {report?.dependencies.flatMap(dep => 
                              dep.vulnerabilities.map((vuln, vIdx) => (
                                <tr key={`${dep.id}-${vIdx}`}>
                                  <td>
                                    <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontFamily: 'var(--font-display)', fontWeight: 600 }}>
                                      {vuln.vuln_id}
                                    </span>
                                  </td>
                                  <td>{dep.name}@{dep.version}</td>
                                  <td>
                                    <span className={`badge ${vuln.severity === 'CRITICAL' ? 'badge-critical' : vuln.severity === 'HIGH' ? 'badge-high' : vuln.severity === 'MEDIUM' ? 'badge-medium' : 'badge-low'}`}>
                                      {vuln.severity}
                                    </span>
                                  </td>
                                  <td>
                                    {vuln.fixed_version ? (
                                      <span style={{ color: 'var(--color-low)', fontWeight: 600 }}>Update to {vuln.fixed_version}</span>
                                    ) : (
                                      <span className="text-muted">No fix available</span>
                                    )}
                                  </td>
                                  <td style={{ maxWidth: '300px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={vuln.summary}>
                                    {vuln.summary}
                                  </td>
                                </tr>
                              ))
                            )}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                )}

                {/* 3. Dependencies Tab */}
                {activeTab === 'dependencies' && (
                  <div className="glass-card">
                    <h3 style={{ marginBottom: '1rem' }}>Resolved Dependency Tree</h3>
                    <div className="table-wrapper">
                      <table className="custom-table">
                        <thead>
                          <tr>
                            <th>Package Name</th>
                            <th>Version</th>
                            <th>Ecosystem</th>
                            <th>Scope</th>
                            <th>License</th>
                            <th>Vulnerabilities</th>
                            <th>Maintenance Score</th>
                          </tr>
                        </thead>
                        <tbody>
                          {report?.dependencies.map((dep) => (
                            <tr key={dep.id}>
                              <td style={{ fontWeight: 600 }}>{dep.name}</td>
                              <td>{dep.version}</td>
                              <td><span className="badge" style={{ background: 'rgba(255,255,255,0.04)', color: 'var(--text-secondary)' }}>{dep.ecosystem}</span></td>
                              <td>{dep.is_direct ? <span style={{ color: 'var(--color-primary)', fontWeight: 600 }}>Direct</span> : <span className="text-muted">Transitive</span>}</td>
                              <td>{dep.license_id || <span style={{ color: 'var(--color-high)' }}>Undeclared</span>}</td>
                              <td>
                                {dep.vulnerabilities.length > 0 ? (
                                  <span className="badge badge-critical">{dep.vulnerabilities.length} vuln</span>
                                ) : (
                                  <span style={{ color: 'var(--color-low)' }}>Secure</span>
                                )}
                              </td>
                              <td>
                                {dep.maintenance_score !== null ? (
                                  <span style={{ color: getScoreColor(100 - dep.maintenance_score), fontWeight: 600 }}>{dep.maintenance_score}/100</span>
                                ) : (
                                  <span className="text-muted">—</span>
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* 4. Licenses Tab */}
                {activeTab === 'licenses' && (
                  <div className="glass-card">
                    <h3 style={{ marginBottom: '1rem' }}>License Audits & Compatibility</h3>
                    <div className="table-wrapper">
                      <table className="custom-table">
                        <thead>
                          <tr>
                            <th>Declared License</th>
                            <th>Risk Level</th>
                            <th>Impacted Package</th>
                            <th>Description</th>
                          </tr>
                        </thead>
                        <tbody>
                          {report?.dependencies.map((dep) => {
                            const risk = dep.license_risk || 'NONE';
                            return (
                              <tr key={dep.id}>
                                <td style={{ fontWeight: 600, fontFamily: 'var(--font-display)' }}>{dep.license_id || 'Undeclared'}</td>
                                <td>
                                  <span className={`badge ${risk === 'HIGH' ? 'badge-critical' : risk === 'MEDIUM' ? 'badge-high' : risk === 'LOW' ? 'badge-medium' : 'badge-low'}`}>
                                    {risk}
                                  </span>
                                </td>
                                <td>{dep.name}@{dep.version}</td>
                                <td style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                                  {risk === 'HIGH' && 'Strong copyleft, potential licensing conflict with proprietary applications.'}
                                  {risk === 'MEDIUM' && 'Unknown or commercial/proprietary license structure.'}
                                  {risk === 'LOW' && 'Weak copyleft structures.'}
                                  {risk === 'NONE' && 'Permissive open-source structure.'}
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* 5. Graph Tab */}
                {activeTab === 'graph' && (
                  <div className="glass-card" style={{ padding: '1rem', height: '680px' }}>
                    <div className="flex justify-between align-center mb-4">
                      <h3 style={{ fontSize: '1.2rem' }}>Interactive Dependency Graph</h3>
                      <Link to={`/graph/${selectedSbomId}`} className="btn btn-secondary" style={{ fontSize: '0.8rem' }}>
                        Open Fullscreen <ExternalLink size={14} />
                      </Link>
                    </div>
                    <div style={{ height: '580px', background: '#0a0b10', borderRadius: 'var(--radius-md)', overflow: 'hidden' }}>
                      {selectedSbomId && <DependencyGraphView sbomId={selectedSbomId} height={580} />}
                    </div>
                  </div>
                )}

                {/* 6. Trend Tab */}
                {activeTab === 'trend' && (
                  <div className="glass-card" style={{ padding: '2rem' }}>
                    <h3 style={{ marginBottom: '1.5rem' }}>Risk Score Trend Line</h3>
                    {trendLoading ? (
                      <div className="skeleton" style={{ height: '300px', width: '100%' }} />
                    ) : trendData && trendData.length > 1 ? (
                      <div style={{ height: '350px', width: '100%' }}>
                        <ResponsiveContainer width="100%" height="100%">
                          <LineChart data={trendData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                            <XAxis
                              dataKey="created_at"
                              tickFormatter={(str) => new Date(str).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                              stroke="var(--text-muted)"
                              style={{ fontSize: '0.75rem' }}
                            />
                            <YAxis domain={[0, 100]} stroke="var(--text-muted)" style={{ fontSize: '0.75rem' }} />
                            <Tooltip
                              contentStyle={{ background: '#12141c', borderColor: 'var(--border-color)', borderRadius: 'var(--radius-md)' }}
                              labelFormatter={(lbl) => new Date(lbl).toLocaleString()}
                              formatter={(val: any) => [`${val}/100`, 'Overall Risk Score']}
                            />
                            <Line
                              type="monotone"
                              dataKey="overall_score"
                              stroke="var(--color-primary)"
                              strokeWidth={3}
                              dot={{ fill: 'var(--color-primary)', strokeWidth: 2, r: 5 }}
                              activeDot={{ r: 8, strokeWidth: 0 }}
                            />
                          </LineChart>
                        </ResponsiveContainer>
                      </div>
                    ) : (
                      <div className="text-center text-muted" style={{ padding: '4rem 0' }}>
                        <TrendingUp size={48} style={{ color: 'var(--color-primary)', marginBottom: '1rem', marginInline: 'auto' }} />
                        <h4>Not enough trend history</h4>
                        <p style={{ maxWidth: '380px', margin: '0.5rem auto' }}>
                          Upload subsequent versions of this application's SBOM to monitor overall risk trend variations over time.
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      )}

      {/* Upload Dialog Modal */}
      {isUploadOpen && (
        <div className="modal-overlay" onClick={() => uploadProgress !== 'polling' && setIsUploadOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '550px' }}>
            <h3 style={{ marginBottom: '1.5rem' }}>Upload SBOM Artifact</h3>

            {uploadProgress === 'idle' && (
              <div {...getRootProps()} className={`dropzone ${isDragActive ? 'active' : ''}`}>
                <input {...getInputProps()} />
                <Upload size={36} style={{ color: 'var(--color-primary)' }} />
                <div>
                  <h4 style={{ fontSize: '1rem', fontWeight: 600 }}>Drag and drop SBOM JSON here</h4>
                  <p className="text-muted" style={{ fontSize: '0.85rem', marginTop: '0.25rem' }}>
                    CycloneDX or SPDX format (max 20MB)
                  </p>
                </div>
                <button type="button" className="btn btn-secondary">Select file</button>
              </div>
            )}

            {uploadProgress === 'uploading' && (
              <div className="text-center" style={{ padding: '2rem' }}>
                <Loader2 size={36} className="animate-spin" style={{ marginInline: 'auto', color: 'var(--color-primary)' }} />
                <h4 style={{ marginTop: '1rem' }}>Uploading artifact...</h4>
              </div>
            )}

            {uploadProgress === 'polling' && (
              <div className="text-center" style={{ padding: '2rem' }}>
                <Loader2 size={36} className="animate-spin" style={{ marginInline: 'auto', color: 'var(--color-primary)' }} />
                <h4 style={{ marginTop: '1rem' }}>Analyzing SBOM</h4>
                <p className="text-muted mt-4" style={{ fontSize: '0.85rem' }}>{pollingStatus}</p>
              </div>
            )}

            {uploadProgress === 'error' && (
              <div className="text-center" style={{ padding: '1rem' }}>
                <AlertTriangle size={36} style={{ color: 'var(--color-critical)', marginInline: 'auto', marginBottom: '1rem' }} />
                <h4>Analysis Failed</h4>
                <p className="text-muted mt-4" style={{ color: 'var(--color-critical)', fontSize: '0.9rem' }}>{uploadError}</p>
                <div style={{ marginTop: '2rem', display: 'flex', justifyContent: 'center', gap: '1rem' }}>
                  <button className="btn btn-secondary" onClick={() => setUploadProgress('idle')}>
                    Try Again
                  </button>
                  <button className="btn btn-primary" onClick={() => setIsUploadOpen(false)}>
                    Close
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
