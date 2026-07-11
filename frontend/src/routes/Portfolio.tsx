import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useApplications, useCreateApplication } from '../hooks/useApplications';
import { Plus, Search, ShieldAlert, Layers, Calendar, Loader2 } from 'lucide-react';
import type { ApplicationListItem } from '../types/application';

export default function Portfolio() {
  const { data: applications, isLoading, error } = useApplications();
  const createMutation = useCreateApplication();
  
  const [searchTerm, setSearchTerm] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [appName, setAppName] = useState('');
  const [appDesc, setAppDesc] = useState('');

  // Handle Form Submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!appName.trim()) return;

    try {
      await createMutation.mutateAsync({
        name: appName,
        description: appDesc || undefined,
      });
      setAppName('');
      setAppDesc('');
      setIsModalOpen(false);
    } catch (err) {
      console.error('Failed to create application:', err);
    }
  };

  // Filter applications by search term
  const filteredApps = applications?.filter((app: ApplicationListItem) =>
    app.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (app.description && app.description.toLowerCase().includes(searchTerm.toLowerCase()))
  ) || [];

  // Helper to get score color variables/classes
  const getScoreColorClass = (score: number | null) => {
    if (score === null) return 'badge-none';
    if (score >= 75) return 'badge-critical';
    if (score >= 50) return 'badge-high';
    if (score >= 25) return 'badge-medium';
    return 'badge-low';
  };

  const getScoreColorBg = (score: number | null) => {
    if (score === null) return 'rgba(107, 114, 128, 0.1)';
    if (score >= 75) return 'rgba(239, 68, 68, 0.15)';
    if (score >= 50) return 'rgba(249, 115, 22, 0.15)';
    if (score >= 25) return 'rgba(234, 179, 8, 0.15)';
    return 'rgba(16, 185, 129, 0.15)';
  };

  const getScoreBorderColor = (score: number | null) => {
    if (score === null) return 'rgba(107, 114, 128, 0.3)';
    if (score >= 75) return 'rgba(239, 68, 68, 0.4)';
    if (score >= 50) return 'rgba(249, 115, 22, 0.4)';
    if (score >= 25) return 'rgba(234, 179, 8, 0.4)';
    return 'rgba(16, 185, 129, 0.4)';
  };

  const getScoreTextColor = (score: number | null) => {
    if (score === null) return 'var(--text-secondary)';
    if (score >= 75) return 'var(--color-critical)';
    if (score >= 50) return 'var(--color-high)';
    if (score >= 25) return 'var(--color-medium)';
    return 'var(--color-low)';
  };

  return (
    <div className="page-container">
      {/* Header section */}
      <div className="flex justify-between align-center mb-4" style={{ marginBottom: '2rem' }}>
        <div>
          <h1 className="m-0">DevSecOps Application Portfolio</h1>
          <p className="text-muted" style={{ marginTop: '0.25rem' }}>
            Monitor and track software supply chain risk scores across applications.
          </p>
        </div>
        <button className="btn btn-primary" onClick={() => setIsModalOpen(true)}>
          <Plus size={18} /> Add Application
        </button>
      </div>

      {/* Search Bar & Stats */}
      <div className="glass-card mb-4" style={{ padding: '1rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <div style={{ position: 'relative', flex: 1 }}>
          <Search size={18} style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
          <input
            type="text"
            placeholder="Search applications..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{
              width: '100%',
              padding: '0.6rem 0.75rem 0.6rem 2.25rem',
              background: 'rgba(255, 255, 255, 0.03)',
              border: '1px solid var(--border-color)',
              borderRadius: 'var(--radius-md)',
              color: 'var(--text-primary)',
              fontFamily: 'var(--font-sans)',
            }}
          />
        </div>
        <div className="text-muted" style={{ fontSize: '0.9rem', whiteSpace: 'nowrap' }}>
          Showing {filteredApps.length} of {applications?.length || 0} applications
        </div>
      </div>

      {/* Main Grid Content */}
      {isLoading ? (
        <div className="portfolio-grid">
          {[1, 2, 3].map((n) => (
            <div key={n} className="glass-card app-card" style={{ height: '220px' }}>
              <div className="skeleton" style={{ height: '24px', width: '60%', marginBottom: '1rem' }} />
              <div className="skeleton" style={{ height: '60px', width: '100%', marginBottom: '1rem' }} />
              <div className="skeleton" style={{ height: '32px', width: '100%', marginTop: 'auto' }} />
            </div>
          ))}
        </div>
      ) : error ? (
        <div className="glass-card text-center" style={{ padding: '3rem', color: 'var(--color-critical)' }}>
          <ShieldAlert size={48} style={{ marginBottom: '1rem', marginInline: 'auto' }} />
          <h3>Error Loading Applications</h3>
          <p className="text-muted mt-4">Could not connect to the risk scoring backend.</p>
        </div>
      ) : filteredApps.length === 0 ? (
        <div className="glass-card text-center" style={{ padding: '4rem 2rem' }}>
          <Layers size={48} style={{ color: 'var(--color-primary)', marginBottom: '1.5rem', marginInline: 'auto' }} />
          <h2>No Applications Found</h2>
          <p className="text-muted" style={{ maxWidth: '400px', margin: '0.5rem auto 1.5rem' }}>
            {searchTerm ? "No apps match your search filter." : "Get started by adding your first application, then upload an SBOM file to parse and analyze it."}
          </p>
          {!searchTerm && (
            <button className="btn btn-primary" onClick={() => setIsModalOpen(true)}>
              <Plus size={18} /> Add Application
            </button>
          )}
        </div>
      ) : (
        <div className="portfolio-grid">
          {filteredApps.map((app: ApplicationListItem) => (
            <Link
              to={`/application/${app.id}`}
              key={app.id}
              className="glass-card app-card text-decoration-none"
              style={{ textDecoration: 'none', display: 'flex', flexDirection: 'column' }}
            >
              <div className="app-card-header">
                <div>
                  <h3 style={{ fontSize: '1.2rem', fontWeight: 600 }}>{app.name}</h3>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.25rem' }}>
                    <span className={`badge ${getScoreColorClass(app.latest_score)}`}>
                      {app.latest_score !== null ? app.latest_category : 'No SBOM'}
                    </span>
                  </div>
                </div>

                <div
                  className="app-score-circle"
                  style={{
                    background: getScoreColorBg(app.latest_score),
                    border: `1px solid ${getScoreBorderColor(app.latest_score)}`,
                    color: getScoreTextColor(app.latest_score),
                  }}
                >
                  {app.latest_score !== null ? app.latest_score : '—'}
                </div>
              </div>

              <div className="app-card-body">
                <p style={{
                  display: '-webkit-box',
                  WebkitLineClamp: 3,
                  WebkitBoxOrient: 'vertical',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis'
                }}>
                  {app.description || 'No description provided.'}
                </p>
              </div>

              <div className="app-card-footer">
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                  <Layers size={14} />
                  <span>{app.sbom_count} {app.sbom_count === 1 ? 'SBOM version' : 'SBOM versions'}</span>
                </div>
                {app.last_analyzed_at && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                    <Calendar size={14} />
                    <span>
                      {new Date(app.last_analyzed_at).toLocaleDateString(undefined, {
                        month: 'short',
                        day: 'numeric',
                      })}
                    </span>
                  </div>
                )}
              </div>
            </Link>
          ))}
        </div>
      )}

      {/* Modal dialog for creating an application */}
      {isModalOpen && (
        <div className="modal-overlay" onClick={() => setIsModalOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3 style={{ marginBottom: '1.5rem' }}>Add New Application</h3>
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label htmlFor="appName">Application Name *</label>
                <input
                  id="appName"
                  type="text"
                  required
                  placeholder="e.g. Payments Service"
                  value={appName}
                  onChange={(e) => setAppName(e.target.value)}
                />
              </div>
              <div className="form-group">
                <label htmlFor="appDesc">Description</label>
                <textarea
                  id="appDesc"
                  placeholder="Introduce the service, technology stack or architecture details..."
                  rows={4}
                  value={appDesc}
                  onChange={(e) => setAppDesc(e.target.value)}
                />
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', marginTop: '2rem' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setIsModalOpen(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={createMutation.isPending}>
                  {createMutation.isPending ? (
                    <>
                      <Loader2 size={16} className="animate-spin" /> Adding...
                    </>
                  ) : (
                    'Add Application'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
