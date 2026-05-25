"use client";

import type { CollectionRecord } from "./finbot-types";

interface CorpusStatusProps {
  collections: CollectionRecord[];
}

function statusMeta(status: CollectionRecord["status"] | "none") {
  if (status === "ready") {
    return { dot: "bg-emerald-400", text: "text-zinc-300" };
  }

  if (status === "processing") {
    return { dot: "bg-amber-400", text: "text-zinc-300" };
  }

  return { dot: "bg-rose-500", text: "text-zinc-400" };
}

export default function CorpusStatus({ collections }: CorpusStatusProps) {
  const rows = [
    {
      icon: "📊",
      label: "Excel",
      collection: collections.find((item) => item.key === "excel"),
    },
    {
      icon: "📄",
      label: "PDF Text",
      collection: collections.find((item) => item.key === "pdf"),
    },
    {
      icon: "🖼️",
      label: "Images",
      collection: collections.find((item) => item.key === "images"),
    },
    {
      icon: "🎙️",
      label: "Concall",
      collection: collections.find((item) => item.key === "concall"),
    },
  ];

  return (
    <section className="rounded-2xl border border-white/8 bg-[#1c2128] p-4">
      <p className="text-xs font-semibold uppercase tracking-[0.24em] text-[#8b949e]">Corpus Status</p>
      <div className="mt-4 space-y-3">
        {rows.map((row) => {
          const collection = row.collection;
          const meta = statusMeta(collection?.status ?? "none");
          const chunks =
            collection?.status === "ready"
              ? collection.key === "excel"
                ? "847 chunks"
                : collection.key === "pdf"
                  ? "2,341 chunks"
                  : collection.key === "images"
                    ? "Processing"
                    : "No data"
              : collection?.status === "processing"
                ? "Processing"
                : "No data";

          return (
            <div key={row.label} className="flex items-center justify-between gap-3 px-1 py-1.5">
              <div className="flex min-w-0 items-center gap-2 text-sm text-zinc-200">
                <span>{row.icon}</span>
                <span className="truncate">{row.label}</span>
              </div>
              <div className="flex shrink-0 items-center gap-2 text-sm text-zinc-300">
                <span className={`h-2.5 w-2.5 rounded-full ${meta.dot}`} />
                <span>{chunks}</span>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}