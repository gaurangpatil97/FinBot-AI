"use client";

import { useEffect, useRef } from "react";

interface InputBarProps {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  onAttach: () => void;
  chartToggle: boolean;
  setChartToggle: (val: boolean) => void;
}

export default function InputBar({
  value,
  onChange,
  onSend,
  onAttach,
  chartToggle,
  setChartToggle,
}: InputBarProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

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

  return (
    <div className="flex items-end gap-3 rounded-2xl border border-[var(--border)] bg-[var(--bg)] p-3">
      <button
        type="button"
        onClick={onAttach}
        className="grid h-12 w-12 place-items-center rounded-xl border border-[var(--border)] bg-[var(--surface-1)] text-lg text-[var(--text-secondary)] transition hover:bg-[var(--surface-2)]"
        aria-label="Attach dataset"
      >
        📎
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

      <div className="flex gap-2 self-center">
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
      </div>

      <button
        type="button"
        onClick={onSend}
        className="inline-flex h-12 items-center gap-2 rounded-xl bg-[#e8ddc7] px-5 text-sm font-semibold text-[#0a0a0c] transition opacity-100 hover:opacity-90"
      >
        <span>Send</span>
        <span>↗</span>
      </button>
    </div>
  );
}