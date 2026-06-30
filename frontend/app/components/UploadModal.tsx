"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import { createCompany, generateEmbeddings, getCompanyStatus, getExistingFiles, uploadFile } from "../../lib/api";

import type {
  CollectionKey,
  CollectionRecord,
  EmbeddingStatus,
  ExistingFilesResponse,
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
  return {
    companyName: "",
    ticker: "",
    files: defaultDraft(),
  };
}

type OverlapItem = {
  id: string;
  collection: CollectionKey;
  fileId: string;
  label: string;
};

type UploadStage = "uploading" | "processing" | "ready" | "failed";

type PendingCollectionItem = {
  key: CollectionKey;
  label: string;
};

type PendingEmbeddingState = {
  companyName: string;
  companySlug: string;
  ticker: string;
  collections: PendingCollectionItem[];
  startedAt: number;
};

const PENDING_EMBEDDING_STORAGE_KEY = "finbotai-pending-embedding";

function summarizeDraftFiles(files: DraftFileItem[]) {
  if (files.length === 0) {
    return "";
  }

  if (files.length === 1) {
    return files[0].name;
  }

  return `${files.length} files`;
}

function readPendingEmbeddingState(): PendingEmbeddingState | null {
  if (typeof window === "undefined") {
    return null;
  }

  try {
    const raw = window.localStorage.getItem(PENDING_EMBEDDING_STORAGE_KEY);
    if (!raw) {
      return null;
    }

    const parsed = JSON.parse(raw) as PendingEmbeddingState;
    if (
      typeof parsed.companyName !== "string" ||
      typeof parsed.companySlug !== "string" ||
      typeof parsed.ticker !== "string" ||
      !Array.isArray(parsed.collections) ||
      typeof parsed.startedAt !== "number"
    ) {
      return null;
    }

    return parsed;
  } catch {
    return null;
  }
}

function writePendingEmbeddingState(state: PendingEmbeddingState | null) {
  if (typeof window === "undefined") {
    return;
  }

  if (!state) {
    window.localStorage.removeItem(PENDING_EMBEDDING_STORAGE_KEY);
    return;
  }

  window.localStorage.setItem(PENDING_EMBEDDING_STORAGE_KEY, JSON.stringify(state));
}

function formatProgressStatus(status: UploadStage) {
  if (status === "uploading") {
    return "Uploading...";
  }

  if (status === "processing") {
    return "Processing...";
  }

  if (status === "ready") {
    return "Ready";
  }

  return "Failed";
}

function normalizeQuarterToken(quarter?: string | null, year?: string | null) {
  if (!quarter || !year) {
    return "";
  }

  return `${quarter.trim().toUpperCase()}_${year.trim().toUpperCase()}`;
}

function normalizeDisplayQuarter(quarter?: string | null, year?: string | null) {
  const cleanedQuarter = quarter?.trim().toUpperCase();
  const cleanedYear = year?.trim().toUpperCase();

  if (!cleanedQuarter) {
    return "";
  }

  return cleanedYear ? `${cleanedQuarter} ${cleanedYear}` : cleanedQuarter;
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
  const [isCheckingExistingFiles, setIsCheckingExistingFiles] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [existingFiles, setExistingFiles] = useState<ExistingFilesResponse | null>(null);
  const [overlapCheckError, setOverlapCheckError] = useState<string | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [progressState, setProgressState] = useState<PendingEmbeddingState | null>(null);
  const [collectionStages, setCollectionStages] = useState<Partial<Record<CollectionKey, UploadStage>>>({});
  const [backendStatus, setBackendStatus] = useState<BackendCompanyStatus | null>(null);
  const [completionMessage, setCompletionMessage] = useState<string | null>(null);
  const [longRunningWarning, setLongRunningWarning] = useState(false);
  const fileInputRefs = useRef<Record<CollectionKey, HTMLInputElement | null>>({
    excel: null,
    pdf: null,
    concall: null,
    images: null,
  });
  const collectionStagesRef = useRef<Partial<Record<CollectionKey, UploadStage>>>({});
  const timeouts = useRef<number[]>([]);
  const toastTimeout = useRef<number | null>(null);
  const totalFiles = useMemo(
    () => (Object.keys(draft.files) as CollectionKey[]).reduce((count, key) => count + draft.files[key].length, 0),
    [draft.files],
  );
  const companySlug = useMemo(() => {
    const companyNameValue = draft.companyName.trim();
    return companyNameValue ? slugifyCompanyName(companyNameValue) : "";
  }, [draft.companyName]);
  const progressCompanySlug = progressState?.companySlug ?? companySlug;
  const progressCompanyName = progressState?.companyName || draft.companyName.trim() || companyName;
  const progressRows = useMemo(() => {
    const sourceCollections = progressState?.collections ?? (Object.keys(draft.files) as CollectionKey[])
      .filter((key) => draft.files[key].length > 0)
      .map((key) => ({
        key,
        label: summarizeDraftFiles(draft.files[key]),
      }));

    return sourceCollections.map((item) => {
      const backendCollection = backendStatus?.collections?.[item.key];
      const backendStage = mapCollectionStatus(backendCollection?.status);
      const localStage = collectionStagesRef.current[item.key];
      const stage: UploadStage = backendStage === "ready" || backendStage === "processing" || backendStage === "failed"
        ? backendStage
        : localStage ?? "processing";

      return {
        key: item.key,
        label: item.label,
        fileLabel: item.key in draft.files ? summarizeDraftFiles(draft.files[item.key]) : item.label,
        stage,
        chunks: typeof backendCollection?.chunks === "number" ? backendCollection.chunks : 0,
      };
    });
  }, [backendStatus, draft.files, progressState]);
  const progressSummary = useMemo(() => {
    const completed = progressRows.filter((row) => row.stage === "ready").length;
    const failed = progressRows.filter((row) => row.stage === "failed").length;
    return { completed, failed, total: progressRows.length };
  }, [progressRows]);

  const overlapItems = useMemo<OverlapItem[]>(() => {
    if (!existingFiles) {
      return [];
    }

    const items: OverlapItem[] = [];

    if (draft.files.excel.length > 0 && existingFiles.excel.exists) {
      const existingFilename = existingFiles.excel.filename?.trim();
      items.push({
        id: `excel:${draft.files.excel[0].id}`,
        collection: "excel",
        fileId: draft.files.excel[0].id,
        label: "Excel already exists — remove from upload?",
      });
    }

    const existingPdfNames = new Set((existingFiles.pdf.files ?? []).map((name) => name.trim().toLowerCase()));
    for (const file of draft.files.pdf) {
      if (existingPdfNames.has(file.name.trim().toLowerCase())) {
        items.push({
          id: `pdf:${file.id}`,
          collection: "pdf",
          fileId: file.id,
          label: `PDF ${file.name} already exists — remove from upload?`,
        });
      }
    }

    const existingQuarterTokens = new Set((existingFiles.concall.quarters ?? []).map((quarter) => quarter.trim().toUpperCase()));
    for (const file of draft.files.concall) {
      const token = normalizeQuarterToken(file.quarter ?? null, file.year ?? null);
      if (token && existingQuarterTokens.has(token)) {
        items.push({
          id: `concall:${file.id}`,
          collection: "concall",
          fileId: file.id,
          label: `Concall ${normalizeDisplayQuarter(file.quarter ?? null, file.year ?? null)} already exists — remove from upload?`,
        });
      }
    }

    return items;
  }, [draft.files, existingFiles]);

  useEffect(() => {
    if (!open) {
      return;
    }

    const pendingEmbedding = readPendingEmbeddingState();

    if (pendingEmbedding) {
      const nextStages = pendingEmbedding.collections.reduce((accumulator, collection) => {
        accumulator[collection.key] = "processing";
        return accumulator;
      }, {} as Partial<Record<CollectionKey, UploadStage>>);

      setProgressState(pendingEmbedding);
      collectionStagesRef.current = nextStages;
      setCollectionStages(nextStages);
      setBackendStatus(null);
      setCompletionMessage(null);
      setLongRunningWarning(Date.now() - pendingEmbedding.startedAt >= 5 * 60 * 1000);
    } else {
      setProgressState(null);
      collectionStagesRef.current = {};
      setCollectionStages({});
      setBackendStatus(null);
      setCompletionMessage(null);
      setLongRunningWarning(false);
    }

    if (!companySlug || totalFiles === 0) {
      setExistingFiles(null);
      setOverlapCheckError(null);
      setIsCheckingExistingFiles(false);
      return;
    }

    let cancelled = false;

    setIsCheckingExistingFiles(true);
    setOverlapCheckError(null);

    void getExistingFiles(companySlug)
      .then((response) => {
        if (!cancelled) {
          setExistingFiles(response as ExistingFilesResponse);
        }
      })
      .catch((error) => {
        if (!cancelled) {
          setExistingFiles(null);
          setOverlapCheckError(error instanceof Error ? error.message : "Failed to check for overlapping files");
        }
      })
      .finally(() => {
        if (!cancelled) {
          setIsCheckingExistingFiles(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [open, companySlug, totalFiles]);

  useEffect(() => {
    if (!open || !progressState || !progressCompanySlug) {
      return;
    }

    let cancelled = false;
    let timeoutId: number | null = null;

    const pollStatus = async () => {
      try {
        const status = (await getCompanyStatus(progressCompanySlug)) as BackendCompanyStatus;

        if (cancelled) {
          return;
        }

        setBackendStatus(status);

        const collectionStatuses = status.collections ?? {};
        const nextStages: Partial<Record<CollectionKey, UploadStage>> = {};

        for (const item of progressState.collections) {
          const backendCollection = collectionStatuses[item.key];
          const backendStage = mapCollectionStatus(backendCollection?.status);

          if (backendStage === "ready" || backendStage === "processing" || backendStage === "failed") {
            nextStages[item.key] = backendStage;
            continue;
          }

          nextStages[item.key] = collectionStages[item.key] ?? "processing";
        }

        const mergedStages = {
          ...collectionStagesRef.current,
          ...nextStages,
        };

        collectionStagesRef.current = mergedStages;
        setCollectionStages(mergedStages);

        const finishedStages = progressState.collections.map((item) => mergedStages[item.key] ?? "processing");
        const allFinished = finishedStages.length > 0 && finishedStages.every((stage) => stage === "ready" || stage === "failed");

        if (allFinished) {
          const allReady = finishedStages.every((stage) => stage === "ready");
          const message = allReady ? "All embeddings generated successfully!" : "Some collections failed — check logs";

          setCompletionMessage(message);
          setIsPollingEmbedding(false);
          setIsEmbedding(false);
          setLongRunningWarning(false);
          writePendingEmbeddingState(null);
          collectionStagesRef.current = mergedStages;

          onSessionUpdate(buildSessionFromDraft(draft.files));

          try {
            await onEmbeddingComplete(progressCompanySlug);
          } catch {
            // Keep the progress screen visible even if the sidebar refresh fails.
          }

          return;
        }

        if (Date.now() - progressState.startedAt >= 5 * 60 * 1000) {
          setLongRunningWarning(true);
        }

        timeoutId = window.setTimeout(() => {
          void pollStatus();
        }, EMBEDDING_POLL_INTERVAL_MS);
      } catch {
        if (cancelled) {
          return;
        }

        if (Date.now() - progressState.startedAt >= 5 * 60 * 1000) {
          setLongRunningWarning(true);
        }

        timeoutId = window.setTimeout(() => {
          void pollStatus();
        }, EMBEDDING_POLL_INTERVAL_MS);
      }
    };

    void pollStatus();

    return () => {
      cancelled = true;
      if (timeoutId) {
        window.clearTimeout(timeoutId);
      }
    };
  }, [open, progressState, progressCompanySlug, onEmbeddingComplete]);

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
    setExistingFiles(null);
    setOverlapCheckError(null);
    setIsCheckingExistingFiles(false);
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

  const removeFile = (key: CollectionKey, fileId: string) => {
    updateFiles(key, (current) => current.filter((file) => file.id !== fileId));
  };

  const buildSessionFromDraft = (files: Record<CollectionKey, DraftFileItem[]>) => {
    const collections = collectionsFromDraft(files);

    return {
      companyName: draft.companyName,
      ticker: draft.ticker,
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

  const handleGenerateAll = async () => {
    if (isEmbedding) {
      showToast("Embedding in progress, please wait");
      return;
    }

    setErrorMessage(null);

    setIsGeneratingAll(true);
    setIsEmbedding(true);
    setIsPollingEmbedding(false);
    setCompletionMessage(null);
    setLongRunningWarning(false);

    try {
      const companyNameValue = draft.companyName;
      const tickerValue = draft.ticker;
      const companySlug = slugifyCompanyName(companyNameValue);
      await createCompany(companyNameValue, companySlug, tickerValue);

      const trackedCollections = (Object.keys(draft.files) as CollectionKey[]).filter((key) => draft.files[key].length > 0);
      const pendingState: PendingEmbeddingState = {
        companyName: companyNameValue,
        companySlug,
        ticker: tickerValue,
        collections: trackedCollections.map((key) => ({
          key,
          label: summarizeDraftFiles(draft.files[key]),
        })),
        startedAt: Date.now(),
      };

      setProgressState(pendingState);
      writePendingEmbeddingState(pendingState);

      const initialStages = pendingState.collections.reduce((accumulator, item) => {
        accumulator[item.key] = "uploading";
        return accumulator;
      }, {} as Partial<Record<CollectionKey, UploadStage>>);

      collectionStagesRef.current = initialStages;
      setCollectionStages(initialStages);

      const existingFilenames = getSessionFilenames(session);
      const uploadTasks: Promise<{ collection: CollectionKey; ok: boolean }>[] = [];

      for (const key of trackedCollections) {
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
              .then(() => ({ collection: key, ok: true }))
              .catch(() => ({ collection: key, ok: false })),
          );
        }
      }

      const uploadResults = await Promise.all(uploadTasks);
      const failedCollections = new Set(
        uploadResults.filter((result) => !result.ok).map((result) => result.collection),
      );

      if (failedCollections.size > 0) {
        const nextStages = {
          ...collectionStagesRef.current,
        };

        for (const collection of failedCollections) {
          nextStages[collection] = "failed";
        }

        collectionStagesRef.current = nextStages;
        setCollectionStages(nextStages);
      }

      await generateEmbeddings(companySlug).catch((error) => {
        throw error instanceof Error ? error : new Error("Failed to start embedding");
      });

      setIsPollingEmbedding(true);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to generate embeddings";
      setErrorMessage(message);
    } finally {
      setIsGeneratingAll(false);
      setIsEmbedding(false);
    }
  };

  const handleSave = async () => {
    setErrorMessage(null);
    setIsSaving(true);

    try {
      const companyNameValue = draft.companyName;
      const tickerValue = draft.ticker;
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
            <p className="truncate text-sm font-medium text-[var(--text-primary)]">{file.name}</p>
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
          isActive ? "border-[#e8ddc7] bg-[#e8ddc7]/10 scale-[1.01]" : "border-[var(--border)] bg-[var(--surface-2)]"
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
            <h3 className="text-base font-semibold text-[var(--text-primary)]">{zoneTitles[key]}</h3>
            <p className="mt-1 text-sm text-[#888888]">{zoneRules[key]}</p>
            {key === "pdf" ? <p className="mt-2 text-xs text-[#888888]">Text and image pages will be processed separately.</p> : null}
          </div>
        </div>

        <label className="mt-4 flex cursor-pointer flex-col rounded-2xl border border-dashed border-[var(--border)] bg-[var(--surface-1)] px-4 py-4 text-center transition hover:border-[#e8ddc7] hover:bg-[#e8ddc7]/10">
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
          <span className="text-sm font-medium text-[#e8ddc7]">
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
            <div className="mb-4 rounded-2xl border border-[var(--border)] bg-[var(--surface-2)] px-4 py-3 text-sm text-[var(--text-primary)]">
              {errorMessage}
            </div>
          ) : null}

          <div className="grid gap-4 md:grid-cols-2">
            <label className="space-y-2 rounded-3xl border border-[var(--border)] bg-[var(--surface-2)] p-4">
              <span className="text-sm font-medium text-[var(--text-secondary)]">Company Name</span>
              <input
                value={draft.companyName}
                onChange={(event) => setDraft((current) => ({ ...current, companyName: event.target.value }))}
                placeholder="e.g. Acme Industries Ltd"
                className="w-full rounded-2xl border border-[var(--border)] bg-[var(--surface-1)] px-4 py-3 text-sm text-[var(--text-primary)] outline-none placeholder:text-[var(--text-secondary)]"
              />
            </label>

            <label className="space-y-2 rounded-3xl border border-[var(--border)] bg-[var(--surface-2)] p-4">
              <span className="text-sm font-medium text-[var(--text-secondary)]">NSE/BSE Ticker</span>
              <input
                value={draft.ticker}
                onChange={(event) => setDraft((current) => ({ ...current, ticker: event.target.value }))}
                placeholder="e.g. ACME.NS"
                className="w-full rounded-2xl border border-[var(--border)] bg-[var(--surface-1)] px-4 py-3 text-sm text-[var(--text-primary)] outline-none placeholder:text-[var(--text-secondary)]"
              />
            </label>
          </div>

          {isCheckingExistingFiles ? (
            <div className="mt-6 rounded-3xl border border-[var(--border)] bg-[var(--surface-2)] p-4 text-sm text-[var(--text-secondary)]">
              Checking for existing uploads...
            </div>
          ) : null}

          {overlapCheckError ? (
            <div className="mt-6 rounded-3xl border border-[var(--border)] bg-[var(--surface-2)] p-4 text-sm text-[var(--text-secondary)]">
              {overlapCheckError}
            </div>
          ) : null}

          {overlapItems.length > 0 ? (
            <div className="mt-6 rounded-3xl border border-[#e8ddc7] bg-[#e8ddc7]/10 p-4">
              <p className="text-sm font-semibold text-[var(--text-primary)]">Existing uploads detected</p>
              <div className="mt-3 space-y-2">
                {overlapItems.map((item) => (
                  <div key={item.id} className="flex items-center justify-between gap-3 rounded-2xl border border-[var(--border)] bg-[var(--surface-1)] px-4 py-3 text-sm text-[var(--text-primary)]">
                    <span className="min-w-0 flex-1">{item.label}</span>
                    <button
                      type="button"
                      onClick={() => removeFile(item.collection, item.fileId)}
                      className="grid h-8 w-8 shrink-0 place-items-center rounded-full border border-[var(--border)] bg-[var(--surface-2)] text-base font-semibold text-[var(--text-primary)] transition hover:bg-[var(--border)]"
                      aria-label={`Remove ${item.label}`}
                    >
                      -
                    </button>
                  </div>
                ))}
              </div>
            </div>
          ) : null}

          {progressState ? (
            <div className="mt-6 rounded-3xl border border-[var(--border)] bg-[var(--surface-2)] p-4">
              <div className="flex flex-col gap-4 border-b border-[var(--border)] pb-4 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <p className="text-xl font-semibold text-[var(--text-primary)]">{progressCompanyName}</p>
                  <p className="mt-1 text-sm text-[var(--text-secondary)]">Embedding collections in the background</p>
                </div>
                <div className="rounded-full border border-[var(--border)] bg-[var(--surface-1)] px-3 py-1.5 text-sm font-medium text-[var(--text-secondary)]">
                  {progressSummary.completed} of {progressSummary.total} collections ready
                </div>
              </div>

              {completionMessage ? (
                <div className={`mt-4 rounded-2xl border px-4 py-3 text-sm ${
                  progressSummary.failed > 0
                    ? "border-[#ef4444]/40 bg-[#ef4444]/10 text-[#fecaca]"
                    : "border-[#22c55e]/30 bg-[#22c55e]/10 text-[#bbf7d0]"
                }`}>
                  {completionMessage}
                </div>
              ) : null}

              {longRunningWarning ? (
                <div className="mt-4 rounded-2xl border border-[#f59e0b]/40 bg-[#f59e0b]/10 px-4 py-3 text-sm text-[#fde68a]">
                  Taking longer than expected — processing continues in background.
                </div>
              ) : null}

              <div className="mt-4 space-y-3">
                {progressRows.map((row) => {
                  const isProcessing = row.stage === "processing" || row.stage === "uploading";
                  return (
                    <div key={row.key} className="flex items-center justify-between gap-4 rounded-2xl border border-[var(--border)] bg-[var(--surface-1)] px-4 py-3">
                      <div className="min-w-0 flex items-center gap-3">
                        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-[var(--border)] bg-[var(--surface-2)] text-xs font-semibold text-[var(--text-primary)]">
                          {row.key === "excel" ? "XLSX" : row.key === "pdf" ? "PDF" : "CAL"}
                        </div>
                        <div className="min-w-0">
                          <p className="truncate text-sm font-medium text-[var(--text-primary)]">{zoneTitles[row.key]}</p>
                          <p className="truncate text-xs text-[var(--text-secondary)]">{row.fileLabel || "No filename available"}</p>
                        </div>
                      </div>

                      <div className="flex shrink-0 items-center gap-2 text-sm font-medium text-[var(--text-primary)]">
                        {row.stage === "ready" ? (
                          <span className="flex h-5 w-5 items-center justify-center rounded-full bg-[#22c55e]/15 text-xs font-bold text-[#22c55e]">✓</span>
                        ) : row.stage === "failed" ? (
                          <span className="flex h-5 w-5 items-center justify-center rounded-full bg-[#ef4444]/15 text-xs font-bold text-[#ef4444]">✕</span>
                        ) : (
                          <span className="h-5 w-5 animate-spin rounded-full border-2 border-[var(--border)] border-t-[#e8ddc7]" />
                        )}
                        <span className={isProcessing ? "text-[var(--text-secondary)]" : "text-[var(--text-primary)]"}>
                          {formatProgressStatus(row.stage)}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>

              <div className="mt-5 flex flex-wrap items-center justify-between gap-3 border-t border-[var(--border)] pt-4">
                <p className="text-sm text-[var(--text-secondary)]">
                  {progressSummary.completed} of {progressSummary.total} collections ready
                </p>
              </div>
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 mt-6">
              {renderZone("excel")}
              {renderZone("pdf")}
              <div className="md:col-span-2">
                {renderZone("concall")}
              </div>
            </div>
          )}
        </div>

        {progressState ? (
          <div className="border-t border-[var(--border)] px-6 py-5 flex items-center justify-end gap-3">
            {toastMessage ? (
              <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-2)] px-4 py-2.5 text-sm text-[var(--text-primary)]">
                {toastMessage}
              </div>
            ) : null}

            {completionMessage ? (
              <button
                type="button"
                onClick={() => {
                  writePendingEmbeddingState(null);
                  onClose();
                }}
                className="rounded-xl bg-[#e8ddc7] px-5 py-2.5 text-sm font-semibold text-[#0a0a0c] transition hover:opacity-90"
              >
                Continue to Chat
              </button>
            ) : (
              <p className="mr-auto text-xs text-[var(--text-secondary)]">Processing continues in the background. You can close this modal anytime.</p>
            )}
          </div>
        ) : (
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
              className="flex items-center justify-center rounded-xl bg-[#e8ddc7] px-5 py-2.5 text-sm font-semibold text-[#0a0a0c] transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-70"
            >
              {isPollingEmbedding || isEmbedding ? (
                <span className="flex items-center gap-2">
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-[var(--bg)]/30 border-t-[var(--bg)]" />
                  Generating...
                </span>
              ) : (
                "Generate All Embeddings"
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
