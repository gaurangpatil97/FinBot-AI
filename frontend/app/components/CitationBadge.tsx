"use client";

interface CitationBadgeProps {
  label: string;
}

export default function CitationBadge({ label }: CitationBadgeProps) {
  return (
    <span className="inline-flex items-center rounded-full bg-[#1a1a1a] hover:bg-[#2a2a2a] border border-[#444] hover:border-[#666] px-2.5 py-1 text-[11px] font-medium tracking-wide text-zinc-300 hover:text-white cursor-pointer transition-colors">
      {label}
    </span>
  );
}