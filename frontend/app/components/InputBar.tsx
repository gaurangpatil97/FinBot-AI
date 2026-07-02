"use client";

import { useEffect, useRef, useState } from "react";
import { useSessions } from "../context/SessionContext";
import { exportTranscriptPdf, exportSummaryPdf, generateReportPdf } from "../../lib/api";

interface InputBarProps {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  onAttach: () => void;
  chartToggle: boolean;
  setChartToggle: (val: boolean) => void;
}

import ReportConfigModal from "./ReportConfigModal";

export default function InputBar({
  value,
  onChange,
  onSend,
  onAttach,
  chartToggle,
  setChartToggle,
}: InputBarProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { activeSessionId } = useSessions();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);
  const [reportModalOpen, setReportModalOpen] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  const toggleRecording = async () => {
    if (isRecording) {
      if (mediaRecorderRef.current) {
        mediaRecorderRef.current.stop();
      }
      setIsRecording(false);
    } else {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const mediaRecorder = new MediaRecorder(stream);
        mediaRecorderRef.current = mediaRecorder;
        audioChunksRef.current = [];

        mediaRecorder.ondataavailable = (event) => {
          if (event.data.size > 0) {
            audioChunksRef.current.push(event.data);
          }
        };

        mediaRecorder.onstop = async () => {
          setIsTranscribing(true);
          const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" });
          const formData = new FormData();
          formData.append("file", audioBlob, "voice_input.webm");

          try {
            const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
            const res = await fetch(`${BASE_URL}/api/voice/transcribe`, {
              method: "POST",
              body: formData,
            });
            if (!res.ok) throw new Error("Transcription failed");
            const data = await res.json();
            if (data.text) {
              onChange(value ? `${value} ${data.text}` : data.text);
            }
          } catch (err) {
            console.error("Transcription error:", err);
          } finally {
            stream.getTracks().forEach((track) => track.stop());
            setIsTranscribing(false);
          }
        };

        mediaRecorder.start();
        setIsRecording(true);
      } catch (err) {
        console.error("Microphone access error:", err);
      }
    }
  };

  useEffect(() => {
    const textarea = textareaRef.current;

    if (!textarea) {
      return;
    }

    const computedStyle = window.getComputedStyle(textarea);
    const lineHeight = Number.parseFloat(computedStyle.lineHeight || "20");
    const paddingTop = Number.parseFloat(computedStyle.paddingTop || "0");
    const paddingBottom = Number.parseFloat(computedStyle.paddingBottom || "0");
    const maxHeight = lineHeight * 5 + paddingTop + paddingBottom;

    textarea.style.height = "auto";
    textarea.style.overflowY = textarea.scrollHeight > maxHeight ? "auto" : "hidden";
    textarea.style.height = `${Math.min(textarea.scrollHeight, maxHeight)}px`;
  }, [value]);

  const handleExport = async (type: 'transcript' | 'summary' | 'report') => {
    if (!activeSessionId) {
      setExportError("No active session");
      return;
    }

    setDropdownOpen(false);

    if (type === 'report') {
      setReportModalOpen(true);
      return;
    }

    setIsExporting(true);
    setExportError(null);

    try {
      let blob: Blob;
      let filename: string;
      
      if (type === 'transcript') {
        const result = await exportTranscriptPdf(activeSessionId);
        blob = result.blob;
        filename = result.filename;
      } else {
        const result = await exportSummaryPdf(activeSessionId);
        blob = result.blob;
        filename = result.filename;
      }

      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (e: any) {
      console.error(e);
      setExportError(e.message || "Failed to export PDF");
    } finally {
      setIsExporting(false);
      // Auto-hide error after 3 seconds
      setTimeout(() => setExportError(null), 3000);
    }
  };

  return (
    <div className="flex flex-col gap-2">
      {exportError && (
        <div className="text-red-400 text-sm font-medium animate-pulse px-2">
          Error: {exportError}
        </div>
      )}
      
      {activeSessionId && (
        <ReportConfigModal 
          isOpen={reportModalOpen} 
          onClose={() => setReportModalOpen(false)} 
          sessionId={activeSessionId} 
        />
      )}

      <div className="flex items-end gap-3 rounded-2xl border border-[var(--border)] bg-[var(--bg)] p-3 relative">
        <button
          type="button"
          onClick={toggleRecording}
          disabled={isTranscribing}
          title={isTranscribing ? "Transcribing..." : isRecording ? "Stop recording" : "Record voice input"}
          aria-label={isTranscribing ? "Transcribing..." : isRecording ? "Stop recording" : "Record voice input"}
          className={`grid h-12 w-12 place-items-center shrink-0 rounded-xl border transition ${
            isTranscribing
              ? "border-[var(--border)] bg-[var(--surface-1)] text-[var(--text-muted)] cursor-not-allowed"
              : isRecording
                ? "border-[#ef4444] bg-[#ef4444]/10 text-[#ef4444] animate-pulse"
                : "border-[var(--border)] bg-[var(--surface-1)] text-[var(--text-secondary)] hover:bg-[var(--surface-2)] hover:text-[var(--text-primary)] hover:border-[var(--border-strong)]"
          }`}
        >
          {isTranscribing ? (
            <span className="h-4.5 w-4.5 animate-spin rounded-full border-2 border-transparent border-t-[var(--text-primary)]" />
          ) : isRecording ? (
            <span className="flex h-3 w-3 rounded-full bg-[#ef4444] animate-pulse" />
          ) : (
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="h-5 w-5"
            >
              <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
              <path d="M19 10v1a7 7 0 0 1-14 0v-1" />
              <line x1="12" y1="19" x2="12" y2="22" />
            </svg>
          )}
        </button>

        <label className="flex min-h-12 flex-1 items-start rounded-xl border border-[var(--border)] bg-[var(--surface-1)] px-4 py-3 text-sm text-[var(--text-secondary)] focus-within:border-[var(--border-strong)]">
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(event) => onChange(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                onSend();
              }
            }}
            placeholder="Ask about company financials..."
            rows={1}
            className="w-full resize-none overflow-x-hidden bg-transparent text-base leading-5 text-[var(--text-primary)] outline-none placeholder:text-[var(--text-muted)]"
          />
        </label>

        <div className="flex flex-wrap gap-2 self-center">
          <button
            type="button"
            onClick={() => setChartToggle(!chartToggle)}
            title="Generate chart and analyze trend"
            className={`flex h-12 items-center gap-2 px-3.5 rounded-xl border text-xs font-semibold cursor-pointer transition ${
              chartToggle
                ? "border-[#e8ddc7] bg-[#e8ddc7]/10 text-[#e8ddc7]"
                : "border-[var(--border)] bg-[var(--surface-1)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--border-strong)]"
            }`}
          >
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="h-4 w-4"
            >
              <path d="M3 3v18h18" />
              <path d="m19 9-5 5-4-4-3 3" />
            </svg>
            <span>Generate Chart</span>
          </button>

          {activeSessionId && (
            <div className="relative">
              <button
                type="button"
                onClick={() => setDropdownOpen(!dropdownOpen)}
                disabled={isExporting}
                className="flex h-12 items-center gap-2 px-3.5 rounded-xl border border-[#e8ddc7]/30 bg-[#e8ddc7]/5 text-xs font-semibold text-[#e8ddc7] cursor-pointer transition hover:bg-[#e8ddc7]/10 disabled:opacity-50"
              >
                {isExporting ? (
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-transparent border-t-[#e8ddc7]" />
                ) : (
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                    <polyline points="7 10 12 15 17 10"/>
                    <line x1="12" y1="15" x2="12" y2="3"/>
                  </svg>
                )}
                <span>Export PDF</span>
              </button>
              
              {dropdownOpen && (
                <div className="absolute bottom-[calc(100%+8px)] right-0 z-50 w-48 rounded-xl border border-[var(--border-strong)] bg-[var(--surface-2)] shadow-xl overflow-hidden">
                  <div className="flex flex-col py-1">
                    <button
                      onClick={() => handleExport('transcript')}
                      className="px-4 py-2.5 text-left text-sm text-[var(--text-primary)] hover:bg-[var(--surface-3)] transition-colors"
                    >
                      Export Transcript
                    </button>
                    <button
                      onClick={() => handleExport('summary')}
                      className="px-4 py-2.5 text-left text-sm text-[var(--text-primary)] hover:bg-[var(--surface-3)] transition-colors"
                    >
                      Export Summary
                    </button>
                    <button
                      onClick={() => handleExport('report')}
                      className="px-4 py-2.5 text-left text-sm text-[var(--text-primary)] hover:bg-[var(--surface-3)] transition-colors"
                    >
                      Generate Report
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          <button
            type="button"
            onClick={onSend}
            className="inline-flex h-12 items-center gap-2 rounded-xl bg-[#e8ddc7] px-5 text-sm font-semibold text-[#0a0a0c] transition opacity-100 hover:opacity-90"
          >
            <span>Send</span>
            <span>↗</span>
          </button>
        </div>
      </div>
    </div>
  );
}