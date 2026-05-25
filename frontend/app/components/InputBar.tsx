"use client";

interface InputBarProps {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  onAttach: () => void;
}

export default function InputBar({ value, onChange, onSend, onAttach }: InputBarProps) {
  return (
    <div className="flex items-end gap-3 rounded-2xl border border-white/8 bg-[#1c2128] p-3">
      <button
        type="button"
        onClick={onAttach}
        className="grid h-12 w-12 place-items-center rounded-xl border border-white/8 bg-[#11161d] text-lg text-zinc-300 transition hover:bg-white/5"
        aria-label="Attach dataset"
      >
        📎
      </button>

      <label className="flex min-h-12 flex-1 items-center rounded-xl border border-white/8 bg-[#11161d] px-4 text-sm text-[#8b949e] focus-within:border-blue-400/40">
        <input
          value={value}
          onChange={(event) => onChange(event.target.value)}
          placeholder="Ask about company financials..."
          className="w-full bg-transparent text-sm text-white outline-none placeholder:text-[#8b949e]"
        />
      </label>

      <button
        type="button"
        onClick={onSend}
        className="inline-flex h-12 items-center gap-2 rounded-xl bg-blue-500 px-5 text-sm font-semibold text-white transition hover:bg-blue-400"
      >
        <span>Send</span>
        <span>↗</span>
      </button>
    </div>
  );
}