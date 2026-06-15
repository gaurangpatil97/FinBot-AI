"use client";

import { useState } from "react";
import { generateReportPdf } from "../../lib/api";

export interface ReportConfigModalProps {
  isOpen: boolean;
  onClose: () => void;
  sessionId: string;
}

const SECTION_OPTIONS = [
  { id: "executive_summary", label: "Executive Summary", defaultChecked: true },
  { id: "financial_highlights", label: "Financial Highlights (charts)", defaultChecked: true },
  { id: "ratio_analysis", label: "Ratio Analysis", defaultChecked: false },
  { id: "growth_analysis", label: "Growth Analysis", defaultChecked: false },
  { id: "risk_factors", label: "Risk Factors", defaultChecked: false },
  { id: "sources", label: "Sources", defaultChecked: true },
];

export default function ReportConfigModal({ isOpen, onClose, sessionId }: ReportConfigModalProps) {
  const [template, setTemplate] = useState("Financial Analysis Report");
  const [sections, setSections] = useState<Record<string, boolean>>(
    SECTION_OPTIONS.reduce((acc, opt) => ({ ...acc, [opt.id]: opt.defaultChecked }), {})
  );
  
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleToggle = (id: string) => {
    setSections((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const handleGenerate = async () => {
    setIsGenerating(true);
    setError(null);
    
    const selectedSections = Object.keys(sections).filter((id) => sections[id]);

    try {
      const result = await generateReportPdf(sessionId, template, selectedSections);
      const url = window.URL.createObjectURL(result.blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = result.filename;
      a.click();
      window.URL.revokeObjectURL(url);
      
      // Close modal on success
      setIsGenerating(false);
      onClose();
    } catch (e: any) {
      console.error(e);
      setError(e.message || "Failed to generate report PDF.");
      setIsGenerating(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div className="w-full max-w-lg rounded-2xl border border-[var(--border)] bg-[var(--surface-1)] shadow-2xl overflow-hidden flex flex-col">
        {/* Header */}
        <div className="border-b border-[var(--border)] p-5">
          <h2 className="text-xl font-bold text-[var(--text-primary)]">Generate Report</h2>
        </div>

        {/* Content */}
        <div className="p-6 flex flex-col gap-6">
          {isGenerating ? (
            <div className="flex flex-col items-center justify-center py-8">
              <div className="h-10 w-10 animate-spin rounded-full border-4 border-[var(--border)] border-t-[#e8ddc7] mb-4"></div>
              <p className="text-sm font-medium text-[var(--text-primary)]">Generating your report... this may take a minute.</p>
            </div>
          ) : (
            <>
              {error && (
                <div className="rounded-xl border border-red-900/50 bg-red-500/10 p-3 text-sm text-red-400">
                  {error}
                </div>
              )}

              {/* Template Dropdown */}
              <div className="flex flex-col gap-2">
                <label className="text-sm font-semibold text-[var(--text-primary)]">Template</label>
                <select 
                  value={template}
                  onChange={(e) => setTemplate(e.target.value)}
                  className="w-full rounded-xl border border-[var(--border)] bg-[var(--surface-2)] px-4 py-2.5 text-sm text-[var(--text-primary)] focus:border-[#e8ddc7] focus:outline-none focus:ring-1 focus:ring-[#e8ddc7]"
                >
                  <option value="Financial Analysis Report">Financial Analysis Report</option>
                  {/* More templates can be added here */}
                </select>
              </div>

              {/* Sections */}
              <div className="flex flex-col gap-3">
                <label className="text-sm font-semibold text-[var(--text-primary)]">Include Sections</label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {SECTION_OPTIONS.map((opt) => (
                    <label key={opt.id} className="flex items-center gap-3 cursor-pointer">
                      <div className="relative flex items-center">
                        <input 
                          type="checkbox" 
                          checked={sections[opt.id]} 
                          onChange={() => handleToggle(opt.id)}
                          className="peer h-5 w-5 appearance-none rounded border border-[var(--border)] bg-[var(--surface-2)] checked:border-[#e8ddc7] checked:bg-[#e8ddc7] focus:outline-none focus:ring-2 focus:ring-[#e8ddc7]/30 transition-all"
                        />
                        <svg className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 h-3.5 w-3.5 text-[#0a0a0c] opacity-0 peer-checked:opacity-100 transition-opacity pointer-events-none" viewBox="0 0 14 14" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <path d="M2.5 7L5.5 10L11.5 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        </svg>
                      </div>
                      <span className="text-sm text-[var(--text-secondary)]">{opt.label}</span>
                    </label>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-[var(--border)] bg-[var(--surface-2)] p-4 flex justify-end gap-3">
          <button
            type="button"
            disabled={isGenerating}
            onClick={onClose}
            className="rounded-xl px-4 py-2 text-sm font-semibold text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            type="button"
            disabled={isGenerating}
            onClick={handleGenerate}
            className="rounded-xl bg-[#e8ddc7] px-5 py-2 text-sm font-semibold text-[#0a0a0c] hover:opacity-90 transition disabled:opacity-50"
          >
            {isGenerating ? "Generating..." : "Generate Report"}
          </button>
        </div>
      </div>
    </div>
  );
}
