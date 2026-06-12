"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import { createCompany, generateEmbeddings, getCompanyStatus, uploadFile } from "../../lib/api";

import type {
  CollectionKey,
  CollectionRecord,
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
  onEmbeddingComplete: (companySlug: string) => Promise<void> | void;
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

const fiscalYears: FiscalYear[] = ["FY20", "FY21", "FY22", "FY23", "FY24", "FY25", "FY26"];
const quarters: FinancialQuarter[] = ["Q1", "Q2", "Q3", "Q4"];

const EMBEDDING_POLL_INTERVAL_MS = 3000;
const EMBEDDING_POLL_TIMEOUT_MS = 120000;

function createId() {
  return typeof crypto !== "undefined" && "randomUUID" in crypto ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`;
}

function slugifyCompanyName(companyName: string) {
  return companyName.toLowerCase().replace(/\s+/g, "_").replace(/[^a-z0-9_]/g, "");
}

function isAlreadyOnServer(status: EmbeddingStatus) {
  return status === "ready" || status === "uploaded";
}

function mapCollectionStatus(status: unknown): EmbeddingStatus {
  if (typeof status !== "string") {
    return "no-embeddings";
  }

  if (status === "ready" || status === "processing" || status === "uploaded" || status === "failed") {
    return status;
  }

  if (status === "error") {
    return "failed";
  }

  return "no-embeddings";
}

function delay(ms: number) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

type BackendCollectionStatus = {
  status?: unknown;
  chunks?: unknown;
};

type BackendCompanyStatus = {
  name?: unknown;
  slug?: unknown;
  ticker?: unknown;
  collections?: Record<string, BackendCollectionStatus>;
};

function buildCollectionsFromBackendStatus(
  backendStatus: BackendCompanyStatus,
  fallbackCollections: CollectionRecord[],
) {
  return fallbackCollections.map((fallback) => {
    const backendCollection = backendStatus.collections?.[fallback.key] ?? {};
    const chunks = typeof backendCollection.chunks === "number" ? backendCollection.chunks : fallback.chunks;

    return {
      ...fallback,
      status: mapCollectionStatus(backendCollection.status ?? fallback.status),
      chunks,
    };
  });
}

function getSessionFilenames(sessionValue: SavedDatasetSession | null) {
  const filenames = new Set<string>();

  if (!sessionValue) {
    return filenames;
  }

  for (const collection of sessionValue.collections) {
    for (const file of collection.files) {
      if (typeof file.name === "string" && file.name.trim()) {
        filenames.add(file.name.trim().toLowerCase());
      }
    }
  }

  return filenames;
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
      status: files.length === 0
        ? "no-embeddings"
        : files.every((item) => item.status === "ready")
          ? "ready"
          : files.some((item) => item.status === "failed")
            ? "failed"
            : files.some((item) => item.status === "processing" || item.status === "uploaded")
              ? "processing"
              : "no-embeddings",
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

  return {
    companyName: session.companyName,
    ticker: session.ticker,
    files: defaultDraft(),
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
  onEmbeddingComplete,
}: UploadModalProps) {
  const [draggingKey, setDraggingKey] = useState<CollectionKey | null>(null);
  const [draft, setDraft] = useState(() => draftFromSession(session, companyName, ticker));
  const [isSaving, setIsSaving] = useState(false);
  const [isGeneratingAll, setIsGeneratingAll] = useState(false);
  const [isEmbedding, setIsEmbedding] = useState(false);
  const [isPollingEmbedding, setIsPollingEmbedding] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const fileInputRefs = useRef<Record<CollectionKey, HTMLInputElement | null>>({
    excel: null,
    pdf: null,
    concall: null,
    images: null,
  });
  const timeouts = useRef<number[]>([]);
  const toastTimeout = useRef<number | null>(null);
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
    setToastMessage(null);
    setIsEmbedding(false);
    setIsPollingEmbedding(false);
    setIsGeneratingAll(false);
  }, [open, session, companyName, ticker]);

  useEffect(
    () => () => {
      timeouts.current.forEach((timeoutId) => window.clearTimeout(timeoutId));
      timeouts.current = [];
      if (toastTimeout.current) {
        window.clearTimeout(toastTimeout.current);
      }
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

    let ignoredDuplicate = false;

    updateFiles(key, (current) => {
      const existingNames = new Set(current.map((item) => item.name.trim().toLowerCase()));

      if (key === "excel") {
        const file = files[0];
        if (existingNames.has(file.name.trim().toLowerCase())) {
          ignoredDuplicate = true;
          return current;
        }

        return [{ id: createId(), name: file.name, file, status: "no-embeddings" }];
      }

      const nextItems = [...current];

      for (const file of files) {
        const normalizedName = file.name.trim().toLowerCase();

        if (existingNames.has(normalizedName)) {
          ignoredDuplicate = true;
          continue;
        }

        existingNames.add(normalizedName);
        nextItems.push({
          id: createId(),
          name: file.name,
          file,
          status: "no-embeddings" as EmbeddingStatus,
          year: "FY24" as FiscalYear,
          quarter: key === "concall" ? ("Q3" as FinancialQuarter) : undefined,
        });
      }

      return nextItems;
    });

    if (ignoredDuplicate) {
      showToast("File already added.");
    }
  };

  const updateFile = (key: CollectionKey, fileId: string, changes: Partial<DraftFileItem>) => {
    updateFiles(key, (current) => current.map((file) => (file.id === fileId ? { ...file, ...changes } : file)));
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

  const showToast = (message: string) => {
    setToastMessage(message);

    if (toastTimeout.current) {
      window.clearTimeout(toastTimeout.current);
    }

    toastTimeout.current = window.setTimeout(() => {
      setToastMessage(null);
    }, 2200);
  };

  const waitForEmbeddingCompletion = async (companySlug: string) => {
    const startedAt = Date.now();

    while (Date.now() - startedAt < EMBEDDING_POLL_TIMEOUT_MS) {
      const status = (await getCompanyStatus(companySlug)) as BackendCompanyStatus;

      const values = Object.values(status.collections ?? {});
      const stillProcessing = values.some((collection) => mapCollectionStatus(collection.status) === "processing");

      if (!stillProcessing) {
        return;
      }
      await delay(EMBEDDING_POLL_INTERVAL_MS);
    }
  };

  const handleGenerateAll = async () => {
    if (isEmbedding) {
      showToast("Embedding in progress, please wait");
      return;
    }

    setErrorMessage(null);

    setIsGeneratingAll(true);
    setIsEmbedding(true);
    setIsPollingEmbedding(false);

    try {
      const companyNameValue = draft.companyName.trim() || companyName;
      const tickerValue = draft.ticker.trim() || ticker;
      const companySlug = slugifyCompanyName(companyNameValue);
      await createCompany(companyNameValue, companySlug, tickerValue);

      const existingFilenames = getSessionFilenames(session);
      const uploadTasks: Promise<{ fileId: string; ok: boolean }>[] = [];

      for (const key of visibleKeys) {
        for (const item of draft.files[key]) {
          if (isAlreadyOnServer(item.status)) {
            continue;
          }

          if (!item.file) {
            continue;
          }

          if (existingFilenames.has(item.file.name.trim().toLowerCase())) {
            continue;
          }
          uploadTasks.push(
            uploadFile(item.file, companySlug, key, item.year, item.quarter)
              .then(() => ({ fileId: item.id, ok: true }))
              .catch(() => ({ fileId: item.id, ok: false })),
          );
        }
      }

      await Promise.all(uploadTasks);

      await generateEmbeddings(companySlug).catch((error) => {
        throw error instanceof Error ? error : new Error("Failed to start embedding");
      });

      setIsPollingEmbedding(true);
      await waitForEmbeddingCompletion(companySlug);

      const nextSession = buildSessionFromDraft(draft.files);
      onSessionUpdate(nextSession);
      await onEmbeddingComplete(companySlug);
      onClose();
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to generate embeddings";
      setErrorMessage(message);
    } finally {
      setIsGeneratingAll(false);
      setIsEmbedding(false);
      setIsPollingEmbedding(false);
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

      if (typeof window !== "undefined") {
        window.localStorage.setItem(
          "activeCompany",
          JSON.stringify({ name: companyNameValue, slug: companySlug, ticker: tickerValue }),
        );
      }

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
      <div key={file.id} className="rounded-2xl border border-[var(--border)] bg-[var(--surface-1)] p-3">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div className="min-w-0">
            <p className="truncate text-sm font-medium text-white">{file.name}</p>
            <div className="mt-2 flex flex-wrap gap-2 text-xs text-[#888888]">
              {showYear ? (
                <select
                  value={file.year ?? "FY24"}
                  onChange={(event) => updateFile(key, file.id, { year: event.target.value as FiscalYear })}
                  className="rounded-lg border border-[var(--border)] bg-[var(--surface-1)] px-2.5 py-1.5 text-xs text-[var(--text-primary)] outline-none"
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
                  className="rounded-lg border border-[var(--border)] bg-[var(--surface-1)] px-2.5 py-1.5 text-xs text-[var(--text-primary)] outline-none"
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
        className={`flex min-h-80 flex-col rounded-3xl border border-dashed p-4 transition duration-200 ${
          isActive ? "border-[var(--accent)] bg-[var(--accent-dim)] scale-[1.01]" : "border-[var(--border)] bg-[var(--surface-2)]"
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
            <p className="mt-1 text-sm text-[#888888]">{zoneRules[key]}</p>
            {key === "pdf" ? <p className="mt-2 text-xs text-[#888888]">Text and image pages will be processed separately.</p> : null}
          </div>
        </div>

        <label className="mt-4 flex cursor-pointer flex-col rounded-2xl border border-dashed border-[var(--border)] bg-[var(--surface-1)] px-4 py-4 text-center transition hover:border-[var(--accent)] hover:bg-[var(--accent-dim)]">
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
          <span className="mt-2 text-xs text-[#888888]">{helperCopy[key]}</span>
        </label>

        <div className="mt-4 space-y-2">
          {files.length > 0 ? files.map((file) => renderFileRow(key, file)) : <p className="text-sm text-[#888888]">No files uploaded yet.</p>}
        </div>

        {key === "images" ? <p className="mt-3 text-xs text-[#888888]">Pages will be processed via GPT-4o vision.</p> : null}

      </section>
    );
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[var(--bg)]/80 px-4 py-6 backdrop-blur-sm">
      <div className="flex max-h-[92vh] w-full max-w-6xl flex-col overflow-hidden rounded-[30px] border border-[var(--border)] bg-[var(--surface-1)] shadow-[0_35px_90px_rgba(0,0,0,0.58)]">
        <div className="flex items-start justify-between border-b border-[var(--border)] px-6 py-5">
          <div>
            <p className="text-xl font-semibold text-[var(--text-primary)]">Upload Dataset</p>
            <p className="mt-1 text-sm text-[var(--text-secondary)]">Upload files to build your financial corpus</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="grid h-9 w-9 place-items-center rounded-full border border-[var(--border)] bg-[var(--surface-2)] text-lg text-[var(--text-primary)] transition hover:bg-[var(--border)]"
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
            <label className="space-y-2 rounded-3xl border border-[var(--border)] bg-[var(--surface-2)] p-4">
              <span className="text-sm font-medium text-[var(--text-secondary)]">Company Name</span>
              <input
                value={draft.companyName}
                onChange={(event) => setDraft((current) => ({ ...current, companyName: event.target.value }))}
                placeholder="e.g. Craftsman Automation Ltd"
                className="w-full rounded-2xl border border-[var(--border)] bg-[var(--surface-1)] px-4 py-3 text-sm text-[var(--text-primary)] outline-none placeholder:text-[var(--text-secondary)]"
              />
            </label>

            <label className="space-y-2 rounded-3xl border border-[var(--border)] bg-[var(--surface-2)] p-4">
              <span className="text-sm font-medium text-[var(--text-secondary)]">NSE/BSE Ticker</span>
              <input
                value={draft.ticker}
                onChange={(event) => setDraft((current) => ({ ...current, ticker: event.target.value }))}
                placeholder="e.g. CRAFTSMAN.NS"
                className="w-full rounded-2xl border border-[var(--border)] bg-[var(--surface-1)] px-4 py-3 text-sm text-[var(--text-primary)] outline-none placeholder:text-[var(--text-secondary)]"
              />
            </label>
          </div>

          <div className="grid gap-4 md:grid-cols-2 mt-6">
            {renderZone("excel")}
            {renderZone("pdf")}
            <div className="md:col-span-2">
              {renderZone("concall")}
            </div>
          </div>
        </div>

        <div className="border-t border-[var(--border)] px-6 py-5 flex items-center justify-end gap-3">
          <p className="mr-auto text-xs text-[var(--text-secondary)]">{totalFiles} file{totalFiles === 1 ? "" : "s"} added</p>
          
          {toastMessage ? (
            <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-2)] px-4 py-2.5 text-sm text-[var(--text-primary)]">
              {toastMessage}
            </div>
          ) : null}

          <button
            type="button"
            onClick={() => void handleSave()}
            disabled={isSaving || isGeneratingAll || isEmbedding}
            className="rounded-xl border border-[var(--border)] bg-transparent px-5 py-2.5 text-sm font-semibold text-[var(--text-primary)] transition hover:bg-[var(--surface-2)] disabled:cursor-not-allowed disabled:opacity-70"
          >
            {isSaving ? "Saving..." : "Save & Close"}
          </button>

          <button
            type="button"
            onClick={() => void handleGenerateAll()}
            disabled={isGeneratingAll || isEmbedding || isPollingEmbedding}
            className="flex items-center justify-center rounded-xl bg-[var(--accent)] px-5 py-2.5 text-sm font-semibold text-[var(--background)] transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-70"
          >
            {isPollingEmbedding || isEmbedding ? (
              <span className="flex items-center gap-2">
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-[var(--background)]/30 border-t-[var(--background)]" />
                Generating...
              </span>
            ) : (
              "Generate All Embeddings"
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
