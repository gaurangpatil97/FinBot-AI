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
    <div className="flex items-end gap-3 rounded-2xl border border-[#222222] bg-[#000000] p-3">
      <button
        type="button"
        onClick={onAttach}
        className="grid h-12 w-12 place-items-center rounded-xl border border-[#222222] bg-[#111111] text-lg text-white transition hover:bg-white/10"
        aria-label="Attach dataset"
      >
        📎
      </button>

      <label className="flex min-h-12 flex-1 items-start rounded-xl border border-[#222222] bg-[#111111] px-4 py-3 text-sm text-[#888888] focus-within:border-[#444444]">
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
          className="w-full resize-none overflow-x-hidden bg-transparent text-sm leading-5 text-white outline-none placeholder:text-[#8b949e]"
        />
      </label>

      <button
        type="button"
        onClick={onSend}
        className="inline-flex h-12 items-center gap-2 rounded-xl bg-white px-5 text-sm font-semibold text-black transition hover:bg-white/90"
      >
        <span>Send</span>
        <span>↗</span>
      </button>
    </div>
  );
}