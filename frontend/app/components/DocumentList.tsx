"use client";

import type { CollectionKey, DocumentRecord } from "./finbot-types";

interface DocumentListProps {
  documents: DocumentRecord[];
}

const sectionOrder: Array<{ key: CollectionKey; title: string; icon: string }> = [
  { key: "excel", title: "Excel", icon: "📊" },
  { key: "pdf", title: "PDF", icon: "📄" },
  { key: "concall", title: "Concall", icon: "🎙️" },
  { key: "images", title: "Images", icon: "🖼️" },
];

function statusDotClass(status: DocumentRecord["status"]) {
  if (status === "ready") {
    return "bg-emerald-400 shadow-[0_0_0_4px_rgba(52,211,153,0.12)]";
  }

  if (status === "processing") {
    return "bg-amber-400 shadow-[0_0_0_4px_rgba(251,191,36,0.12)]";
  }

  return "bg-rose-500 shadow-[0_0_0_4px_rgba(239,68,68,0.12)]";
}

export default function DocumentList({ documents }: DocumentListProps) {
  return (
    <section className="mt-4 space-y-4">
      <div>
        <h3 className="mb-3 text-xs font-semibold uppercase tracking-[0.22em] text-zinc-500">
          Documents
        </h3>
        <div className="space-y-4">
          {sectionOrder.map((section) => {
            const group = documents.filter((item) => item.group === section.key);

            return (
              <div key={section.key} className="space-y-2">
                <div className="flex items-center gap-2 text-sm font-semibold text-zinc-300">
                  <span>{section.icon}</span>
                  <span>{section.title}</span>
                  <span className="text-xs text-zinc-500">{group.length}</span>
                </div>
                <div className="space-y-2">
                  {group.map((item) => (
                    <div
                      key={item.id}
                      className="flex items-center justify-between rounded-xl border border-white/6 bg-[#11161d] px-3 py-2 text-sm text-zinc-200"
                    >
                      <span className="min-w-0 truncate pr-3">{item.name}</span>
                      <span className="flex items-center gap-2 text-xs text-zinc-500">
                        <span className={`h-2.5 w-2.5 rounded-full ${statusDotClass(item.status)}`} />
                        <span>
                          {item.status === "ready"
                            ? "Embedded"
                            : item.status === "processing"
                              ? "Processing"
                              : "Needs embedding"}
                        </span>
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}