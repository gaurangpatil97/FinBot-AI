"use client";

interface CitationBadgeProps {
  label: string;
}

export default function CitationBadge({ label }: CitationBadgeProps) {
  return (
    <span className="inline-flex items-center rounded-full bg-[#2f81f7] px-2.5 py-1 text-[11px] font-medium tracking-wide text-white">
      {label}
    </span>
  );
}