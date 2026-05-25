"use client";

import { useEffect, useState } from "react";

import { queryRAG } from "../../lib/api";

import ChatWindow from "./ChatWindow";
import InputBar from "./InputBar";
import KPICards from "./KPICards";
import Sidebar from "./Sidebar";
import UploadModal from "./UploadModal";
import type {
  ChatMessage,
  CollectionRecord,
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

function createInitialCollections(companyName: string): CollectionRecord[] {
  const slug = companyName.replace(/\s+/g, "_");

  return [
    {
      key: "excel",
      label: "Excel Financial Data",
      fileName: `${slug}_FY24.xlsx`,
      status: "ready",
      description: "Structured financial statements and working capital schedules.",
    },
    {
      key: "pdf",
      label: "PDF Annual Reports",
      fileName: "Annual_Report_FY24.pdf",
      status: "ready",
      description: "Text and scanned pages processed independently.",
    },
    {
      key: "concall",
      label: "Concall Transcripts",
      fileName: "Q3_FY24_Concall.pdf",
      status: "no-embeddings",
      description: "Quarterly call transcripts and management commentary.",
    },
    {
      key: "images",
      label: "Image Dataset",
      fileName: "",
      status: "processing",
      description: "Charts, screenshots, and scanned board notes.",
    },
  ];
}

function createBaseMessages(companyName: string): ChatMessage[] {
  return [
    {
      id: "msg-1",
      role: "assistant",
      content: `Corpus loaded for ${companyName} — documents ready for queries.`,
    },
  ];
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

export default function FinbotDashboard({ stock }: FinbotDashboardProps) {
  const defaultCompanyName = stock.companyName;
  const defaultTicker = stock.ticker;

  const [companies, setCompanies] = useState<string[]>([defaultCompanyName]);
  const [activeCompany, setActiveCompany] = useState(defaultCompanyName);
  const [activeTicker, setActiveTicker] = useState(defaultTicker);
  const [collections, setCollections] = useState<CollectionRecord[]>(() => createInitialCollections(defaultCompanyName));
  const [documents, setDocuments] = useState<DocumentRecord[]>(() => syncDocuments(createInitialCollections(defaultCompanyName)));
  const [messages, setMessages] = useState<ChatMessage[]>(() => createBaseMessages(defaultCompanyName));
  const [inputValue, setInputValue] = useState("");
  const [uploadOpen, setUploadOpen] = useState(false);
  const [resumeBannerVisible, setResumeBannerVisible] = useState(false);
  const [hasSession, setHasSession] = useState(false);
  const [savedSession, setSavedSession] = useState<SavedDatasetSession | null>(null);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    const stored = window.localStorage.getItem(sessionStorageKey);
    if (!stored) {
      return;
    }

    const parsed = parseSessionPayload(stored);
    if (!parsed) {
      return;
    }

    const nextCollections = collectionsFromSession(parsed, parsed.companyName);

    setSavedSession(parsed);
    setCompanies((current) => (current.includes(parsed.companyName) ? current : [...current, parsed.companyName]));
    setActiveCompany(parsed.companyName);
    setActiveTicker(parsed.ticker);
    setCollections(nextCollections);
    setDocuments(syncDocuments(nextCollections));
    setMessages(createBaseMessages(parsed.companyName));
    setHasSession(true);
    setResumeBannerVisible(true);
  }, []);

  const handleSend = async () => {
    const trimmed = inputValue.trim();

    if (!trimmed) {
      return;
    }

    const userMessageId = createMessageId();
    const loadingMessageId = createMessageId();

    setInputValue("");

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
      const companySlug = getCompanySlugFromLocalStorage(activeCompany);
      const year = extractYearFromQuestion(trimmed);
      const result = await queryRAG(trimmed, companySlug, year);

      const answer =
        result && typeof result.answer === "string" && result.answer.trim()
          ? result.answer
          : "Failed to get response";

      const citations = Array.isArray(result?.citations)
        ? result.citations.map((citation: unknown) => ({ label: toCitationLabel(citation) }))
        : [];

      setMessages((current) =>
        current.map((message) =>
          message.id === loadingMessageId
            ? {
                ...message,
                content: answer,
                citations,
                isLoading: false,
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
    setMessages(createBaseMessages(session.companyName));
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
    }

    setSavedSession(null);
    setActiveCompany(defaultCompanyName);
    setActiveTicker(defaultTicker);
    setCompanies([defaultCompanyName]);
    const nextCollections = createInitialCollections(defaultCompanyName);
    setCollections(nextCollections);
    setDocuments(syncDocuments(nextCollections));
    setMessages(createBaseMessages(defaultCompanyName));
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
    setResumeBannerVisible(false);
  };

  const corpusCount = documents.length;
  const chunkCount = 12340;

  return (
    <div className="flex min-h-screen bg-[#0f1117] text-white">
      <Sidebar
        activeCompany={activeCompany}
        companies={companies}
        onSelectCompany={handleSelectCompany}
        stock={stock}
        collections={collections}
        onOpenUpload={() => setUploadOpen(true)}
      />

      <main className="flex min-w-0 flex-1 flex-col px-4 py-4 lg:px-5">
        <header className="flex items-center justify-between rounded-2xl border border-white/8 bg-[#161b22] px-5 py-4">
          <div className="flex items-center gap-3 text-sm font-medium text-zinc-100">
            <span className="relative flex h-3 w-3">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-blue-400 opacity-60" />
              <span className="relative inline-flex h-3 w-3 rounded-full bg-blue-400" />
            </span>
            <span>FinbotAI beta</span>
          </div>
          <div className="text-sm text-[#8b949e]">
            Corpus: {corpusCount} docs · {chunkCount.toLocaleString()} chunks · {activeTicker}
          </div>
        </header>

        {resumeBannerVisible ? (
          <div className="mt-3 rounded-2xl border border-blue-400/15 bg-[#11161d] px-4 py-3 text-sm text-zinc-200">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <p>
                Welcome back — {activeCompany} loaded. {savedSession?.collections.length ?? collections.length} collections ready.
              </p>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={handleContinue}
                  className="rounded-xl bg-blue-500 px-4 py-2 text-sm font-semibold text-white"
                >
                  Continue
                </button>
                <button
                  type="button"
                  onClick={handleNewDataset}
                  className="rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm font-semibold text-zinc-100"
                >
                  Load New Dataset
                </button>
              </div>
            </div>
          </div>
        ) : null}

        <div className="mt-4">
          <KPICards revenue="₹153,670 Cr" margin="17.1%" chunksIndexed="3,500" docsUploaded="47" />
        </div>

        <div className="mt-4 flex min-h-0 flex-1 flex-col overflow-hidden rounded-3xl border border-white/8 bg-[#1c2128]">
          <ChatWindow messages={messages} />
          <div className="border-t border-white/8 p-3">
            <InputBar
              value={inputValue}
              onChange={setInputValue}
              onSend={handleSend}
              onAttach={() => setUploadOpen(true)}
            />
          </div>
        </div>
      </main>

      <UploadModal
        open={uploadOpen}
        session={savedSession}
        companyName={activeCompany}
        ticker={activeTicker}
        onClose={() => setUploadOpen(false)}
        onSave={handleSaveSession}
        onSessionUpdate={handleSessionUpdate}
      />
    </div>
  );
}