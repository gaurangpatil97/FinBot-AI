"use client";

import { useEffect, useRef, useState } from "react";

import CitationBadge from "./CitationBadge";
import ReactMarkdown from "react-markdown";
import { getCompanies } from "../../lib/api";
import type { ChatMessage } from "./finbot-types";

interface ChatWindowProps {
  messages: ChatMessage[];
  activeCompanyKey?: string;
  totalChunks?: number;
  totalDocs?: number;
  collectionCount?: number;
  onQuickQuery?: (query: string) => void;
}

function PipelineStatus() {
  const [step, setStep] = useState(0);

  useEffect(() => {
    const t1 = setTimeout(() => setStep(1), 600);
    const t2 = setTimeout(() => setStep(2), 2200);
    return () => { clearTimeout(t1); clearTimeout(t2); };
  }, []);

  const steps = [
    { label: "Routing query → Excel", active: step === 0, done: step > 0 },
    { label: "Retrieving relevant chunks", active: step === 1, done: step > 1 },
    { label: "Generating answer", active: step === 2, done: step > 2 }
  ];

  return (
    <div className="flex flex-col gap-2 py-1">
      {steps.map((s, i) => (
        <div key={i} className="flex items-center gap-2">
          {s.done ? (
            <span className="flex h-3.5 w-3.5 items-center justify-center rounded-full bg-green-500/20 text-[9px] text-[#22c55e]">✓</span>
          ) : s.active ? (
            <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-amber-500/20 border-t-amber-500" />
          ) : (
            <span className="h-3.5 w-3.5 rounded-full border border-zinc-600" />
          )}
          <span className={`text-xs ${s.active ? 'text-amber-500' : s.done ? 'text-[var(--text-secondary)]' : 'text-zinc-600'}`}>
            {s.label}
          </span>
        </div>
      ))}
    </div>
  );
}

type StoredCompany = {
  name?: string;
  slug?: string;
  companyName?: string;
  companySlug?: string;
};

type CompanySummary = {
  name?: string;
  slug?: string;
};

type WelcomeState = {
  activeCompanyName: string | null;
  otherCompanies: string[];
};

function slugifyCompanyName(companyName: string) {
  return companyName.trim().toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "");
}

function readStoredCompany(): StoredCompany {
  if (typeof window === "undefined") {
    return {};
  }

  const parse = (raw: string | null) => {
    if (!raw) {
      return {};
    }

    try {
      return JSON.parse(raw) as StoredCompany;
    } catch {
      return {};
    }
  };

  const activeCompany = parse(window.localStorage.getItem("activeCompany"));
  if (typeof activeCompany.name === "string" || typeof activeCompany.slug === "string") {
    return activeCompany;
  }

  const session = parse(window.localStorage.getItem("finbotai-session"));
  if (
    typeof session.name === "string" ||
    typeof session.slug === "string" ||
    typeof session.companyName === "string" ||
    typeof session.companySlug === "string"
  ) {
    return session;
  }

  return {};
}

function getCompanyLabel(company: CompanySummary) {
  if (typeof company.name === "string" && company.name.trim()) {
    return company.name.trim();
  }

  if (typeof company.slug === "string" && company.slug.trim()) {
    return company.slug.trim();
  }

  return "";
}

export default function ChatWindow({ messages, activeCompanyKey, totalChunks, totalDocs, collectionCount, onQuickQuery }: ChatWindowProps) {
  const viewportRef = useRef<HTMLDivElement>(null);
  const [welcome, setWelcome] = useState<WelcomeState | null>(null);

  useEffect(() => {
    const viewport = viewportRef.current;

    if (!viewport) {
      return;
    }

    viewport.scrollTo({ top: viewport.scrollHeight, behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    let cancelled = false;

    const loadWelcome = async () => {
      const storedCompany = readStoredCompany();
      const activeSlug =
        typeof storedCompany.slug === "string"
          ? storedCompany.slug.trim()
          : typeof storedCompany.companySlug === "string"
            ? storedCompany.companySlug.trim()
            : "";
      const activeName =
        typeof storedCompany.name === "string"
          ? storedCompany.name.trim()
          : typeof storedCompany.companyName === "string"
            ? storedCompany.companyName.trim()
            : "";

      try {
        const companies = (await getCompanies()) as CompanySummary[];
        const normalizedCompanies = Array.isArray(companies) ? companies : [];

        const matchedCompany = normalizedCompanies.find((company) => {
          const label = getCompanyLabel(company);
          const companySlug = typeof company.slug === "string" ? company.slug.trim() : "";

          return Boolean(
            (activeSlug && companySlug === activeSlug) ||
              (activeName && label.toLowerCase() === activeName.toLowerCase()) ||
              (activeName && companySlug === slugifyCompanyName(activeName)),
          );
        });

        const resolvedActiveName = matchedCompany ? getCompanyLabel(matchedCompany) : activeName || "";

        if (cancelled) {
          return;
        }

        if (!resolvedActiveName) {
          setWelcome({ activeCompanyName: null, otherCompanies: [] });
          return;
        }

        const otherCompanies = normalizedCompanies
          .map(getCompanyLabel)
          .filter((label) => label && label.toLowerCase() !== resolvedActiveName.toLowerCase());

        setWelcome({
          activeCompanyName: resolvedActiveName,
          otherCompanies,
        });
      } catch {
        if (!cancelled) {
          setWelcome(activeName ? { activeCompanyName: activeName, otherCompanies: [] } : { activeCompanyName: null, otherCompanies: [] });
        }
      }
    };

    void loadWelcome();

    return () => {
      cancelled = true;
    };
  }, [activeCompanyKey]);

  return (
    <section
      ref={viewportRef}
      className="flex flex-1 flex-col gap-4 overflow-y-auto min-h-0 p-4"
    >
      {messages.length === 0 ? (
        <div className="flex items-start gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[var(--surface-1)] text-sm font-semibold text-[var(--text-primary)] border border-[var(--border)]">
            AI
          </div>

          <div className="flex flex-col gap-3">
            <div className="max-w-[min(48rem,90%)] rounded-2xl border border-[var(--border)] bg-[var(--surface-1)] px-4 py-3 text-sm leading-6 text-[var(--text-primary)]">
              {welcome?.activeCompanyName ? (
                <>
                  <p className="font-medium text-[var(--text-primary)]">
                    {welcome.activeCompanyName} — corpus ready.
                  </p>
                  <p className="mt-2 text-[var(--text-secondary)]">
                    <span className="font-mono num">{totalDocs ?? 0}</span> documents · <span className="font-mono num">{totalChunks ?? 0}</span> chunks indexed across <span className="font-mono num">{collectionCount ?? 0}</span> collections (Excel, PDF, Images, Concall).
                  </p>
                  <p className="mt-2 text-[var(--text-primary)]">Ask about financials, earnings calls, or annual reports.</p>
                </>
              ) : (
                <p className="text-[var(--text-secondary)]">Click "+ Upload Dataset" to get started.</p>
              )}
            </div>

            {welcome?.activeCompanyName ? (
              <div className="flex flex-wrap gap-2 max-w-[min(48rem,90%)]">
                {[
                  "What was the EBITDA margin trend from FY23 to FY25?",
                  "What did management say about powertrain capex in the latest concall?",
                  "Calculate ROCE for FY24 and FY25",
                  "Summarize segment-wise revenue for FY24"
                ].map((q) => (
                  <button
                    key={q}
                    type="button"
                    onClick={() => onQuickQuery?.(q)}
                    className="rounded-full border border-[var(--border)] bg-[var(--surface-2)] px-3 py-1.5 text-xs font-medium text-[var(--text-secondary)] transition hover:border-[var(--accent)] hover:text-[var(--text-primary)]"
                  >
                    "{q}"
                  </button>
                ))}
              </div>
            ) : null}
          </div>
        </div>
      ) : null}

      {messages.map((message) => {
        const assistant = message.role === "assistant";

        return (
          <div
            key={message.id}
            className={`flex items-end gap-3 ${assistant ? "justify-start" : "justify-end"}`}
          >
            {assistant ? (
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[var(--surface-1)] text-sm font-semibold text-white border border-[var(--border)]">
                AI
              </div>
            ) : null}

            <div
              className={`max-w-[min(48rem,90%)] rounded-2xl border px-4 py-3 text-sm leading-6 ${
                assistant
                  ? "border-[var(--border)] bg-[var(--surface-1)] text-white"
                  : "border-[var(--border)] bg-[var(--surface-2)] text-white"
              }`}
            >
              {message.isLoading ? (
                <PipelineStatus />
              ) : assistant ? (
                <>
                  <div className="mb-2 text-[11px] text-[var(--text-secondary)]">Routed to Excel · 8 chunks · 1.4s</div>
                  <div className="prose prose-invert prose-sm max-w-none">
                    <ReactMarkdown>{message.content}</ReactMarkdown>
                  </div>
                </>
              ) : (
                <p className="whitespace-pre-line">{message.content}</p>
              )}
              {!message.isLoading && message.citations && message.citations.length > 0 ? (
                <div className="mt-3 flex flex-wrap gap-2">
                  {message.citations.slice(0, 3).map((citation, index) => (
                    <CitationBadge key={`${citation.label}-${index}`} label={citation.label} />
                  ))}
                  {message.citations.length > 3 && (
                    <CitationBadge label={`+${message.citations.length - 3} more`} />
                  )}
                </div>
              ) : null}
            </div>

            {!assistant ? (
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[var(--surface-1)] text-sm font-semibold text-white border border-[var(--border)]">
                U
              </div>
            ) : null}
          </div>
        );
      })}
    </section>
  );
}