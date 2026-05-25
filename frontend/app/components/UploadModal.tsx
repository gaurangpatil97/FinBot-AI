"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import { createCompany, generateEmbeddings, uploadFile } from "../../lib/api";

import type {
  CollectionKey,
  EmbeddingStatus,
  FinancialQuarter,
  FiscalYear,
  SavedCollectionState,
  SavedDatasetSession,
  UploadedFileMetadata,
} from "./finbot-types";

interface UploadModalProps {
  open: boolean;
  session: SavedDatasetSession | null;
  companyName: string;
  ticker: string;
  onClose: () => void;
  onSave: (session: SavedDatasetSession) => void;
  onSessionUpdate: (session: SavedDatasetSession) => void;
}

interface DraftFileItem {
  id: string;
  name: string;
  status: EmbeddingStatus;
  year?: FiscalYear;
  quarter?: FinancialQuarter;
  file?: File;
}

const helperCopy: Record<CollectionKey, string> = {
  excel: "Balance sheets, P&L, cash flow and working capital models.",
  pdf: "Annual report PDFs with text and image pages processed separately.",
  concall: "Quarterly call transcripts, management commentary and Q&A.",
  images: "Charts, screenshots, board scans and visual reference docs.",
};

const zoneTitles: Record<CollectionKey, string> = {
  excel: "📊 Excel Financial Data",
  pdf: "📄 PDF Annual Reports",
  concall: "🎙️ Concall Transcripts",
  images: "🖼️ Images (from Annual Report)",
};

const zoneRules: Record<CollectionKey, string> = {
  excel: "Accepts .xlsx only",
  pdf: "Accepts .pdf only",
  concall: "Accepts .pdf only",
  images: "Accepts .pdf only",
};

const visibleKeys: CollectionKey[] = ["excel", "pdf", "concall"];

const statusCopy: Record<EmbeddingStatus, string> = {
  "no-embeddings": "🔴 No embeddings",
  processing: "🟡 Processing",
  uploaded: "🟣 Uploaded",
  ready: "🟢 Ready",
};

const fiscalYears: FiscalYear[] = ["FY20", "FY21", "FY22", "FY23", "FY24", "FY25", "FY26"];
const quarters: FinancialQuarter[] = ["Q1", "Q2", "Q3", "Q4"];

function createId() {
  return typeof crypto !== "undefined" && "randomUUID" in crypto ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`;
}

function slugifyCompanyName(companyName: string) {
  return companyName.trim().toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "");
}

function isAlreadyOnServer(status: EmbeddingStatus) {
  return status === "ready" || status === "uploaded";
}

function getExtension(fileName: string) {
  return fileName.split(".").pop()?.toLowerCase() ?? "";
}

function isValidFileForZone(key: CollectionKey, file: File) {
  const extension = getExtension(file.name);

  if (key === "excel") {
    return extension === "xlsx";
  }

  return extension === "pdf";
}

function defaultDraft(): Record<CollectionKey, DraftFileItem[]> {
  return {
    excel: [],
    pdf: [],
    concall: [],
    images: [],
  };
}

function collectionsFromDraft(draft: Record<CollectionKey, DraftFileItem[]>): SavedCollectionState[] {
  const descriptions: Record<CollectionKey, string> = {
    excel: "Structured financial statements and working capital schedules.",
    pdf: "Text and scanned pages processed independently.",
    concall: "Quarterly call transcripts and management commentary.",
    images: "Charts, screenshots, and scanned board notes.",
  };

  const labels: Record<CollectionKey, string> = {
    excel: "Excel Financial Data",
    pdf: "PDF Annual Reports",
    concall: "Concall Transcripts",
    images: "Image Dataset",
  };

  return (Object.keys(draft) as CollectionKey[]).map((key) => {
    const files = draft[key];
    const fileName =
      files.length === 0 ? "" : files.length === 1 ? files[0].name : `${files.length} files`;

    return {
      key,
      label: labels[key],
      description: descriptions[key],
      fileName,
      status: files.length === 0 ? "no-embeddings" : files.every((item) => item.status === "ready") ? "ready" : files.some((item) => item.status === "processing") ? "processing" : "no-embeddings",
      files: files.map((item) => ({
        id: item.id,
        collection: key,
        name: item.name,
        status: item.status,
        year: item.year,
        quarter: item.quarter,
      })),
    };
  });
}

function draftFromSession(session: SavedDatasetSession | null, companyName: string, ticker: string) {
  if (!session) {
    return {
      companyName,
      ticker,
      files: defaultDraft(),
    };
  }

  const files = defaultDraft();

  for (const collection of session.collections) {
    files[collection.key] = collection.files.map((item) => ({
      id: item.id,
      name: item.name,
      status: item.status,
      year: item.year,
      quarter: item.quarter,
    }));
  }

  return {
    companyName: session.companyName,
    ticker: session.ticker,
    files,
  };
}

export default function UploadModal({
  open,
  session,
  companyName,
  ticker,
  onClose,
  onSave,
  onSessionUpdate,
}: UploadModalProps) {
  const [draggingKey, setDraggingKey] = useState<CollectionKey | null>(null);
  const [draft, setDraft] = useState(() => draftFromSession(session, companyName, ticker));
  const [isSaving, setIsSaving] = useState(false);
  const [isGeneratingAll, setIsGeneratingAll] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const fileInputRefs = useRef<Record<CollectionKey, HTMLInputElement | null>>({
    excel: null,
    pdf: null,
    concall: null,
    images: null,
  });
  const timeouts = useRef<number[]>([]);
  const totalFiles = useMemo(
    () => (Object.keys(draft.files) as CollectionKey[]).reduce((count, key) => count + draft.files[key].length, 0),
    [draft.files],
  );

  useEffect(() => {
    if (!open) {
      return;
    }

    setDraft(draftFromSession(session, companyName, ticker));
    setErrorMessage(null);
  }, [open, session, companyName, ticker]);

  useEffect(
    () => () => {
      timeouts.current.forEach((timeoutId) => window.clearTimeout(timeoutId));
      timeouts.current = [];
    },
    [],
  );

  if (!open) {
    return null;
  }

  const updateFiles = (key: CollectionKey, updater: (current: DraftFileItem[]) => DraftFileItem[]) => {
    setDraft((current) => ({
      ...current,
      files: {
        ...current.files,
        [key]: updater(current.files[key]),
      },
    }));
  };

  const addFiles = (key: CollectionKey, fileList: FileList | null) => {
    const files = Array.from(fileList ?? []).filter((file) => isValidFileForZone(key, file));

    if (files.length === 0) {
      return;
    }

    updateFiles(key, (current) => {
      const baseItems: DraftFileItem[] = key === "excel" ? [] : current;

      if (key === "excel") {
        const file = files[0];
        return [{ id: createId(), name: file.name, file, status: "no-embeddings" }];
      }

      return [
        ...baseItems,
        ...files.map((file) => ({
          id: createId(),
          name: file.name,
          file,
          status: "no-embeddings" as EmbeddingStatus,
          year: "FY24" as FiscalYear,
          quarter: key === "concall" ? ("Q3" as FinancialQuarter) : undefined,
        })),
      ];
    });
  };

  const updateFile = (key: CollectionKey, fileId: string, changes: Partial<DraftFileItem>) => {
    updateFiles(key, (current) => current.map((file) => (file.id === fileId ? { ...file, ...changes } : file)));
  };

  const handleGenerate = (key: CollectionKey) => {
    updateFiles(key, (current) =>
      current.map((item) => (item.status === "ready" ? item : { ...item, status: "processing" })),
    );

    const timeoutId = window.setTimeout(() => {
      updateFiles(key, (current) => current.map((item) => ({ ...item, status: "ready" })));
    }, 900);

    timeouts.current.push(timeoutId);
  };

  const buildSessionFromDraft = (files: Record<CollectionKey, DraftFileItem[]>) => {
    const collections = collectionsFromDraft(files);

    return {
      companyName: draft.companyName.trim() || companyName,
      ticker: draft.ticker.trim() || ticker,
      collections,
      readyCollections: collections.filter((collection) => collection.status === "ready").length,
      chunks: 3500,
      savedAt: new Date().toISOString(),
    } satisfies SavedDatasetSession;
  };

  const handleGenerateAll = async () => {
    setErrorMessage(null);
    setIsGeneratingAll(true);

    try {
      const companyNameValue = draft.companyName.trim() || companyName;
      const companySlug = slugifyCompanyName(companyNameValue);
      const uploadTasks: Promise<unknown>[] = [];

      const uploadedInThisRun = new Set<string>();

      for (const key of visibleKeys) {
        for (const item of draft.files[key]) {
          if (isAlreadyOnServer(item.status)) {
            continue;
          }

          if (!item.file) {
            continue;
          }

          uploadedInThisRun.add(item.id);
          uploadTasks.push(uploadFile(item.file, companySlug, key, item.year, item.quarter));
        }
      }

      await Promise.all(uploadTasks);
      await generateEmbeddings(companySlug);

      const readyFiles = Object.fromEntries(
        (Object.keys(draft.files) as CollectionKey[]).map((key) => [
          key,
          draft.files[key].map((item) => ({
            ...item,
            status: isAlreadyOnServer(item.status) || uploadedInThisRun.has(item.id) ? ("ready" as EmbeddingStatus) : item.status,
          })),
        ]),
      ) as Record<CollectionKey, DraftFileItem[]>;

      setDraft((current) => ({
        ...current,
        files: readyFiles,
      }));

      onSessionUpdate(buildSessionFromDraft(readyFiles));
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Failed to generate embeddings");
    } finally {
      setIsGeneratingAll(false);
    }
  };

  const handleSave = async () => {
    setErrorMessage(null);
    setIsSaving(true);

    try {
      const companyNameValue = draft.companyName.trim() || companyName;
      const tickerValue = draft.ticker.trim() || ticker;
      const companySlug = slugifyCompanyName(companyNameValue);

      await createCompany(companyNameValue, companySlug, tickerValue);

      const nextSession = buildSessionFromDraft(draft.files);
      onSave(nextSession);
      onClose();
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Failed to save dataset");
    } finally {
      setIsSaving(false);
    }
  };

  const renderFileRow = (key: CollectionKey, file: DraftFileItem) => {
    const showQuarter = key === "concall";
    const showYear = key !== "excel";

    return (
      <div key={file.id} className="rounded-2xl border border-white/8 bg-[#11161d] p-3">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div className="min-w-0">
            <p className="truncate text-sm font-medium text-white">{file.name}</p>
            <div className="mt-2 flex flex-wrap gap-2 text-xs text-[#8b949e]">
              {showYear ? (
                <select
                  value={file.year ?? "FY24"}
                  onChange={(event) => updateFile(key, file.id, { year: event.target.value as FiscalYear })}
                  className="rounded-lg border border-white/8 bg-[#161b22] px-2.5 py-1.5 text-xs text-white outline-none"
                >
                  {fiscalYears.map((year) => (
                    <option key={year} value={year}>
                      {year}
                    </option>
                  ))}
                </select>
              ) : null}

              {showQuarter ? (
                <select
                  value={file.quarter ?? "Q3"}
                  onChange={(event) => updateFile(key, file.id, { quarter: event.target.value as FinancialQuarter })}
                  className="rounded-lg border border-white/8 bg-[#161b22] px-2.5 py-1.5 text-xs text-white outline-none"
                >
                  {quarters.map((quarter) => (
                    <option key={quarter} value={quarter}>
                      {quarter}
                    </option>
                  ))}
                </select>
              ) : null}
            </div>
          </div>

          <span className="inline-flex shrink-0 items-center rounded-full border border-white/8 bg-white/5 px-3 py-1 text-xs font-medium text-zinc-200">
            {statusCopy[file.status]}
          </span>
        </div>
      </div>
    );
  };

  const renderZone = (key: CollectionKey) => {
    const isActive = draggingKey === key;
    const files = draft.files[key];

    return (
      <section
        key={key}
        className={`flex min-h-80 flex-col rounded-3xl border border-dashed p-4 transition ${
          isActive ? "border-blue-400/60 bg-blue-500/10 shadow-[0_0_0_1px_rgba(47,129,247,0.3)]" : "border-[#30363d] bg-[#1c2128]"
        }`}
        onDragEnter={() => setDraggingKey(key)}
        onDragOver={(event) => {
          event.preventDefault();
          setDraggingKey(key);
        }}
        onDragLeave={() => setDraggingKey((current) => (current === key ? null : current))}
        onDrop={(event) => {
          event.preventDefault();
          setDraggingKey(null);
          addFiles(key, event.dataTransfer.files);
        }}
      >
        <div className="flex items-start justify-between gap-3">
          <div>
            <h3 className="text-base font-semibold text-white">{zoneTitles[key]}</h3>
            <p className="mt-1 text-sm text-[#8b949e]">{zoneRules[key]}</p>
            {key === "pdf" ? <p className="mt-2 text-xs text-[#8b949e]">Text and image pages will be processed separately.</p> : null}
          </div>
          <span className="rounded-full border border-white/8 bg-white/5 px-3 py-1 text-xs font-medium text-zinc-300">
            {statusCopy[files.length ? (files.every((item) => item.status === "ready") ? "ready" : files.some((item) => item.status === "processing") ? "processing" : "no-embeddings") : "no-embeddings"]}
          </span>
        </div>

        <label className="mt-4 flex cursor-pointer flex-col rounded-2xl border border-dashed border-[#30363d] bg-[#11161d] px-4 py-4 text-center transition hover:border-blue-400/45 hover:bg-blue-500/5">
          <input
            ref={(node) => {
              fileInputRefs.current[key] = node;
            }}
            type="file"
            multiple={key !== "excel"}
            accept={key === "excel" ? ".xlsx" : ".pdf"}
            className="hidden"
            onChange={(event) => {
              addFiles(key, event.target.files);
              event.currentTarget.value = "";
            }}
          />
          <span className="text-sm font-medium text-zinc-100">
            {files.length ? `${files.length} file${files.length > 1 ? "s" : ""} ready` : "Drop files here or click to browse"}
          </span>
          <span className="mt-2 text-xs text-[#8b949e]">{helperCopy[key]}</span>
        </label>

        <div className="mt-4 space-y-2">
          {files.length > 0 ? files.map((file) => renderFileRow(key, file)) : <p className="text-sm text-[#8b949e]">No files uploaded yet.</p>}
        </div>

        {key === "images" ? <p className="mt-3 text-xs text-[#8b949e]">Pages will be processed via GPT-4o vision.</p> : null}

      </section>
    );
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#0f1117]/80 px-4 py-6 backdrop-blur-sm">
      <div className="flex max-h-[92vh] w-full max-w-6xl flex-col overflow-hidden rounded-[30px] border border-white/10 bg-[#1c2128] shadow-[0_35px_90px_rgba(0,0,0,0.58)]">
        <div className="flex items-start justify-between border-b border-white/8 px-6 py-5">
          <div>
            <p className="text-xl font-semibold text-white">Upload Dataset</p>
            <p className="mt-1 text-sm text-[#8b949e]">Upload files to build your financial corpus</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="grid h-9 w-9 place-items-center rounded-full border border-white/8 bg-white/5 text-lg text-zinc-300 transition hover:bg-white/10"
          >
            X
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-6">
          {errorMessage ? (
            <div className="mb-4 rounded-2xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-200">
              {errorMessage}
            </div>
          ) : null}

          <div className="grid gap-4 md:grid-cols-2">
            <label className="space-y-2 rounded-3xl border border-white/8 bg-[#161b22] p-4">
              <span className="text-xs font-semibold uppercase tracking-[0.22em] text-[#8b949e]">Company Name</span>
              <input
                value={draft.companyName}
                onChange={(event) => setDraft((current) => ({ ...current, companyName: event.target.value }))}
                placeholder="e.g. Craftsman Automation Ltd"
                className="w-full rounded-2xl border border-white/8 bg-[#11161d] px-4 py-3 text-sm text-white outline-none placeholder:text-[#5c6673]"
              />
            </label>

            <label className="space-y-2 rounded-3xl border border-white/8 bg-[#161b22] p-4">
              <span className="text-xs font-semibold uppercase tracking-[0.22em] text-[#8b949e]">NSE/BSE Ticker</span>
              <input
                value={draft.ticker}
                onChange={(event) => setDraft((current) => ({ ...current, ticker: event.target.value }))}
                placeholder="e.g. CRAFTSMAN.NS"
                className="w-full rounded-2xl border border-white/8 bg-[#11161d] px-4 py-3 text-sm text-white outline-none placeholder:text-[#5c6673]"
              />
            </label>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            {visibleKeys.map((key) => renderZone(key))}
          </div>
        </div>

        <div className="border-t border-white/8 px-6 py-5">
          <button
            type="button"
            onClick={() => void handleGenerateAll()}
            disabled={isGeneratingAll}
            className="flex w-full items-center justify-center rounded-2xl bg-blue-500 px-5 py-3 text-sm font-semibold text-white transition hover:bg-blue-400 disabled:cursor-not-allowed disabled:opacity-70"
          >
            {isGeneratingAll ? (
              <span className="flex items-center gap-2">
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                Generating...
              </span>
            ) : (
              "Generate All Embeddings"
            )}
          </button>
          <button
            type="button"
            onClick={() => void handleSave()}
            disabled={isSaving || isGeneratingAll}
            className="mt-3 flex w-full items-center justify-center rounded-2xl border border-white/8 bg-white/5 px-5 py-3 text-sm font-semibold text-zinc-200 transition hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-70"
          >
            {isSaving ? "Saving..." : "Save & Close"}
          </button>
          <p className="mt-3 text-center text-xs text-[#8b949e]">{totalFiles} file{totalFiles === 1 ? "" : "s"} added</p>
        </div>
      </div>
    </div>
  );
}