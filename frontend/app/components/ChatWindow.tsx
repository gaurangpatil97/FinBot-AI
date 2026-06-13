"use client";

import { useEffect, useRef, useState } from "react";

import CitationBadge from "./CitationBadge";
import ReactMarkdown from "react-markdown";
import remarkMath from "remark-math";
import remarkGfm from "remark-gfm";
import rehypeKatex from "rehype-katex";
import "katex/dist/katex.min.css";
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
            <span className="flex h-3.5 w-3.5 items-center justify-center rounded-full bg-[#22c55e]/20 text-[9px] text-[#22c55e]">✓</span>
          ) : s.active ? (
            <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-[var(--border)] border-t-[#22c55e]" />
          ) : (
            <span className="h-3.5 w-3.5 rounded-full border border-[var(--border)]" />
          )}
          <span className={`text-xs ${s.active ? 'text-[var(--text-primary)]' : s.done ? 'text-[var(--text-secondary)]' : 'text-[var(--text-muted)]'}`}>
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

const cleanContent = (content: string): string => {
  if (!content) return "";
  return content
    .split("\n")
    .filter((line) => {
      const trimmed = line.trim();
      const isAsterisksOnly = trimmed.length > 0 && /^\*+$/.test(trimmed) && !trimmed.includes("|") && !trimmed.includes("-");
      return !isAsterisksOnly;
    })
    .join("\n");
};

const renderMessageContent = (content: string) => {
  const cleaned = cleanContent(content);
  console.log("RAW_CONTENT:", JSON.stringify(cleaned));
  return (
    <div className="prose prose-invert prose-base max-w-none prose-p:leading-relaxed prose-pre:bg-zinc-900">
      <ReactMarkdown remarkPlugins={[remarkMath, remarkGfm]} rehypePlugins={[rehypeKatex]}>
        {cleaned}
      </ReactMarkdown>
    </div>
  );
};

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
                    className="rounded-full border border-[var(--border)] bg-[var(--surface-2)] px-3 py-1.5 text-xs font-medium text-[var(--text-secondary)] transition hover:border-[#e8ddc7] hover:text-[var(--text-primary)]"
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
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[var(--surface-1)] text-sm font-semibold text-[var(--text-primary)] border border-[var(--border)]">
                AI
              </div>
            ) : null}

            <div
                className={`max-w-[min(48rem,90%)] rounded-2xl border px-4 py-3 text-base leading-6 ${
                  assistant
                  ? "border-[var(--border)] bg-[var(--surface-1)] text-[var(--text-primary)]"
                  : "border-[var(--border)] bg-[var(--surface-2)] text-[var(--text-primary)]"
                }`}
            >
              {message.isLoading ? (
                <PipelineStatus />
              ) : assistant ? (
                <>
                  {message.routingSource && (
                    <div className="inline-block mb-2 rounded-full bg-[var(--surface-2)] border border-[var(--border)] px-2.5 py-0.5 text-xs text-[var(--text-secondary)]">
                      {message.routingSource === "Calculation" ? (
                        <>Calculated · {message.latency ? parseFloat(message.latency).toFixed(1) : "0.0"}s</>
                      ) : (
                        <>
                          Routed to {message.routingSource} · {message.chunkCount || 0} chunk{(message.chunkCount || 0) === 1 ? "" : "s"} · {message.latency ? parseFloat(message.latency).toFixed(1) : "0.0"}s
                        </>
                      )}
                    </div>
                  )}
                  {renderMessageContent(message.content)}
                </>
              ) : (
                <p className="whitespace-pre-line">{cleanContent(message.content)}</p>
              )}
            </div>

            {!assistant ? (
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[var(--surface-1)] text-sm font-semibold text-[var(--text-primary)] border border-[var(--border)]">
                U
              </div>
            ) : null}
          </div>
        );
      })}
    </section>
  );
}