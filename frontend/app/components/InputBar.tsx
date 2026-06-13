"use client";

import { useEffect, useRef } from "react";

interface InputBarProps {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  onAttach: () => void;
}

export default function InputBar({ value, onChange, onSend, onAttach }: InputBarProps) {
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
        className="grid h-12 w-12 place-items-center rounded-xl border border-[var(--border)] bg-[var(--surface-1)] text-lg text-[var(--text-primary)] transition hover:bg-[var(--surface-2)]"
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
          className="w-full resize-none overflow-x-hidden bg-transparent text-sm leading-5 text-[var(--text-primary)] outline-none placeholder:text-[var(--text-muted)]"
        />
      </label>

      <button
        type="button"
        onClick={onSend}
        className="inline-flex h-12 items-center gap-2 rounded-xl bg-[var(--accent)] px-5 text-sm font-semibold text-[var(--accent-fill-text)] transition opacity-100 hover:opacity-90"
      >
        <span>Send</span>
        <span>↗</span>
      </button>
    </div>
  );
}