"use client";

import { useEffect, useRef, useState } from "react";

import CitationBadge from "./CitationBadge";
import ReactMarkdown from "react-markdown";
import { getCompanies } from "../../lib/api";
import type { ChatMessage } from "./finbot-types";

interface ChatWindowProps {
  messages: ChatMessage[];
  activeCompanyKey?: string;
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

export default function ChatWindow({ messages, activeCompanyKey }: ChatWindowProps) {
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
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[#111111] text-sm font-semibold text-white border border-[#222222]">
            AI
          </div>

          <div className="max-w-[min(48rem,90%)] rounded-2xl border border-[#333333] bg-[#0a0a0a] px-4 py-3 text-sm leading-6 text-white">
            <p className="text-base font-semibold text-white">Hey! I&apos;m FinbotAI 👋</p>
            {welcome?.activeCompanyName ? (
              <>
                <p className="mt-2">
                  I&apos;m your AI-powered financial research assistant. You&apos;ve loaded <strong>{welcome.activeCompanyName}</strong> as your active corpus — ask me anything about their financials, earnings calls, or annual reports.
                </p>
                {welcome.otherCompanies.length > 0 ? (
                  <p className="mt-2 text-zinc-400">Other available datasets: {welcome.otherCompanies.join(", ")}</p>
                ) : null}
                <p className="mt-2">You can also upload a new dataset anytime using the "+ Upload Dataset" button.</p>
                <p className="mt-2">What would you like to know?</p>
              </>
            ) : (
              <p className="mt-2 text-zinc-300">Click "+ Upload Dataset" to get started.</p>
            )}
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
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[#111111] text-sm font-semibold text-white border border-[#222222]">
                AI
              </div>
            ) : null}

            <div
              className={`max-w-[min(48rem,90%)] rounded-2xl border px-4 py-3 text-sm leading-6 ${
                assistant
                  ? "border-[#333333] bg-[#0a0a0a] text-white"
                  : "border-[#222222] bg-[#1a1a1a] text-white"
              }`}
            >
              {message.isLoading ? (
                <div className="flex items-center gap-2 text-zinc-300">
                  <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-blue-300" />
                  <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-blue-300 [animation-delay:120ms]" />
                  <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-blue-300 [animation-delay:240ms]" />
                </div>
              ) : assistant ? (
                <div className="prose prose-invert prose-sm max-w-none">
                  <ReactMarkdown>{message.content}</ReactMarkdown>
                </div>
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
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[#111111] text-sm font-semibold text-white border border-[#222222]">
                U
              </div>
            ) : null}
          </div>
        );
      })}
    </section>
  );
}