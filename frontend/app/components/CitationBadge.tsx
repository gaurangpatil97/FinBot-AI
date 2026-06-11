"use client";

interface CitationBadgeProps {
  label: string;
}

export default function CitationBadge({ label }: CitationBadgeProps) {
  return (
    <span className="inline-flex items-center rounded-full bg-[#1a1a1a] border border-[#444444] px-2.5 py-1 text-[11px] font-medium tracking-wide text-white">
      {label}
    </span>
  );
}