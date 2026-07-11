import { useState, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, X, Loader2, CheckCircle, ShieldAlert } from 'lucide-react';
import { useUiStore } from '../../store/uiStore';
import { sbomsApi } from '../../api/upload';
import { useMutation, useQueryClient } from '@tanstack/react-query';

interface SbomUploadModalProps {
  applicationId?: string; // Optional, otherwise uses global selectedApplicationId
  onSuccess?: (sbomId: string) => void;
}

export default function SbomUploadModal({ applicationId, onSuccess }: SbomUploadModalProps) {
  const queryClient = useQueryClient();
  const { isUploadOpen, setIsUploadOpen, selectedApplicationId } = useUiStore();
  const targetAppId = applicationId || selectedApplicationId;

  const [file, setFile] = useState<File | null>(null);
  const [uploadState, setUploadState] = useState<'idle' | 'uploading' | 'processing' | 'success' | 'error'>('idle');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [currentStepIdx, setCurrentStepIdx] = useState<number>(0);
  const [sbomId, setSbomId] = useState<string | null>(null);

  const steps = [
    'Uploading SBOM file...',
    'Parsing SBOM packages & metadata...',
    'Building complete Dependency Graph...',
    'Checking CVE vulnerabilities...',
    'Analyzing software licenses compatibility...',
    'Performing GitHub repository maintenance checks...',
    'Generating Gemini AI Remediation Summary...',
    'Completed'
  ];

  // Reset state on open/close
  useEffect(() => {
    if (!isUploadOpen) {
      setFile(null);
      setUploadState('idle');
      setErrorMsg(null);
      setCurrentStepIdx(0);
      setSbomId(null);
    }
  }, [isUploadOpen]);

  // File Upload Mutation
  const uploadMutation = useMutation({
    mutationFn: ({ appId, file }: { appId: string; file: File }) => sbomsApi.upload(appId, file),
  });

  const onDrop = (acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setFile(acceptedFiles[0]);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/json': ['.json'] },
    maxFiles: 1,
    disabled: uploadState !== 'idle',
  });

  const handleStartUpload = async () => {
    if (!file || !targetAppId) return;

    setUploadState('uploading');
    setCurrentStepIdx(0);

    try {
      const response = await uploadMutation.mutateAsync({
        appId: targetAppId,
        file,
      });
      setSbomId(response.sbom_id);
      setUploadState('processing');
      setCurrentStepIdx(1); // Move to parsing
    } catch (err: any) {
      setUploadState('error');
      setErrorMsg(err.message || 'Failed to upload SBOM file.');
    }
  };

  // Poll status and animate timeline steps
  useEffect(() => {
    if (uploadState !== 'processing' || !sbomId) return;

    let timerId: any = null;
    let pollIntervalId: any = null;
    let isMounted = true;

    // Simulate step progress increments to make the corporate scan feel fluid
    const incrementStep = () => {
      setCurrentStepIdx((prev) => {
        if (prev < 6) return prev + 1; // Stay at AI summary generation until backend completes
        return prev;
      });
    };

    // Auto-advance step timeline slowly during analysis
    timerId = setInterval(incrementStep, 2500);

    const pollStatus = async () => {
      try {
        const res = await sbomsApi.status(sbomId);
        if (!isMounted) return;

        if (res.status === 'completed') {
          clearInterval(timerId);
          clearInterval(pollIntervalId);
          setCurrentStepIdx(7); // Completed
          setUploadState('success');
          
          // Refetch queries
          queryClient.invalidateQueries({ queryKey: ['application', targetAppId] });
          queryClient.invalidateQueries({ queryKey: ['applications'] });

          setTimeout(() => {
            if (onSuccess) onSuccess(sbomId);
            setIsUploadOpen(false);
          }, 1500);

        } else if (res.status === 'failed' || res.status === 'parse_failed') {
          clearInterval(timerId);
          clearInterval(pollIntervalId);
          setUploadState('error');
          setErrorMsg(res.error_detail || 'SBOM analysis failed.');
        } else if (res.status === 'parsing') {
          setCurrentStepIdx((prev) => Math.max(prev, 1));
        } else if (res.status === 'analyzing') {
          setCurrentStepIdx((prev) => Math.max(prev, 3));
        }
      } catch (err: any) {
        clearInterval(timerId);
        clearInterval(pollIntervalId);
        setUploadState('error');
        setErrorMsg(err.message || 'Error polling analysis status.');
      }
    };

    // Poll every 2 seconds
    pollIntervalId = setInterval(pollStatus, 2000);

    return () => {
      isMounted = false;
      clearInterval(timerId);
      clearInterval(pollIntervalId);
    };
  }, [uploadState, sbomId, targetAppId, queryClient, onSuccess, setIsUploadOpen]);

  if (!isUploadOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-sg-navy/60 backdrop-blur-sm">
      <div className="bg-white border border-gray-300 rounded-lg p-8 w-full max-w-lg shadow-2xl relative">
        
        {/* Close Button */}
        {uploadState !== 'uploading' && uploadState !== 'processing' && (
          <button
            onClick={() => setIsUploadOpen(false)}
            className="absolute top-4 right-4 text-gray-400 hover:text-sg-red transition-all cursor-pointer"
          >
            <X size={20} />
          </button>
        )}

        <h3 className="text-xl font-extrabold text-sg-navy mb-6 uppercase tracking-tight">
          Upload SBOM Version
        </h3>

        {/* 1. Drag & Drop Zone */}
        {uploadState === 'idle' && (
          <div className="space-y-6">
            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-lg p-10 text-center cursor-pointer transition-all flex flex-col items-center justify-center gap-4 ${
                isDragActive
                  ? 'border-sg-red bg-red-50/20'
                  : 'border-gray-300 bg-gray-50/50 hover:bg-gray-50 hover:border-gray-400'
              }`}
            >
              <input {...getInputProps()} />
              <Upload size={40} className="text-sg-red" />
              <div>
                <h4 className="text-sm font-bold text-sg-navy">Drag & Drop SBOM JSON here</h4>
                <p className="text-xs text-gray-400 mt-1">
                  CycloneDX or SPDX format up to 20MB
                </p>
              </div>
              <button type="button" className="rounded border border-gray-300 bg-white px-4 py-1.5 text-xs font-bold text-gray-500 hover:bg-gray-50 transition-all">
                Select File
              </button>
            </div>

            {file && (
              <div className="flex items-center justify-between rounded border border-gray-200 bg-gray-50 px-4 py-2.5 text-xs font-semibold text-sg-navy">
                <div className="truncate pr-4 font-mono">{file.name}</div>
                <div className="text-[10px] text-gray-400 shrink-0">({(file.size / 1024).toFixed(1)} KB)</div>
              </div>
            )}

            <div className="flex justify-end gap-3 pt-4 border-t border-gray-100">
              <button
                type="button"
                onClick={() => setIsUploadOpen(false)}
                className="rounded-md border border-gray-200 px-4 py-2 text-xs font-bold text-gray-500 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={!file}
                onClick={handleStartUpload}
                className="rounded-md bg-sg-red px-5 py-2 text-xs font-bold text-white hover:bg-red-600 disabled:bg-gray-200 disabled:text-gray-400 transition-all"
              >
                START SCAN ANALYSIS
              </button>
            </div>
          </div>
        )}

        {/* 2. Uploading Spinner */}
        {uploadState === 'uploading' && (
          <div className="text-center py-8">
            <Loader2 size={40} className="animate-spin text-sg-red mx-auto mb-4" />
            <h4 className="font-bold text-sg-navy">Uploading file...</h4>
            <p className="text-xs text-gray-400 mt-1">Sending SBOM data to the scanning engine.</p>
          </div>
        )}

        {/* 3. Processing Timeline steps */}
        {uploadState === 'processing' && (
          <div className="space-y-6 py-2">
            <div className="flex items-center gap-3 bg-gray-50 border border-gray-200 rounded p-4 mb-4">
              <Loader2 size={18} className="animate-spin text-sg-red shrink-0" />
              <div className="text-xs font-bold text-sg-navy">
                SCAN JOB RUNNING: <span className="font-normal text-gray-500">Do not close this panel.</span>
              </div>
            </div>

            <div className="space-y-4">
              {steps.slice(0, 7).map((step, idx) => {
                const isCurrent = idx === currentStepIdx;
                const isDone = idx < currentStepIdx;

                return (
                  <div key={idx} className="flex items-center gap-3 text-xs">
                    <div className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full border">
                      {isDone ? (
                        <div className="h-2.5 w-2.5 rounded-full bg-sg-success" />
                      ) : isCurrent ? (
                        <Loader2 size={12} className="animate-spin text-sg-red" />
                      ) : (
                        <div className="h-1.5 w-1.5 rounded-full bg-gray-300" />
                      )}
                    </div>
                    <span className={`font-semibold ${
                      isDone
                        ? 'text-gray-400 line-through'
                        : isCurrent
                        ? 'text-sg-red font-bold'
                        : 'text-gray-300'
                    }`}>
                      {step}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* 4. Success screen */}
        {uploadState === 'success' && (
          <div className="text-center py-8 space-y-4">
            <CheckCircle size={48} className="text-sg-success mx-auto" />
            <div>
              <h4 className="font-bold text-sg-navy text-lg">Analysis Completed</h4>
              <p className="text-xs text-gray-400 mt-1">SBOM has been processed and scored successfully.</p>
            </div>
          </div>
        )}

        {/* 5. Error screen */}
        {uploadState === 'error' && (
          <div className="text-center py-4 space-y-6">
            <ShieldAlert size={48} className="text-sg-danger mx-auto" />
            <div>
              <h4 className="font-bold text-sg-navy text-lg">Scan Execution Failed</h4>
              <p className="text-xs text-sg-danger font-medium mt-2 bg-red-50 border border-sg-danger/10 p-3 rounded font-mono break-words">
                {errorMsg}
              </p>
            </div>
            <div className="flex justify-center gap-3 border-t border-gray-100 pt-4">
              <button
                type="button"
                onClick={() => setUploadState('idle')}
                className="rounded border border-gray-300 bg-white px-4 py-2 text-xs font-bold text-gray-500 hover:bg-gray-50"
              >
                Try Again
              </button>
              <button
                type="button"
                onClick={() => setIsUploadOpen(false)}
                className="rounded bg-sg-navy text-white px-4 py-2 text-xs font-bold hover:bg-sg-navy/90"
              >
                Close Dialog
              </button>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
