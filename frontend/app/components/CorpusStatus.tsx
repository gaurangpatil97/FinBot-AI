"use client";

import { useState } from "react";

import { getCompanyFiles } from "../../lib/api";

import type { CollectionKey, CollectionRecord, CorpusFileRecord } from "./finbot-types";

interface CorpusStatusProps {
  collections: CollectionRecord[];
  filesByCollection: Record<CollectionKey, CorpusFileRecord[]>;
  companySlug: string;
}

type RemoteFileMetadata = {
  chunks: number;
  year?: string | null;
  quarter?: string | null;
};

type StatusCollectionRecord = {
  status?: CollectionRecord["status"];
  chunks?: number;
};

type StatusResponseLike = {
  collections: Partial<Record<CollectionKey, StatusCollectionRecord>>;
};

type RemoteCompanyFiles = Partial<Record<CollectionKey, Record<string, number | RemoteFileMetadata>>>;
type RemoteFileRow = {
  name: string;
  chunks: number;
  year?: string | null;
  quarter?: string | null;
};

function statusMeta(collection: CollectionRecord | undefined) {
  if (!collection) {
    return { dot: "bg-[#52525b]", text: "text-[var(--text-secondary)]" };
  }

  if (collection.status === "processing") {
    return { dot: "bg-amber-500 animate-pulse", text: "text-amber-500" };
  }

  if (collection.status === "failed") {
    return { dot: "bg-red-500", text: "text-red-500" };
  }

  if ((collection.chunks ?? 0) > 0) {
    return { dot: "bg-[#22c55e]", text: "text-[#22c55e]" };
  }

  return { dot: "bg-[#52525b]", text: "text-[#52525b]" };
}

function statusLabel(collection: CollectionRecord | undefined) {
  if (!collection) {
    return "No data";
  }

  if (collection.status === "processing") {
    return "Processing";
  }

  if (collection.status === "no-embeddings") {
    return "No data";
  }

  if (collection.status === "ready") {
    const chunks = collection.chunks ?? 0;
    return `${chunks} chunks`;
  }

  if (collection.status === "failed") {
    return "No data";
  }

  return "No data";
}

function totalChunks(files: CorpusFileRecord[]) {
  return files.reduce((sum, file) => sum + (typeof file.chunks === "number" ? file.chunks : 0), 0);
}

function formatPeriodTag(year?: string | null, quarter?: string | null) {
  const parts = [year?.trim(), quarter?.trim()].filter((part): part is string => Boolean(part) && part !== "unknown");

  return parts.length > 0 ? parts.join(" ") : null;
}

function displayFilename(filename: string) {
  const trimmed = filename.trim();

  if (trimmed.length <= 32) {
    return trimmed;
  }

  const patterns = [
    /((?:FY\d{2})[_\s-]*Q[1-4](?:\.[A-Za-z0-9]+)?)$/i,
    /((?:19|20)\d{2}[_-][A-Za-z]{3}(?:\.[A-Za-z0-9]+)?)$/i,
    /((?:19|20)\d{2}[-_]\d{2}(?:\.[A-Za-z0-9]+)?)$/i,
  ];

  for (const pattern of patterns) {
    const match = trimmed.match(pattern);
    if (match?.[1]) {
      return match[1].replace(/\s+/g, " ");
    }
  }

  return trimmed;
}

export default function CorpusStatus({ collections, filesByCollection, companySlug }: CorpusStatusProps) {
  const status: StatusResponseLike = {
    collections: Object.fromEntries(
      collections.map((collection) => [collection.key, { status: collection.status, chunks: collection.chunks }]),
    ) as Partial<Record<CollectionKey, StatusCollectionRecord>>,
  };

  const [expanded, setExpanded] = useState<Record<CollectionKey, boolean>>({
    excel: false,
    pdf: false,
    concall: false,
    images: false,
  });
  const [remoteFiles, setRemoteFiles] = useState<Partial<Record<CollectionKey, RemoteFileRow[]>>>({});
  const [isLoadingFiles, setIsLoadingFiles] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);

  const loadFiles = async () => {
    if (!companySlug.trim()) {
      return;
    }

    setIsLoadingFiles(true);
    setLoadError(null);

    try {
      const response = (await getCompanyFiles(companySlug)) as RemoteCompanyFiles;
      const mapped: Partial<Record<CollectionKey, RemoteFileRow[]>> = {};

      for (const key of ["excel", "pdf", "concall", "images"] as const) {
        const entry = response[key];
        if (!entry || typeof entry !== "object") {
          mapped[key] = [];
          continue;
        }

        mapped[key] = Object.entries(entry)
          .map(([name, value]) => {
            if (typeof value === "number") {
              return { name, chunks: value };
            }

            return {
              name,
              chunks: typeof value.chunks === "number" ? value.chunks : 0,
              year: value.year ?? null,
              quarter: value.quarter ?? null,
            };
          })
          .sort((a, b) => b.chunks - a.chunks);
      }

      setRemoteFiles(mapped);
    } catch {
      setLoadError("Details unavailable");
    } finally {
      setIsLoadingFiles(false);
    }
  };

  const handleToggle = async (key: CollectionKey) => {
    const isOpening = !expanded[key];

    setExpanded((current) => ({ ...current, [key]: !current[key] }));

    if (isOpening && !remoteFiles[key] && !isLoadingFiles) {
      await loadFiles();
    }
  };

  const rows = [
    {
      icon: "📊",
      label: "Excel",
      key: "excel" as CollectionKey,
      collection: collections.find((item) => item.key === "excel"),
    },
    {
      icon: "📄",
      label: "PDF Text",
      key: "pdf" as CollectionKey,
      collection: collections.find((item) => item.key === "pdf"),
    },
    {
      icon: "🖼️",
      label: "Images",
      key: "images" as CollectionKey,
      collection: collections.find((item) => item.key === "images"),
    },
    {
      icon: "🎙️",
      label: "Concall",
      key: "concall" as CollectionKey,
      collection: collections.find((item) => item.key === "concall"),
    },
  ];

  return (
    <section className="rounded-2xl border border-[var(--border)] bg-[var(--surface-1)] p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]">
      <p className="text-sm font-medium text-[var(--text-secondary)]">Corpus Status</p>
      <div className="mt-4 space-y-3">
        {rows.map((row) => {
            const collection = row.collection;
            const backendCollection = status.collections[row.key];
            const resolvedCollection = collection
              ? {
                  ...collection,
                  status: backendCollection?.status ?? collection.status,
                  chunks: typeof backendCollection?.chunks === "number" ? backendCollection.chunks : collection.chunks,
                }
              : collection;
            const meta = statusMeta(resolvedCollection);
          const files = filesByCollection[row.key] ?? [];
            const total = typeof backendCollection?.chunks === "number" ? backendCollection.chunks : totalChunks(files);
          const chunkSummary = `${total} chunks`;
          const isExpanded = expanded[row.key];

          return (
            <div key={row.label} className="rounded-xl border border-[var(--border)] bg-transparent px-2 py-1">
              <button
                type="button"
                onClick={() => void handleToggle(row.key)}
                className="flex w-full items-center justify-between gap-3 px-1 py-1.5"
              >
                <div className="flex min-w-0 items-center gap-2 text-sm text-[var(--text-primary)]">
                  <span>{row.icon}</span>
                  <span className="truncate">{row.label}</span>
                </div>
                <div className="flex shrink-0 items-center gap-2 text-sm text-[var(--text-primary)]">
                  <span className={`h-2.5 w-2.5 rounded-full ${meta.dot}`} />
                  <span className="font-mono tabular-nums num">{chunkSummary}</span>
                  <span className={`text-xs text-[var(--text-secondary)] transition ${isExpanded ? "rotate-180" : ""}`}>⌄</span>
                </div>
              </button>

              <div className={`${isExpanded ? "block" : "hidden"} border-t border-[var(--border)] px-1 pb-2 pt-2`}>
                {isLoadingFiles ? <p className="text-xs text-[var(--text-secondary)]">Loading files...</p> : null}
                {loadError ? <p className="text-xs text-rose-300">{loadError}</p> : null}
                {!isLoadingFiles && !loadError ? (
                  <div className="space-y-1.5">
                    {(remoteFiles[row.key] ?? []).map((file) => (
                      <div
                        key={`${row.key}-${file.name}`}
                        title={file.name}
                        className="flex items-center justify-between gap-2 rounded-lg bg-[var(--bg)] px-2.5 py-2"
                      >
                        <p className="min-w-0 truncate text-xs text-[var(--text-primary)]">{displayFilename(file.name)}</p>
                        <p className="shrink-0 text-xs text-[var(--text-secondary)] font-mono tabular-nums num">
                          {formatPeriodTag(file.year, file.quarter) ? `${formatPeriodTag(file.year, file.quarter)} · ` : ""}
                          {file.chunks} chunks
                        </p>
                      </div>
                    ))}
                    {(remoteFiles[row.key] ?? []).length === 0 ? (
                      <p className="text-xs text-[var(--text-secondary)] font-mono tabular-nums num">Total: {total} chunks</p>
                    ) : null}
                  </div>
                ) : null}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}