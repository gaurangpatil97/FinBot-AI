"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import {
  Bar,
  Area,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
} from "recharts";

import { getCompanyKpi, getCompanyRisks } from "../../lib/api";

type FinancialMetric = "Sales" | "Net profit" | "EBITDA" | "Borrowings";
type FiscalYear = "FY22" | "FY23" | "FY24" | "FY25";

interface KPICardsProps {
  companySlug: string;
  totalChunks: number;
  totalDocs: number;
  isCorpusLoading?: boolean;
}

type KpiResponse = {
  metric?: string;
  value?: number;
  year?: string;
  unit?: string;
};

const FINANCIAL_METRICS: Array<{ label: string; value: FinancialMetric }> = [
  { label: "Revenue", value: "Sales" },
  { label: "Net Profit", value: "Net profit" },
  { label: "EBITDA", value: "EBITDA" },
  { label: "Borrowings", value: "Borrowings" },
];

const YEAR_OPTIONS: Array<{ label: FiscalYear; value: FiscalYear }> = [
  { label: "FY22", value: "FY22" },
  { label: "FY23", value: "FY23" },
  { label: "FY24", value: "FY24" },
  { label: "FY25", value: "FY25" },
];

const TREND_YEARS: FiscalYear[] = ["FY22", "FY23", "FY24", "FY25"];

const CARD_BACKGROUND = "#111111";
const CARD_BORDER = "#222222";
const BAR_COLOR = "#555555";
const LINE_COLOR = "#cccccc";

function toApiYear(year: string) {
  const normalized = year.replace(/^FY/i, "");
  if (normalized.length === 2 && /^\d{2}$/.test(normalized)) {
    return `20${normalized}`;
  }
  return normalized;
}

function previousFiscalYear(year: FiscalYear) {
  const numeric = Number.parseInt(year.slice(2), 10);
  if (Number.isNaN(numeric) || numeric <= 0) {
    return null;
  }

  return `FY${String(numeric - 1).padStart(2, "0")}`;
}

function formatCrValue(value: number | null | undefined) {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "Unavailable";
  }

  return `₹${new Intl.NumberFormat("en-IN", {
    maximumFractionDigits: 2,
  }).format(value)} Cr`;
}

function formatYoY(currentValue: number | null | undefined, previousValue: number | null | undefined) {
  if (typeof currentValue !== "number" || typeof previousValue !== "number") {
    return "YoY unavailable";
  }

  const delta = currentValue - previousValue;
  const sign = delta > 0 ? "+" : delta < 0 ? "-" : "";
  const pct = previousValue !== 0 ? ((Math.abs(delta) / Math.abs(previousValue)) * 100).toFixed(1) : "0.0";

  return `${sign}₹${new Intl.NumberFormat("en-IN", { maximumFractionDigits: 2 }).format(Math.abs(delta))} Cr (${sign}${pct}%)`;
}

function metricLabel(metric: FinancialMetric) {
  return FINANCIAL_METRICS.find((option) => option.value === metric)?.label ?? metric;
}

function formatCompactNumber(value: number) {
  const absolute = Math.abs(value);

  if (absolute >= 1000) {
    const compact = absolute / 1000;
    const formatted = Number.isInteger(compact) ? compact.toFixed(0) : compact.toFixed(1);
    return `${value < 0 ? "-" : ""}${formatted}k`;
  }

  return `${value}`;
}

function KpiCard({
  title,
  value,
  subtext,
  emphasis = "neutral",
  subtextClass = "text-sm",
}: {
  title: string;
  value: string;
  subtext: string;
  emphasis?: "neutral" | "positive" | "warning";
  subtextClass?: string;
}) {
  const accentClass =
    subtext.startsWith("+")
      ? "text-[var(--gain)]"
      : subtext.startsWith("-")
        ? "text-[var(--loss)]"
        : "text-[var(--text-secondary)]";

  return (
    <article className="rounded-2xl border border-[var(--border)] bg-[var(--surface-1)] p-4 h-full shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]">
      <p className="text-xs font-semibold uppercase tracking-wider text-[var(--text-secondary)]">{title}</p>
      <p className="mt-2 text-2xl font-semibold tracking-tight text-[var(--text-primary)] font-mono tabular-nums num">{value}</p>
      <p className={`mt-3 ${subtextClass} ${accentClass}`}>{subtext}</p>
    </article>
  );
}

function PencilIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 20 20" fill="none" className="h-3.5 w-3.5">
      <path
        d="M13.5 3.5a1.4 1.4 0 0 1 2 0l1 1a1.4 1.4 0 0 1 0 2l-8.7 8.7-3.8 1 1-3.8 8.7-8.9Z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
      <path d="M12.6 4.4 15.6 7.4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

function usePopoverDismiss(onDismiss: () => void, active: boolean, containerRef: React.RefObject<HTMLDivElement | null>) {
  useEffect(() => {
    if (!active) {
      return;
    }

    const handlePointerDown = (event: MouseEvent | TouchEvent) => {
      const target = event.target;

      if (containerRef.current && target instanceof Node && !containerRef.current.contains(target)) {
        onDismiss();
      }
    };

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onDismiss();
      }
    };

    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("touchstart", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("touchstart", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [active, containerRef, onDismiss]);
}

function FadeValue({ value }: { value: string }) {
  const [displayValue, setDisplayValue] = useState(value);
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    if (value === displayValue) {
      return;
    }

    const fadeOutId = window.setTimeout(() => {
      setVisible(false);
    }, 0);

    const swapId = window.setTimeout(() => {
      setDisplayValue(value);
      window.requestAnimationFrame(() => {
        setVisible(true);
      });
    }, 100);

    return () => {
      window.clearTimeout(fadeOutId);
      window.clearTimeout(swapId);
    };
  }, [displayValue, value]);

  return (
    <span className={`inline-block transition-opacity duration-200 ${visible ? "opacity-100" : "opacity-0"}`}>
      {displayValue}
    </span>
  );
}

function useFinancialKpi(companySlug: string, metric: FinancialMetric, initialYear: FiscalYear) {
  const [year, setYear] = useState<FiscalYear>(initialYear);
  const [currentValue, setCurrentValue] = useState<number | null>(null);
  const [previousValue, setPreviousValue] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      setIsLoading(true);

      try {
        const current = (await getCompanyKpi(companySlug, metric, toApiYear(year))) as KpiResponse;
        const previousYear = previousFiscalYear(year);
        let previous: KpiResponse | null = null;

        if (previousYear) {
          try {
            previous = (await getCompanyKpi(companySlug, metric, toApiYear(previousYear))) as KpiResponse;
          } catch {
            previous = null;
          }
        }

        if (cancelled) {
          return;
        }

        setCurrentValue(typeof current.value === "number" ? current.value : null);
        setPreviousValue(typeof previous?.value === "number" ? previous.value : null);
      } catch {
        if (cancelled) {
          return;
        }

        setCurrentValue(null);
        setPreviousValue(null);
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    };

    if (companySlug) {
      void load();
    } else {
      setCurrentValue(null);
      setPreviousValue(null);
      setIsLoading(false);
    }

    return () => {
      cancelled = true;
    };
  }, [companySlug, metric, year]);

  return {
    year,
    setYear,
    currentValue,
    previousValue,
    isLoading,
  };
}

function choicePillClass(active: boolean) {
  return active
    ? "border-[#e8ddc7] bg-[#e8ddc7] text-[#0a0a0c]"
    : "border-[var(--border)] bg-[var(--surface-1)] text-[var(--text-secondary)] hover:border-[var(--text-primary)] hover:text-[var(--text-primary)]";
}

function FinancialKpiCard({
  companySlug,
  metric,
  onMetricChange,
  initialYear,
}: {
  companySlug: string;
  metric: FinancialMetric;
  onMetricChange: (metric: FinancialMetric) => void;
  initialYear: FiscalYear;
}) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [isPopoverOpen, setIsPopoverOpen] = useState(false);
  const { year, setYear, currentValue, previousValue, isLoading } = useFinancialKpi(companySlug, metric, initialYear);
  usePopoverDismiss(() => setIsPopoverOpen(false), isPopoverOpen, containerRef);

  const currentLabel = metricLabel(metric);
  const title = `${currentLabel} ${year}`;
  const value = isLoading ? "Loading..." : formatCrValue(currentValue);
  const subtext = isLoading ? "Fetching values..." : formatYoY(currentValue, previousValue);
  const emphasis = subtext.startsWith("+") ? "positive" : subtext.startsWith("-") ? "negative" : "neutral";

  const popover = isPopoverOpen ? (
    <div className="absolute left-0 top-[calc(100%+0.5rem)] z-20 w-[min(20rem,calc(100vw-2rem))] rounded-2xl border border-[var(--border)] bg-[var(--surface-2)] p-3 shadow-[0_20px_50px_rgba(0,0,0,0.45)] backdrop-blur-sm">
      <div className="grid gap-3">
        <div>
          <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-zinc-500">Metric</p>
          <div className="flex flex-wrap gap-2">
            {FINANCIAL_METRICS.map((option) => (
              <button
                key={option.value}
                type="button"
                onClick={() => onMetricChange(option.value)}
                className={`rounded-full border px-3 py-1.5 text-xs font-medium transition ${choicePillClass(metric === option.value)}`}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>

        <div>
          <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-zinc-500">Year</p>
          <div className="flex flex-wrap gap-2">
            {YEAR_OPTIONS.map((option) => (
              <button
                key={option.value}
                type="button"
                onClick={() => setYear(option.value)}
                className={`rounded-full border px-3 py-1.5 text-xs font-medium transition ${choicePillClass(year === option.value)}`}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  ) : null;

  return (
    <article ref={containerRef} className="relative rounded-2xl border border-[var(--border)] bg-[var(--surface-1)] p-4 h-full shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]">
      <button
        type="button"
        onClick={() => setIsPopoverOpen((current) => !current)}
        className="group flex items-center gap-2 text-left outline-none rounded-md focus-visible:ring-2 focus-visible:ring-[#e8ddc7]"
      >
        <p className="text-xs font-semibold uppercase tracking-wider text-[var(--text-secondary)] transition-colors group-hover:text-[var(--text-primary)]">{title}</p>
        <span className="opacity-0 transition-opacity duration-150 group-hover:opacity-100 group-focus-visible:opacity-100 text-[var(--text-secondary)]">
          <PencilIcon />
        </span>
      </button>

      <p className="mt-2 text-2xl font-semibold tracking-tight text-[var(--text-primary)] font-mono tabular-nums num">
        <FadeValue value={value} />
      </p>
      <p className={`mt-3 text-sm ${emphasis === "positive" ? "text-[var(--gain)]" : emphasis === "negative" ? "text-[var(--loss)]" : "text-[var(--text-secondary)]"}`}>
        {subtext}
      </p>

      {popover}
    </article>
  );
}

type TrendPoint = {
  year: FiscalYear;
  value: number | null;
};

function TrendTooltip({ active, payload, label }: { active?: boolean; payload?: Array<{ value?: number | null }> ; label?: string }) {
  if (!active || !payload?.length) {
    return null;
  }

  const value = payload[0]?.value;

  if (typeof value !== "number") {
    return null;
  }

  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-2)] px-3 py-2 text-xs text-[var(--text-primary)] shadow-[0_12px_30px_rgba(0,0,0,0.35)]">
      <div className="font-medium text-[var(--text-secondary)] uppercase tracking-wider">{label}</div>
      <div className="mt-1 text-[var(--text-primary)] font-mono tabular-nums num">{formatCrValue(value)}</div>
    </div>
  );
}

function TrendCard({ companySlug, metric }: { companySlug: string; metric: FinancialMetric }) {
  const [data, setData] = useState<TrendPoint[]>(
    TREND_YEARS.map((year) => ({ year, value: null })),
  );
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      setIsLoading(true);

      try {
        const points = await Promise.all(
          TREND_YEARS.map(async (year) => {
            try {
              const response = (await getCompanyKpi(companySlug, metric, toApiYear(year))) as KpiResponse;
              return {
                year,
                value: typeof response.value === "number" ? response.value : null,
              };
            } catch {
              return { year, value: null };
            }
          }),
        );

        if (!cancelled) {
          setData(points);
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    };

    if (companySlug) {
      void load();
    } else {
      setData(TREND_YEARS.map((year) => ({ year, value: null })));
      setIsLoading(false);
    }

    return () => {
      cancelled = true;
    };
  }, [companySlug, metric]);

  const chartData = useMemo(
    () =>
      data.map((point) => ({
        year: point.year,
        value: point.value ?? 0,
      })),
    [data],
  );

  return (
    <article className="rounded-2xl border border-[var(--border)] bg-[var(--surface-1)] p-4 h-full shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]">
      {isLoading ? (
        <div className="flex h-full min-h-40 items-center justify-center text-sm text-[var(--text-secondary)]">Loading chart...</div>
      ) : (
        <div className="h-40">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartData} margin={{ top: 4, right: 4, left: 4, bottom: 4 }}>
              <defs>
                <linearGradient id="kpiLineGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#cccccc" stopOpacity={0.08} />
                  <stop offset="100%" stopColor="#cccccc" stopOpacity={0} />
                </linearGradient>
              </defs>
              <Tooltip
                cursor={false}
                content={<TrendTooltip />}
                labelFormatter={(label) => String(label)}
                formatter={(value) => [formatCrValue(Number(value)), ""]}
              />
              <XAxis dataKey="year" axisLine={false} tickLine={false} tick={{ fill: 'var(--text-secondary)', fontSize: 10 }} dy={10} />
              <Bar dataKey="value" fill={BAR_COLOR} fillOpacity={1} radius={[4, 4, 0, 0]} barSize={26} />
              <Area
                type="monotone"
                dataKey="value"
                stroke="none"
                fill="url(#kpiLineGradient)"
                activeDot={false}
              />
              <Line
                type="monotone"
                dataKey="value"
                stroke={LINE_COLOR}
                strokeWidth={2}
                dot={{ r: 2.5, stroke: LINE_COLOR, strokeWidth: 1.25, fill: CARD_BACKGROUND }}
                activeDot={{ r: 4 }}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      )}
    </article>
  );
}

type RiskFlag = {
  metric: string;
  year: string;
  value: number;
  previous_value?: number;
  change?: number;
  rule_triggered: string;
  severity: string;
  unit: string;
};

type RiskReport = {
  flags: RiskFlag[];
};

function RiskFlagsCard({ companySlug }: { companySlug: string }) {
  const [status, setStatus] = useState<"idle" | "loading" | "loaded">("idle");
  const [flags, setFlags] = useState<RiskFlag[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => {
    setStatus("idle");
    setFlags([]);
    setIsModalOpen(false);
  }, [companySlug]);

  const handleScan = async () => {
    setStatus("loading");
    try {
      const response = (await getCompanyRisks(companySlug)) as RiskReport;
      setFlags(response.flags || []);
      setStatus("loaded");
    } catch {
      setStatus("idle");
    }
  };

  const highCount = flags.filter(f => f.severity.toLowerCase() === "high").length;
  const mediumCount = flags.filter(f => f.severity.toLowerCase() === "medium").length;
  
  let badgeColor = "bg-[var(--surface-2)] text-[var(--text-secondary)] border-[var(--border)]";
  if (status === "loaded") {
    if (highCount > 0) badgeColor = "bg-red-500/10 text-red-500 border-red-500/20";
    else if (mediumCount > 0) badgeColor = "bg-amber-500/10 text-amber-500 border-amber-500/20";
    else badgeColor = "bg-emerald-500/10 text-emerald-500 border-emerald-500/20";
  }

  return (
    <>
      <article 
        className={`rounded-2xl border border-[var(--border)] bg-[var(--surface-1)] p-4 h-full shadow-[inset_0_1px_0_rgba(255,255,255,0.04)] ${status === 'loaded' ? 'cursor-pointer hover:border-[var(--text-primary)] transition-colors' : ''}`}
        onClick={() => { if (status === "loaded") setIsModalOpen(true); }}
      >
        <div className="flex items-center justify-between">
            <p className="text-xs font-semibold uppercase tracking-wider text-[var(--text-secondary)]">Risk Flags</p>
            {status === "loaded" && (
                <span className={`px-2 py-0.5 rounded text-[10px] font-semibold tracking-widest uppercase border ${badgeColor}`}>
                    {flags.length} FLAGS
                </span>
            )}
        </div>
        
        {status === "idle" ? (
          <div className="mt-3">
            <button 
                onClick={(e) => { e.stopPropagation(); handleScan(); }}
                className="rounded-full bg-[var(--surface-2)] px-4 py-2 text-sm font-medium text-[var(--text-primary)] border border-[var(--border)] hover:border-[var(--text-primary)] transition-colors w-full"
            >
              Run Risk Scan
            </button>
            <p className="mt-3 text-[11px] text-[var(--text-secondary)] text-center leading-snug">
              Scans financial ratios for red flags across all years
            </p>
          </div>
        ) : status === "loading" ? (
          <div className="mt-4 flex items-center justify-center h-10">
            <p className="text-sm text-[var(--text-secondary)] animate-pulse">Scanning metrics...</p>
          </div>
        ) : (
          <div className="mt-2">
             <p className="text-2xl font-semibold tracking-tight text-[var(--text-primary)] font-mono tabular-nums num">
                {flags.length} <span className="text-base font-sans tracking-normal text-[var(--text-secondary)] font-normal">{flags.length === 1 ? 'flag' : 'flags'} found</span>
             </p>
             <p className="mt-3 text-sm text-[var(--text-secondary)]">Click to view details</p>
          </div>
        )}
      </article>

      {isModalOpen && (
        <RiskModal 
          flags={flags} 
          onClose={() => setIsModalOpen(false)} 
        />
      )}
    </>
  );
}

function RiskModal({ flags, onClose }: { flags: RiskFlag[], onClose: () => void }) {
  const sortedFlags = useMemo(() => {
     return [...flags].sort((a, b) => {
        const sevA = a.severity.toLowerCase() === "high" ? 2 : 1;
        const sevB = b.severity.toLowerCase() === "high" ? 2 : 1;
        if (sevA !== sevB) return sevB - sevA;
        return b.year.localeCompare(a.year);
     });
  }, [flags]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-black/60 backdrop-blur-sm" onClick={onClose}>
      <div 
        className="relative w-full max-w-3xl rounded-2xl border border-[var(--border)] bg-[var(--surface-1)] shadow-2xl flex flex-col max-h-[90vh]"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-[var(--border)] px-6 py-4">
          <h2 className="text-lg font-semibold text-[var(--text-primary)] tracking-tight">Risk Flags Detail</h2>
          <button onClick={onClose} className="p-2 -mr-2 text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors rounded-lg hover:bg-[var(--surface-2)]">
            <svg viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5">
              <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
            </svg>
          </button>
        </div>
        
        <div className="p-6 overflow-y-auto">
          {flags.length === 0 ? (
            <div className="text-center py-12">
              <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-emerald-500/10 text-emerald-500 mb-4">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-6 h-6">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <p className="text-[var(--text-primary)] font-medium">No risk flags detected</p>
              <p className="text-[var(--text-secondary)] text-sm mt-1">All scanned metrics are within normal ranges.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {sortedFlags.map((flag, idx) => {
                const isHigh = flag.severity.toLowerCase() === "high";
                const isDecline = flag.rule_triggered.toLowerCase().includes("dropped") || flag.rule_triggered.toLowerCase().includes("decreased");
                const formattedChange = flag.change !== undefined && flag.change !== null 
                  ? (isDecline ? `-${Math.abs(flag.change).toFixed(1)}%` : `+${Math.abs(flag.change).toFixed(1)}%`)
                  : null;

                return (
                  <div key={idx} className="p-5 rounded-xl border border-[var(--border)] bg-[var(--surface-2)] shadow-sm">
                    <div className="flex justify-between items-start mb-3">
                        <div className="flex items-center gap-2">
                            <span className="font-semibold text-[var(--text-primary)]">{flag.metric}</span>
                            <span className="px-2 py-0.5 rounded bg-[var(--surface-1)] border border-[var(--border)] text-xs font-medium text-[var(--text-secondary)]">{flag.year}</span>
                        </div>
                        <span className={`px-2 py-0.5 rounded text-[10px] tracking-widest font-bold uppercase border ${isHigh ? 'bg-red-500/10 text-red-500 border-red-500/20' : 'bg-amber-500/10 text-amber-500 border-amber-500/20'}`}>
                            {flag.severity}
                        </span>
                    </div>
                    <div className="text-sm text-[var(--text-primary)] mb-4 leading-relaxed bg-[var(--surface-1)] border border-[var(--border)] p-3 rounded-lg">
                        {flag.rule_triggered}
                    </div>
                    <div className="flex flex-wrap gap-x-6 gap-y-2 text-sm font-mono tabular-nums num">
                        <div className="flex items-center gap-2">
                            <span className="text-[var(--text-secondary)] font-sans text-xs uppercase tracking-wider">Value:</span> 
                            <span className="text-[var(--text-primary)] font-medium">{flag.value}{flag.unit}</span>
                        </div>
                        {flag.previous_value !== undefined && flag.previous_value !== null && (
                            <div className="flex items-center gap-2">
                                <span className="text-[var(--text-secondary)] font-sans text-xs uppercase tracking-wider">Previous:</span> 
                                <span className="text-[var(--text-primary)] font-medium">{flag.previous_value}{flag.unit}</span>
                            </div>
                        )}
                        {formattedChange && (
                            <div className="flex items-center gap-2">
                                <span className="text-[var(--text-secondary)] font-sans text-xs uppercase tracking-wider">Change:</span> 
                                <span className={`text-[var(--loss)] font-medium`}>
                                    {formattedChange}
                                </span>
                            </div>
                        )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function KPICards({ companySlug, totalChunks, totalDocs, isCorpusLoading }: KPICardsProps) {
  const [selectedMetric, setSelectedMetric] = useState<FinancialMetric>("Sales");

  useEffect(() => {
    setSelectedMetric("Sales");
  }, [companySlug]);

  const chunksValue = isCorpusLoading ? "Loading..." : totalChunks === undefined || totalChunks === null ? "Unavailable" : new Intl.NumberFormat("en-IN").format(totalChunks);
  const docsValue = isCorpusLoading ? "Loading..." : totalDocs === undefined || totalDocs === null ? "Unavailable" : new Intl.NumberFormat("en-IN").format(totalDocs);

  return (
    <section className="grid items-stretch gap-3 sm:grid-cols-2 xl:grid-cols-4">
      <FinancialKpiCard
        companySlug={companySlug}
        metric={selectedMetric}
        onMetricChange={setSelectedMetric}
        initialYear="FY24"
      />
      <TrendCard companySlug={companySlug} metric={selectedMetric} />
      <KpiCard
        title="Corpus Indexing"
        value={isCorpusLoading ? "Loading..." : `${chunksValue} chunks`}
        subtext={isCorpusLoading ? "Fetching corpus status..." : `${docsValue} docs uploaded`}
        subtextClass="text-lg font-medium"
      />
      <RiskFlagsCard companySlug={companySlug} />
    </section>
  );
}