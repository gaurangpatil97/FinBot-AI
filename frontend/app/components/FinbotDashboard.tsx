"use client";

import { useEffect, useState } from "react";

import { getCompanies, getCompanyStatus, queryRAG } from "../../lib/api";

import ChatWindow from "./ChatWindow";
import InputBar from "./InputBar";
import KPICards from "./KPICards";
import Sidebar from "./Sidebar";
import UploadModal from "./UploadModal";
import SessionsRail from "./SessionsRail";
import { SessionProvider, useSessions } from "../context/SessionContext";
import { createSession } from "../../lib/api";
import type {
  ChatMessage,
  CollectionRecord,
  CollectionKey,
  CorpusFileRecord,
  DocumentRecord,
  SavedDatasetSession,
  StockSummary,
} from "./finbot-types";

interface FinbotDashboardProps {
  stock: StockSummary;
}

const sessionStorageKey = "finbotai-session";

function createMessageId() {
  return typeof crypto !== "undefined" && "randomUUID" in crypto ? crypto.randomUUID() : `msg-${Date.now()}-${Math.random()}`;
}

function slugifyCompanyName(companyName: string) {
  return companyName.trim().toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "");
}

function extractYearFromQuestion(question: string): string | undefined {
  const match = question.match(/\b(FY20\d{2}|FY\d{2}|20\d{2})\b/i);

  if (!match) {
    return undefined;
  }

  return match[1].toUpperCase();
}

function getCompanySlugFromLocalStorage(activeCompanyName: string): string {
  if (typeof window === "undefined") {
    return slugifyCompanyName(activeCompanyName);
  }

  try {
    const raw = window.localStorage.getItem(sessionStorageKey);

    if (!raw) {
      return slugifyCompanyName(activeCompanyName);
    }

    const parsed = JSON.parse(raw) as { companySlug?: string; companyName?: string };
    if (typeof parsed.companySlug === "string" && parsed.companySlug.trim()) {
      return parsed.companySlug.trim();
    }

    if (typeof parsed.companyName === "string" && parsed.companyName.trim()) {
      return slugifyCompanyName(parsed.companyName);
    }
  } catch {
    // Fallback to active company slug.
  }

  return slugifyCompanyName(activeCompanyName);
}

function getActiveCompanyFromLocalStorage(fallbackName: string) {
  if (typeof window === "undefined") {
    return { name: fallbackName, slug: slugifyCompanyName(fallbackName) };
  }

  try {
    const raw = window.localStorage.getItem("activeCompany");

    if (raw) {
      const parsed = JSON.parse(raw) as { name?: string; slug?: string; companyName?: string; companySlug?: string };
      const name =
        typeof parsed.name === "string" && parsed.name.trim()
          ? parsed.name.trim()
          : typeof parsed.companyName === "string" && parsed.companyName.trim()
            ? parsed.companyName.trim()
            : "";
      const slug =
        typeof parsed.slug === "string" && parsed.slug.trim()
          ? parsed.slug.trim()
          : typeof parsed.companySlug === "string" && parsed.companySlug.trim()
            ? parsed.companySlug.trim()
            : name
              ? slugifyCompanyName(name)
              : "";

      if (name || slug) {
        return { name: name || fallbackName, slug: slug || slugifyCompanyName(name || fallbackName) };
      }
    }

    const sessionRaw = window.localStorage.getItem("finbotai-session");
    if (sessionRaw) {
      const parsed = JSON.parse(sessionRaw) as { companyName?: string; companySlug?: string };
      const name = typeof parsed.companyName === "string" && parsed.companyName.trim() ? parsed.companyName.trim() : "";
      const slug = typeof parsed.companySlug === "string" && parsed.companySlug.trim() ? parsed.companySlug.trim() : "";

      if (name || slug) {
        return { name: name || fallbackName, slug: slug || slugifyCompanyName(name || fallbackName) };
      }
    }
  } catch {
    // Fallback below.
  }

  return { name: fallbackName, slug: slugifyCompanyName(fallbackName) };
}

function toCitationLabel(citation: unknown): string {
  if (!citation || typeof citation !== "object") {
    return "unknown | unknown";
  }

  const record = citation as { filename?: unknown; page?: unknown };
  const filename = typeof record.filename === "string" && record.filename.trim() ? record.filename : "unknown";

  const page =
    typeof record.page === "string" || typeof record.page === "number"
      ? String(record.page)
      : "unknown";

  return `${filename} | ${page}`;
}

function isGreetingMessage(message: string) {
  const normalized = message
    .toLowerCase()
    .trim()
    .replace(/[.!?,]+$/g, "")
    .replace(/\s+/g, " ");

  const greetings = ["hi", "hello", "hey", "thanks", "thank you", "bye", "good morning", "good evening"];

  return greetings.some((greeting) => normalized === greeting);
}

function createInitialCollections(companyName: string): CollectionRecord[] {
  const slug = companyName.replace(/\s+/g, "_");

  return [
    {
      key: "excel",
      label: "Excel Financial Data",
      fileName: `${slug}_FY24.xlsx`,
      status: "ready",
      description: "Structured financial statements and working capital schedules.",
      chunks: 0,
    },
    {
      key: "pdf",
      label: "PDF Annual Reports",
      fileName: "Annual_Report_FY24.pdf",
      status: "ready",
      description: "Text and scanned pages processed independently.",
      chunks: 0,
    },
    {
      key: "concall",
      label: "Concall Transcripts",
      fileName: "Q3_FY24_Concall.pdf",
      status: "no-embeddings",
      description: "Quarterly call transcripts and management commentary.",
      chunks: 0,
    },
    {
      key: "images",
      label: "Image Dataset",
      fileName: "",
      status: "processing",
      description: "Charts, screenshots, and scanned board notes.",
      chunks: 0,
    },
  ];
}

function mapBackendCollectionStatus(status: string | undefined) {
  if (status === "ready" || status === "processing" || status === "uploaded" || status === "failed") {
    return status;
  }

  if (status === "error") {
    return "failed";
  }

  return "no-embeddings";
}

type BackendCollectionStatus = {
  status?: string;
  chunks?: number;
};

type BackendCompanyStatus = {
  name?: unknown;
  slug?: unknown;
  ticker?: unknown;
  collections?: Partial<Record<CollectionKey, BackendCollectionStatus>>;
  files?: unknown;
};

function collectionsFromBackendStatus(
  companyName: string,
  backendStatus: BackendCompanyStatus,
): CollectionRecord[] {
  const fallback = createInitialCollections(companyName);
  const fallbackByKey = new Map(fallback.map((collection) => [collection.key, collection]));

  const orderedCollections: Array<{ key: CollectionKey; label: string }> = [
    { key: "excel", label: "Excel" },
    { key: "pdf", label: "PDF Text" },
    { key: "images", label: "Images" },
    { key: "concall", label: "Concall" },
  ];

  return orderedCollections.map(({ key, label }) => {
    const collection = fallbackByKey.get(key) ?? createInitialCollections(companyName).find((item) => item.key === key);
    const server = backendStatus.collections?.[key];

    if (!collection) {
      return {
        key,
        label,
        fileName: "",
        status: mapBackendCollectionStatus(server?.status),
        description: "",
        chunks: typeof server?.chunks === "number" ? server.chunks : 0,
      };
    }

    return {
      ...collection,
      label,
      status: mapBackendCollectionStatus(server?.status),
      chunks: typeof server?.chunks === "number" ? server.chunks : collection.chunks,
    };
  });
}

function mapFileCollection(value: unknown): CollectionKey | null {
  if (value === "excel" || value === "pdf" || value === "concall" || value === "images") {
    return value;
  }

  return null;
}

function filesFromBackendStatus(backendStatus: { files?: unknown }): Record<CollectionKey, CorpusFileRecord[]> {
  const mapped: Record<CollectionKey, CorpusFileRecord[]> = {
    excel: [],
    pdf: [],
    concall: [],
    images: [],
  };

  if (!Array.isArray(backendStatus.files)) {
    return mapped;
  }

  for (const entry of backendStatus.files) {
    if (!entry || typeof entry !== "object") {
      continue;
    }

    const record = entry as {
      file_id?: unknown;
      filename?: unknown;
      file_type?: unknown;
      chunks?: unknown;
    };
    const collection = mapFileCollection(record.file_type);

    if (!collection) {
      continue;
    }

    const id = typeof record.file_id === "string" && record.file_id.trim() ? record.file_id : `${collection}-${Date.now()}-${Math.random()}`;
    const name = typeof record.filename === "string" && record.filename.trim() ? record.filename : "Unknown file";
    const chunks = typeof record.chunks === "number" ? record.chunks : 0;

    mapped[collection].push({
      id,
      name,
      collection,
      chunks,
    });
  }

  return mapped;
}

function getStatusCompanyLabel(status: { name?: unknown; slug?: unknown } | null, fallback: string) {
  if (!status) {
    return fallback;
  }

  if (typeof status.name === "string" && status.name.trim()) {
    return status.name.trim();
  }

  if (typeof status.slug === "string" && status.slug.trim()) {
    return status.slug.trim();
  }

  return fallback;
}

const initialDocuments: DocumentRecord[] = [
  { id: "doc-1", group: "excel", name: "Balance Sheet FY24", status: "ready" },
  { id: "doc-2", group: "excel", name: "P&L Statement FY24", status: "ready" },
  { id: "doc-3", group: "pdf", name: "Annual Report FY24", status: "ready" },
  { id: "doc-4", group: "pdf", name: "Annual Report FY23", status: "ready" },
  { id: "doc-5", group: "concall", name: "Q3 FY24 Results", status: "none" },
  { id: "doc-6", group: "concall", name: "Q2 FY24 Results", status: "none" },
  { id: "doc-7", group: "images", name: "Investor Presentation", status: "processing" },
  { id: "doc-8", group: "images", name: "Board Resolution Scan", status: "processing" },
];

function syncDocuments(collections: CollectionRecord[]): DocumentRecord[] {
  return initialDocuments.map((document) => {
    const collection = collections.find((entry) => entry.key === document.group);

    if (!collection) {
      return document;
    }

    const status: DocumentRecord["status"] =
      collection.status === "ready"
        ? "ready"
        : collection.status === "processing"
          ? "processing"
          : "none";

    return {
      ...document,
      status,
    };
  });
}

function collectionsFromSession(session: SavedDatasetSession, companyName: string): CollectionRecord[] {
  const fallbackCollections = createInitialCollections(companyName);

  return fallbackCollections.map((fallback) => {
    const saved = session.collections.find((collection) => collection.key === fallback.key);

    if (!saved) {
      return fallback;
    }

    return {
      key: saved.key,
      label: saved.label,
      description: saved.description,
      fileName: saved.fileName,
      status: saved.status,
    };
  });
}

function parseSessionPayload(value: string): SavedDatasetSession | null {
  try {
    const parsed = JSON.parse(value) as Partial<SavedDatasetSession>;

    if (
      typeof parsed.companyName !== "string" ||
      typeof parsed.ticker !== "string" ||
      !Array.isArray(parsed.collections) ||
      typeof parsed.readyCollections !== "number" ||
      typeof parsed.chunks !== "number" ||
      typeof parsed.savedAt !== "string"
    ) {
      return null;
    }

    return parsed as SavedDatasetSession;
  } catch {
    return null;
  }
}

function FinbotDashboardInner({ stock }: FinbotDashboardProps) {
  const defaultCompanyName = stock.companyName;
  const defaultTicker = stock.ticker;

  const [companies, setCompanies] = useState<string[]>([defaultCompanyName]);
  const [activeCompany, setActiveCompany] = useState(defaultCompanyName);
  const [activeTicker, setActiveTicker] = useState(defaultTicker);
  const [collections, setCollections] = useState<CollectionRecord[]>(() => createInitialCollections(defaultCompanyName));
  const [, setDocuments] = useState<DocumentRecord[]>(() => syncDocuments(createInitialCollections(defaultCompanyName)));
  
  const { messages, setMessages, activeSessionId, setActiveSessionId, loadSessions, setIsRailOpen, isRailOpen, switchSession, clearState } = useSessions();
  
  const [inputValue, setInputValue] = useState("");
  const [uploadOpen, setUploadOpen] = useState(false);
  const [resumeBannerVisible, setResumeBannerVisible] = useState(false);
  const [, setHasSession] = useState(false);
  const [savedSession, setSavedSession] = useState<SavedDatasetSession | null>(null);
  const [corpusFiles, setCorpusFiles] = useState<Record<CollectionKey, CorpusFileRecord[]>>({
    excel: [],
    pdf: [],
    concall: [],
    images: [],
  });

  const refreshCompanyStatus = async (companyLabel: string) => {
    const companySlug = getCompanySlugFromLocalStorage(companyLabel);

    try {
      const status = await getCompanyStatus(companySlug);
      const resolvedCompanyName = getStatusCompanyLabel(status, companyLabel);
      const nextCollections = collectionsFromBackendStatus(resolvedCompanyName, status);
      const nextFiles = filesFromBackendStatus(status);

      setCollections(nextCollections);
      setCorpusFiles(nextFiles);
      setDocuments(syncDocuments(nextCollections));
      setActiveCompany(resolvedCompanyName);
      setCompanies((current) => (current.includes(resolvedCompanyName) ? current : [...current, resolvedCompanyName]));
    } catch {
      const fallbackCollections = collectionsFromBackendStatus(companyLabel, { collections: {} });
      setCollections(fallbackCollections);
      setCorpusFiles({ excel: [], pdf: [], concall: [], images: [] });
      setDocuments(syncDocuments(fallbackCollections));
    }
  };

  useEffect(() => {
    let cancelled = false;
    let timeoutId: number | null = null;

    const run = async () => {
      const companySlug = getCompanySlugFromLocalStorage(activeCompany);

      try {
        const status = (await getCompanyStatus(companySlug)) as BackendCompanyStatus;

        if (cancelled) {
          return;
        }

        const resolvedCompanyName = getStatusCompanyLabel(status, activeCompany);
        const nextCollections = collectionsFromBackendStatus(resolvedCompanyName, status);
        const nextFiles = filesFromBackendStatus(status);

        setCollections(nextCollections);
        setCorpusFiles(nextFiles);
        setDocuments(syncDocuments(nextCollections));

        if (resolvedCompanyName !== activeCompany) {
          setActiveCompany(resolvedCompanyName);
          setCompanies((current) => (current.includes(resolvedCompanyName) ? current : [...current, resolvedCompanyName]));
        }

        const isProcessing = Object.values(status.collections ?? {}).some((collection) => collection?.status === "processing");

        if (isProcessing) {
          timeoutId = window.setTimeout(() => {
            void run();
          }, 5000);
        }
      } catch {
        if (cancelled) {
          return;
        }

        const fallbackCollections = collectionsFromBackendStatus(activeCompany, { collections: {} });
        setCollections(fallbackCollections);
        setCorpusFiles({ excel: [], pdf: [], concall: [], images: [] });
        setDocuments(syncDocuments(fallbackCollections));
      }
    };

    void run();

    return () => {
      cancelled = true;

      if (timeoutId) {
        window.clearTimeout(timeoutId);
      }
    };
  }, [activeCompany]);

  useEffect(() => {
    const slug = getCompanySlugFromLocalStorage(activeCompany);
    loadSessions(slug);
  }, [activeCompany, loadSessions]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const storedSessionId = window.localStorage.getItem("activeSessionId");
    if (storedSessionId && storedSessionId !== activeSessionId) {
      switchSession(storedSessionId);
    }
  }, [switchSession, activeSessionId]);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    let refreshTimeoutId: number | null = null;

    const stored = window.localStorage.getItem(sessionStorageKey);
    if (!stored) {
      return;
    }

    const parsed = parseSessionPayload(stored);
    if (!parsed) {
      refreshTimeoutId = window.setTimeout(() => {
        void refreshCompanyStatus(defaultCompanyName);
      }, 0);
    } else {
      refreshTimeoutId = window.setTimeout(() => {
        setSavedSession(parsed);
        setCompanies((current) => (current.includes(parsed.companyName) ? current : [...current, parsed.companyName]));
        setActiveCompany(parsed.companyName);
        setActiveTicker(parsed.ticker);
        setMessages([]);
        setHasSession(true);
        setResumeBannerVisible(true);
      }, 0);
    }

    return () => {
      if (refreshTimeoutId) {
        window.clearTimeout(refreshTimeoutId);
      }
    };
  }, [defaultCompanyName]);

  const handleSend = async (queryOverride?: string | React.MouseEvent | React.KeyboardEvent) => {
    const overrideString = typeof queryOverride === "string" ? queryOverride : undefined;
    const trimmed = (overrideString ?? inputValue).trim();

    if (!trimmed) {
      return;
    }

    const userMessageId = createMessageId();
    const loadingMessageId = createMessageId();

    setInputValue("");

    if (isGreetingMessage(trimmed)) {
      const activeCompanyInfo = getActiveCompanyFromLocalStorage(activeCompany);

      try {
        const companies = (await getCompanies()) as Array<{ name?: string; slug?: string }>;
        const normalizedCompanies = Array.isArray(companies) ? companies : [];
        const otherCompanies = normalizedCompanies.filter((company) => company.slug !== activeCompanyInfo.slug);

        let response = `Hey there! 👋 Ask me anything about **${activeCompanyInfo.name}**'s financials, earnings calls, or annual reports.\n\n`;

        if (otherCompanies.length > 0) {
          response += `You also have these datasets available:\n`;
          otherCompanies.forEach((company) => {
            if (typeof company.name === "string" && company.name.trim()) {
              response += `• ${company.name.trim()}\n`;
            }
          });
          response += `\nSwitch companies using the selector in the sidebar, or upload a new dataset using the "+ Upload Dataset" button.`;
        } else {
          response += `You can also upload a new dataset anytime using the "+ Upload Dataset" button.`;
        }

        setMessages((current) => [
          ...current,
          { id: userMessageId, role: "user", content: trimmed },
          {
            id: loadingMessageId,
            role: "assistant",
            content: response,
          },
        ]);
      } catch {
        setMessages((current) => [
          ...current,
          { id: userMessageId, role: "user", content: trimmed },
          {
            id: loadingMessageId,
            role: "assistant",
            content: `Hey there! 👋 Ask me anything about **${activeCompanyInfo.name}**'s financials, earnings calls, or annual reports.\n\nYou can also upload a new dataset anytime using the "+ Upload Dataset" button.`,
          },
        ]);
      }

      return;
    }

    setMessages((current) => [
      ...current,
      { id: userMessageId, role: "user", content: trimmed },
      {
        id: loadingMessageId,
        role: "assistant",
        content: "",
        isLoading: true,
      },
    ]);

    try {
      const startTime = Date.now();
      const companySlug = getCompanySlugFromLocalStorage(activeCompany);
      const year = extractYearFromQuestion(trimmed);
      
      let currentSessionId = activeSessionId;
      
      if (!currentSessionId) {
         const title = trimmed.length > 50 ? trimmed.substring(0, 50) + "..." : trimmed;
         const sess = await createSession(companySlug, title);
         currentSessionId = sess.id;
         setActiveSessionId(currentSessionId);
         if (typeof window !== "undefined") {
            window.localStorage.setItem("activeSessionId", currentSessionId!);
         }
         await loadSessions(companySlug); // refresh rail
      }

      const result = await queryRAG(trimmed, companySlug, year, currentSessionId || undefined);
      const latencySeconds = ((Date.now() - startTime) / 1000).toFixed(1);

      const answer =
        result && typeof result.answer === "string" && result.answer.trim()
          ? result.answer
          : "Failed to get response";

      const citations = Array.isArray(result?.citations)
        ? result.citations.map((citation: unknown) => ({ label: toCitationLabel(citation) }))
        : [];

      let routingSource = "Unknown";
      if (result?.routing_debug?.source_types && Array.isArray(result.routing_debug.source_types) && result.routing_debug.source_types.length > 0) {
        routingSource = result.routing_debug.source_types.map((s: string) => s.charAt(0).toUpperCase() + s.slice(1)).join(", ");
      } else if (Array.isArray(result?.collections_searched) && result.collections_searched.length > 0) {
        routingSource = result.collections_searched.map((c: string) => (c.split("_").pop() || c)).join(", ");
      }

      const chunkCount = Array.isArray(result?.chunks) ? result.chunks.length : 0;

      setMessages((current) =>
        current.map((message) =>
          message.id === loadingMessageId
            ? {
                ...message,
                content: answer,
                citations,
                isLoading: false,
                routingSource,
                chunkCount,
                latency: latencySeconds,
              }
            : message,
        ),
      );
    } catch {
      setMessages((current) =>
        current.map((message) =>
          message.id === loadingMessageId
            ? {
                ...message,
                content: "Failed to get response",
                citations: [],
                isLoading: false,
              }
            : message,
        ),
      );
    }
  };

  const handleContinue = () => setResumeBannerVisible(false);

  const handleEmbeddingComplete = async (companySlug: string) => {
    try {
      const status = await getCompanyStatus(companySlug);
      const resolvedCompanyName = getStatusCompanyLabel(status, activeCompany);
      const nextCollections = collectionsFromBackendStatus(resolvedCompanyName, status);
      const nextFiles = filesFromBackendStatus(status);
      setCollections(nextCollections);
      setCorpusFiles(nextFiles);
      setDocuments(syncDocuments(nextCollections));
      setActiveCompany(resolvedCompanyName);
    } catch {
      // Keep existing sidebar state if status refresh fails.
    }
  };

  const syncSessionState = (session: SavedDatasetSession) => {
    const nextCollections = collectionsFromSession(session, session.companyName);

    if (typeof window !== "undefined") {
      window.localStorage.setItem(sessionStorageKey, JSON.stringify(session));
    }

    setSavedSession(session);
    setCompanies((current) => (current.includes(session.companyName) ? current : [...current, session.companyName]));
    setActiveCompany(session.companyName);
    setActiveTicker(session.ticker);
    setCollections(nextCollections);
    setDocuments(syncDocuments(nextCollections));
    clearState();
    setHasSession(true);
    setResumeBannerVisible(true);
  };

  const handleSaveSession = (session: SavedDatasetSession) => {
    syncSessionState(session);
    setUploadOpen(false);
  };

  const handleSessionUpdate = (session: SavedDatasetSession) => {
    syncSessionState(session);
  };

  const handleNewDataset = () => {
    if (typeof window !== "undefined") {
      window.localStorage.removeItem(sessionStorageKey);
      window.localStorage.removeItem("activeSessionId");
    }

    setSavedSession(null);
    setActiveCompany(defaultCompanyName);
    setActiveTicker(defaultTicker);
    setCompanies([defaultCompanyName]);
    const nextCollections = createInitialCollections(defaultCompanyName);
    setCollections(nextCollections);
    setCorpusFiles({ excel: [], pdf: [], concall: [], images: [] });
    setDocuments(syncDocuments(nextCollections));
    clearState(); // Clears messages and activeSessionId from context
    setInputValue("");
    setUploadOpen(false);
    setResumeBannerVisible(false);
    setHasSession(false);
  };

  const handleSelectCompany = (value: string) => {
    if (value === "New Dataset") {
      handleNewDataset();
      return;
    }

    setActiveCompany(value);
    clearState(); // Clear chat when switching companies
    setResumeBannerVisible(false);
  };

  const activeCompanySlug = getCompanySlugFromLocalStorage(activeCompany);
  const totalChunks = collections.reduce((sum, col) => sum + (col.chunks ?? 0), 0);
  const totalDocs = Object.values(corpusFiles).flat().length;
  const activeCollectionsCount = collections.filter(c => (c.chunks ?? 0) > 0).length || collections.length;

  return (
    <div className="flex h-screen overflow-hidden bg-[var(--bg)] text-[var(--text-primary)]">
      <div className="sticky top-0 h-screen overflow-auto w-72 flex-shrink-0 overflow-x-hidden border-r border-[var(--border)]">
        <Sidebar
          activeCompany={activeCompany}
          activeCompanySlug={getCompanySlugFromLocalStorage(activeCompany)}
          companies={companies}
          onSelectCompany={handleSelectCompany}
          stock={stock}
          collections={collections}
          filesByCollection={corpusFiles}
          onOpenUpload={() => setUploadOpen(true)}
        />
      </div>

      <main className="flex min-w-0 flex-1 flex-col overflow-hidden h-full px-4 py-4 lg:px-5">

        {resumeBannerVisible ? (
          <div className="mb-4 rounded-2xl border border-[var(--border)] bg-[var(--surface-1)] px-4 py-3 text-sm text-[var(--text-secondary)]">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <p>
                Welcome back — {activeCompany} loaded. {savedSession?.collections.length ?? collections.length} collections ready.
              </p>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={handleContinue}
                  className="rounded-xl bg-[var(--accent)] px-4 py-2 text-sm font-semibold text-[var(--accent-fill-text)] hover:opacity-90 transition-opacity"
                >
                  Continue
                </button>
                <button
                  type="button"
                  onClick={handleNewDataset}
                  className="rounded-xl border border-[var(--border-strong)] bg-transparent px-4 py-2 text-sm font-semibold text-[var(--text-primary)] hover:bg-[var(--surface-3)] transition-colors"
                >
                  Load New Dataset
                </button>
              </div>
            </div>
          </div>
        ) : null}

        <div>
          <KPICards companySlug={activeCompanySlug} totalChunks={totalChunks} totalDocs={totalDocs} isCorpusLoading={false} />
        </div>

        <div className="mt-4 flex min-h-0 flex-1 flex-col overflow-hidden rounded-3xl border border-[var(--border)] bg-[var(--surface-1)]">
          <ChatWindow messages={messages} activeCompanyKey={activeCompany} totalChunks={totalChunks} totalDocs={totalDocs} collectionCount={activeCollectionsCount} onQuickQuery={handleSend} />
          <div className="border-t border-[var(--border)] p-3">
            <InputBar
              value={inputValue}
              onChange={setInputValue}
              onSend={handleSend}
              onAttach={() => setUploadOpen(true)}
            />
          </div>
        </div>
      </main>

      <SessionsRail activeCompanySlug={activeCompanySlug} />

      <UploadModal
        open={uploadOpen}
        session={savedSession}
        companyName={activeCompany}
        ticker={activeTicker}
        onClose={() => setUploadOpen(false)}
        onSave={handleSaveSession}
        onSessionUpdate={handleSessionUpdate}
        onEmbeddingComplete={handleEmbeddingComplete}
      />
    </div>
  );
}

export default function FinbotDashboard(props: FinbotDashboardProps) {
  return (
    <SessionProvider>
      <FinbotDashboardInner {...props} />
    </SessionProvider>
  );
}