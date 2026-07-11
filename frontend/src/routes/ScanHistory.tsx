import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useApplications } from '../hooks/useApplications';
import { useQueries } from '@tanstack/react-query';
import { applicationsApi } from '../services/apiClient';
import { Search, Loader2, History, CheckCircle, AlertTriangle, Clock, ShieldAlert } from 'lucide-react';

export default function ScanHistory() {
  const { data: applications, isLoading, error } = useApplications();
  const [searchTerm, setSearchTerm] = useState('');

  // Fetch details for all applications in parallel to compile scan history
  const applicationDetails = useQueries({
    queries: (applications || []).map((app) => ({
      queryKey: ['application', app.id],
      queryFn: () => applicationsApi.get(app.id),
      enabled: !!applications,
    })),
  });

  // Compile all scan history logs
  const allScans = React.useMemo(() => {
    const list: any[] = [];
    applicationDetails.forEach((query, idx) => {
      const app = applications?.[idx];
      const detail = query.data;
      if (!app || !detail?.sboms) return;

      detail.sboms.forEach((sbom) => {
        list.push({
          id: sbom.id,
          original_filename: sbom.original_filename,
          format: sbom.format,
          status: sbom.status,
          component_count: sbom.component_count,
          created_at: sbom.created_at,
          application_id: app.id,
          application_name: app.name,
          score: sbom.status === 'completed' && app.latest_score !== null ? app.latest_score : null,
          category: sbom.status === 'completed' && app.latest_category ? app.latest_category : null,
        });
      });
    });

    // Sort by date descending
    return list.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
  }, [applications, applicationDetails]);

  // Filter scan history logs
  const filteredScans = React.useMemo(() => {
    const term = searchTerm.trim().toLowerCase();
    if (!term) return allScans;
    return allScans.filter((scan) =>
      scan.application_name.toLowerCase().includes(term) ||
      scan.original_filename.toLowerCase().includes(term)
    );
  }, [allScans, searchTerm]);

  // Helper to get score styles
  const getScoreBadgeClass = (score: number | null) => {
    if (score === null) return 'bg-gray-100 text-gray-500 border border-gray-200';
    if (score >= 75) return 'bg-red-50 text-sg-danger border border-sg-danger/30';
    if (score >= 50) return 'bg-amber-50 text-sg-warning border border-sg-warning/30';
    if (score >= 25) return 'bg-yellow-50 text-yellow-600 border border-yellow-500/30';
    return 'bg-green-50 text-sg-success border border-sg-success/30';
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return (
          <span className="inline-flex items-center gap-1 rounded bg-green-50 px-2 py-0.5 text-xs font-bold text-sg-success border border-sg-success/30">
            <CheckCircle size={10} /> COMPLETED
          </span>
        );
      case 'failed':
      case 'parse_failed':
        return (
          <span className="inline-flex items-center gap-1 rounded bg-red-50 px-2 py-0.5 text-xs font-bold text-sg-danger border border-sg-danger/30">
            <AlertTriangle size={10} /> FAILED
          </span>
        );
      case 'queued':
        return (
          <span className="inline-flex items-center gap-1 rounded bg-gray-50 px-2 py-0.5 text-xs font-bold text-gray-500 border border-gray-200">
            <Clock size={10} /> QUEUED
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 rounded bg-yellow-50 px-2 py-0.5 text-xs font-bold text-sg-warning border border-sg-warning/30 animate-pulse">
            <Loader2 size={10} className="animate-spin" /> ANALYZING
          </span>
        );
    }
  };

  const isQuerying = applicationDetails.some(q => q.isLoading) || isLoading;

  return (
    <div className="max-w-7xl mx-auto w-full px-8 py-10">
      
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-extrabold text-sg-navy tracking-tight uppercase flex items-center gap-2">
          <History size={28} className="text-sg-red" /> Scan History Audit Logs
        </h1>
        <p className="text-gray-500 text-sm mt-1">
          Chronological record of all SBOM security audits performed by the scoring engine.
        </p>
      </div>

      {/* Search Input Bar */}
      <div className="bg-white border border-gray-200 rounded-lg p-4 mb-6 flex flex-col md:flex-row md:items-center gap-4 shadow-sm">
        <div className="relative flex-1">
          <Search size={18} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="Search scans by application name or filename..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-11 pr-4 py-2 border border-gray-200 bg-gray-50/50 rounded-md text-sm text-sg-navy placeholder-gray-400 focus:outline-none focus:border-sg-red focus:bg-white transition-all"
          />
        </div>
        <div className="text-gray-400 text-xs font-semibold whitespace-nowrap">
          Showing {filteredScans.length} of {allScans.length} total scans
        </div>
      </div>

      {isQuerying ? (
        <div className="bg-white border border-gray-200 rounded-lg p-16 text-center shadow-sm flex items-center justify-center">
          <Loader2 size={36} className="animate-spin text-sg-red" />
        </div>
      ) : error ? (
        <div className="bg-white border border-gray-200 rounded-lg p-12 text-center text-sg-danger">
          <ShieldAlert size={48} className="mx-auto mb-4 text-sg-red" />
          <h3 className="text-lg font-bold">Error Connecting to Backend</h3>
          <p className="text-gray-500 text-sm mt-1">Could not fetch portfolio scan history details.</p>
        </div>
      ) : filteredScans.length === 0 ? (
        <div className="bg-white border border-gray-200 rounded-lg p-16 text-center shadow-sm">
          <History size={48} className="mx-auto mb-4 text-sg-navy/30" />
          <h2 className="text-xl font-bold text-sg-navy">No Scan Records</h2>
          <p className="text-gray-500 text-sm max-w-md mx-auto mt-2">
            No audits have been executed yet or matching your search criteria.
          </p>
        </div>
      ) : (
        <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 text-left">
              <thead className="bg-gray-50">
                <tr className="text-xs font-bold text-gray-500 uppercase tracking-wider">
                  <th className="px-6 py-4">Scan Date</th>
                  <th className="px-6 py-4">Application / Project</th>
                  <th className="px-6 py-4">SBOM Source File</th>
                  <th className="px-6 py-4">Risk Score</th>
                  <th className="px-6 py-4">Status</th>
                  <th className="px-6 py-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 text-sm">
                {filteredScans.map((scan) => (
                  <tr key={scan.id} className="hover:bg-gray-50/50 transition-all">
                    <td className="px-6 py-4 whitespace-nowrap text-xs text-gray-400 font-semibold">
                      {new Date(scan.created_at).toLocaleString(undefined, {
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap font-bold text-sg-navy">
                      {scan.application_name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-xs text-gray-500 font-mono">
                      {scan.original_filename}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {scan.score !== null ? (
                        <span className={`inline-flex items-center gap-1 rounded px-2.5 py-0.5 text-xs font-bold font-mono ${getScoreBadgeClass(scan.score)}`}>
                          {scan.score}/100 ({scan.category})
                        </span>
                      ) : (
                        <span className="text-gray-400 text-xs">—</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getStatusBadge(scan.status)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-xs">
                      <Link
                        to={`/application/${scan.application_id}`}
                        className="inline-flex items-center font-bold text-sg-red hover:text-red-700 transition-all no-underline"
                      >
                        View Report &rarr;
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

    </div>
  );
}
