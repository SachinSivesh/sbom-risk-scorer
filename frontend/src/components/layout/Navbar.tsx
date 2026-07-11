import { Link } from 'react-router-dom';
import { Download, Layers } from 'lucide-react';
import { useUiStore } from '../../store/uiStore';
import { reportsApi } from '../../api/reports';

export default function Navbar() {
  const { currentApplicationName, currentSbomId } = useUiStore();

  const handleDownloadReport = async () => {
    if (!currentSbomId) return;
    try {
      const data = await reportsApi.get(currentSbomId);
      const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(data, null, 2));
      const downloadAnchor = document.createElement('a');
      downloadAnchor.setAttribute("href", dataStr);
      downloadAnchor.setAttribute("download", `sbom-risk-report-${currentSbomId}.json`);
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();
    } catch (err) {
      console.error('Failed to export report:', err);
    }
  };

  return (
    <header className="sticky top-0 z-40 flex h-16 w-full items-center justify-between border-b border-gray-200 bg-white px-6 shadow-sm print:hidden">
      {/* Brand Logo & Name */}
      <div className="flex items-center gap-3">
        <Link to="/" className="flex items-center gap-3 no-underline">
          {/* Societe Generale Logo */}
          <div className="flex h-8 w-8 flex-col overflow-hidden border border-gray-300 shadow-sm">
            <div className="h-[47%] w-full bg-sg-red" />
            <div className="h-[6%] w-full bg-white" />
            <div className="h-[47%] w-full bg-sg-black" />
          </div>
          <div className="flex flex-col">
            <span className="font-sans text-sm font-extrabold tracking-wider text-sg-black">SOCIETE GENERALE</span>
            <span className="font-sans text-xs font-semibold tracking-tight text-gray-500">SBOM RISK SCORER</span>
          </div>
        </Link>

        {/* Current Scan Pill */}
        {currentApplicationName && (
          <div className="ml-6 hidden items-center gap-2 rounded-full border border-gray-200 bg-gray-50 px-3.5 py-1 text-xs font-semibold text-sg-navy md:flex">
            <Layers size={12} className="text-gray-400" />
            <span className="text-gray-500 font-normal">Active Project:</span>
            <span className="font-bold">{currentApplicationName}</span>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex items-center gap-3">
        {currentSbomId && (
          <button
            onClick={handleDownloadReport}
            className="inline-flex items-center gap-2 rounded-md bg-sg-red px-4 py-2 text-xs font-bold text-white shadow-sm transition-all hover:bg-red-600 focus:outline-none focus:ring-2 focus:ring-sg-red/30 active:scale-95 cursor-pointer"
          >
            <Download size={14} />
            <span>DOWNLOAD REPORT JSON</span>
          </button>
        )}
      </div>
    </header>
  );
}
