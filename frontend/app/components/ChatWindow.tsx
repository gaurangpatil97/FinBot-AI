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
import {
  ResponsiveContainer,
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend
} from "recharts";

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

interface InlineChartProps {
  chartData: {
    chart_type: "bar" | "line" | "combo";
    title: string;
    x_axis: string[];
    series: Array<{ name: string; data: number[] }>;
    y_axis_label?: string;
  };
}

function CustomTooltip({ active, payload, label }: any) {
  if (active && payload && payload.length) {
    return (
      <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-2)] px-3 py-2 text-xs text-[var(--text-primary)] shadow-[0_12px_30px_rgba(0,0,0,0.35)] font-sans">
        <div className="font-semibold text-[var(--text-secondary)] uppercase tracking-wider mb-1">{label}</div>
        {payload.map((p: any, idx: number) => (
          <div key={idx} className="flex justify-between gap-4 py-0.5">
            <span className="text-[var(--text-secondary)]">{p.name}:</span>
            <span className="font-mono font-medium text-[var(--text-primary)] tabular-nums">
              ₹{new Intl.NumberFormat("en-IN", { maximumFractionDigits: 2 }).format(p.value)} Cr
            </span>
          </div>
        ))}
      </div>
    );
  }
  return null;
}

function InlineChart({ chartData }: InlineChartProps) {
  const [hasMounted, setHasMounted] = useState(false);
  useEffect(() => {
    setHasMounted(true);
  }, []);

  if (!hasMounted) {
    return <div className="h-56 flex items-center justify-center text-xs text-[var(--text-muted)]">Loading chart...</div>;
  }

  const formattedData = chartData.x_axis.map((label, index) => {
    const item: any = { name: label };
    chartData.series.forEach((s) => {
      item[s.name] = s.data[index];
    });
    return item;
  });

  return (
    <div className="h-56 w-full mt-2">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={formattedData} margin={{ top: 10, right: 10, left: -20, bottom: 5 }}>
          <CartesianGrid stroke="rgba(255,255,255,0.04)" vertical={false} />
          <XAxis 
            dataKey="name" 
            axisLine={false} 
            tickLine={false} 
            tick={{ fill: 'var(--text-secondary)', fontSize: 10 }} 
          />
          <YAxis 
            axisLine={false} 
            tickLine={false} 
            tick={{ fill: 'var(--text-secondary)', fontSize: 10 }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend 
            verticalAlign="top" 
            height={28} 
            iconType="circle" 
            wrapperStyle={{ fontSize: 11 }}
            formatter={(value) => <span style={{ color: '#e8ddc7', fontWeight: 500 }}>{value}</span>}
          />
          {chartData.chart_type === "line" && chartData.series.map((s) => (
            <Line
              key={s.name}
              type="monotone"
              dataKey={s.name}
              stroke="#e8ddc7"
              strokeWidth={2}
              dot={{ r: 3, fill: '#111111', stroke: '#e8ddc7', strokeWidth: 1.5 }}
              activeDot={{ r: 5 }}
            />
          ))}
          {chartData.chart_type === "bar" && chartData.series.map((s) => (
            <Bar
              key={s.name}
              dataKey={s.name}
              fill="#857c6b"
              radius={[4, 4, 0, 0]}
              maxBarSize={30}
            />
          ))}
          {chartData.chart_type === "combo" && chartData.series.map((s, idx) => {
            if (idx === 0) {
              return (
                <Bar
                  key={s.name}
                  dataKey={s.name}
                  fill="#857c6b"
                  radius={[4, 4, 0, 0]}
                  maxBarSize={30}
                />
              );
            } else {
              return (
                <Line
                  key={s.name}
                  type="monotone"
                  dataKey={s.name}
                  stroke="#e8ddc7"
                  strokeWidth={2}
                  dot={{ r: 3, fill: '#111111', stroke: '#e8ddc7', strokeWidth: 1.5 }}
                  activeDot={{ r: 5 }}
                />
              );
            }
          })}
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

function getCompanySlug(activeCompanyKey?: string): string {
  if (activeCompanyKey) {
    return slugifyCompanyName(activeCompanyKey);
  }
  const storedCompany = readStoredCompany();
  const activeSlug =
    typeof storedCompany.slug === "string"
      ? storedCompany.slug.trim()
      : typeof storedCompany.companySlug === "string"
        ? storedCompany.companySlug.trim()
        : "";
  if (activeSlug) return activeSlug;
  const activeName =
    typeof storedCompany.name === "string"
      ? storedCompany.name.trim()
      : typeof storedCompany.companyName === "string"
        ? storedCompany.companyName.trim()
        : "";
  return slugifyCompanyName(activeName || "craftsman_automation_ltd");
}

export function extractYears(text: string): string[] {
  const yearsMatch = [...text.matchAll(/\b(FY\d{2}|FY\s*\d{2}|20\d{2})\b/gi)];
  let years = Array.from(new Set(yearsMatch.map(m => {
    const yr = m[1].replace(/FY\s*/i, "").trim();
    if (yr.length === 2) return `20${yr}`;
    return yr;
  }))).sort();
  
  if (years.length === 2) {
    const start = parseInt(years[0]);
    const end = parseInt(years[1]);
    if (!isNaN(start) && !isNaN(end) && start < end && (end - start <= 10)) {
      const expanded: string[] = [];
      for (let y = start; y <= end; y++) {
        expanded.push(y.toString());
      }
      years = expanded;
    }
  }
  return years;
}

export function extractMetrics(text: string): string[] {
  const lower = text.toLowerCase();
  const metrics: string[] = [];
  
  if (lower.includes("ebitda margin")) {
    metrics.push("EBITDA", "Sales");
  } else if (lower.includes("ebitda")) {
    metrics.push("EBITDA");
  }
  
  if (lower.includes("debt to equity") || lower.includes("debt-to-equity") || lower.includes("d/e ratio") || lower.includes("d/e")) {
    metrics.push("Borrowings", "Networth");
  }
  
  if (lower.includes("sales") || lower.includes("revenue")) {
    if (!metrics.includes("Sales")) metrics.push("Sales");
  }
  
  if (lower.includes("net profit") || lower.includes("profit after tax") || lower.includes("pat") || lower.includes("net income")) {
    if (!metrics.includes("Net profit")) metrics.push("Net profit");
  }
  
  if (lower.includes("borrowings") || lower.includes("debt")) {
    if (!metrics.includes("Borrowings")) metrics.push("Borrowings");
  }
  
  if (lower.includes("networth") || lower.includes("equity") || lower.includes("net worth")) {
    if (!metrics.includes("Networth")) metrics.push("Networth");
  }
  
  if (lower.includes("cash conversion") || lower.includes("ccr")) {
    metrics.push("Cash from Operating Activity", "Net profit");
  }
  
  if (lower.includes("interest coverage") || lower.includes("icr")) {
    metrics.push("EBITDA", "Interest");
  }
  
  if (lower.includes("roe") || lower.includes("return on equity")) {
    metrics.push("Net profit", "Networth");
  }
  
  if (metrics.length === 0) {
    metrics.push("Sales");
  }
  
  return metrics;
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

                  {message.chart_data && (
                    <div className="mt-3 border-t border-[var(--border)] pt-3">
                      <div className="mt-2 rounded-xl border border-[var(--border)] bg-[var(--surface-2)] p-4 shadow-sm">
                        <h4 className="text-xs font-semibold uppercase tracking-wider text-[var(--text-secondary)] mb-3">
                          {message.chart_data.title}
                        </h4>
                        <InlineChart chartData={message.chart_data} />
                      </div>
                    </div>
                  )}
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