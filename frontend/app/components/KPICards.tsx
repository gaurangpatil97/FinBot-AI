"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import {
  Bar,
  Area,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
} from "recharts";

import { getCompanyKpi, getCompanyStatus } from "../../lib/api";

type FinancialMetric = "Sales" | "Net profit" | "EBITDA" | "Borrowings";
type FiscalYear = "FY22" | "FY23" | "FY24" | "FY25";

interface KPICardsProps {
  companySlug: string;
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
  const sign = delta >= 0 ? "+" : "-";

  return `${sign}₹${new Intl.NumberFormat("en-IN", { maximumFractionDigits: 2 }).format(Math.abs(delta))} Cr YoY`;
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
}: {
  title: string;
  value: string;
  subtext: string;
  emphasis?: "neutral" | "positive" | "warning";
}) {
  const accentClass =
    subtext.startsWith("+")
      ? "text-[#22c55e]"
      : subtext.startsWith("-")
        ? "text-[#ef4444]"
        : "text-[#888888]";

  return (
    <article className="rounded-2xl border border-[#222222] bg-[#111111] p-4 h-full">
      <p className="text-xs font-semibold uppercase tracking-wider text-[#888888]">{title}</p>
      <p className="mt-2 text-2xl font-semibold tracking-tight text-white font-mono tabular-nums">{value}</p>
      <p className={`mt-3 text-sm ${accentClass}`}>{subtext}</p>
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
    ? "border-white bg-white text-black"
    : "border-[#222222] bg-[#111111] text-[#888888] hover:border-white/20 hover:text-white";
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
    <div className="absolute left-0 top-[calc(100%+0.5rem)] z-20 w-[min(20rem,calc(100vw-2rem))] rounded-2xl border border-[#222222] bg-[#0a0a0a] p-3 shadow-[0_20px_50px_rgba(0,0,0,0.45)] backdrop-blur-sm">
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
    <article ref={containerRef} className="relative rounded-2xl border border-[#222222] bg-[#111111] p-4 h-full">
      <button
        type="button"
        onClick={() => setIsPopoverOpen((current) => !current)}
        className="group flex items-center gap-2 text-left outline-none"
      >
        <p className="text-xs font-semibold uppercase tracking-wider text-[#888888] transition-colors group-hover:text-white">{title}</p>
        <span className="opacity-0 transition-opacity duration-150 group-hover:opacity-100 group-focus-visible:opacity-100 text-[#888888]">
          <PencilIcon />
        </span>
      </button>

      <p className="mt-2 text-2xl font-semibold tracking-tight text-white font-mono tabular-nums">
        <FadeValue value={value} />
      </p>
      <p className={`mt-3 text-sm ${emphasis === "positive" ? "text-[#22c55e]" : emphasis === "negative" ? "text-[#ef4444]" : "text-[#888888]"}`}>
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
    <div className="rounded-xl border border-[#222222] bg-[#0a0a0a] px-3 py-2 text-xs text-white shadow-[0_12px_30px_rgba(0,0,0,0.35)]">
      <div className="font-medium text-[#888888] uppercase tracking-wider">{label}</div>
      <div className="mt-1 text-white font-mono tabular-nums">{formatCrValue(value)}</div>
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
    <article className="rounded-2xl border border-[#222222] bg-[#111111] p-4 h-full">
      {isLoading ? (
        <div className="flex h-full min-h-40 items-center justify-center text-sm text-zinc-500">Loading chart...</div>
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

export default function KPICards({ companySlug }: KPICardsProps) {
  const [selectedMetric, setSelectedMetric] = useState<FinancialMetric>("Sales");
  const [chunksIndexed, setChunksIndexed] = useState<number | null>(null);
  const [docsUploaded, setDocsUploaded] = useState<number | null>(null);
  const [isCorpusLoading, setIsCorpusLoading] = useState(true);

  useEffect(() => {
    setSelectedMetric("Sales");
  }, [companySlug]);

  useEffect(() => {
    let cancelled = false;

    const loadCorpusStatus = async () => {
      setIsCorpusLoading(true);

      try {
        const status = await getCompanyStatus(companySlug);
        const collectionEntries = Object.values((status as { collections?: Record<string, { chunks?: number }> }).collections ?? {});
        const totalChunks = collectionEntries.reduce(
          (sum, collection) => sum + (typeof collection?.chunks === "number" ? collection.chunks : 0),
          0,
        );
        const fileRecords = Array.isArray((status as { files?: unknown }).files) ? ((status as { files?: Array<{ file_id?: string }> }).files ?? []) : [];
        const totalDocs = fileRecords.length;

        if (cancelled) {
          return;
        }

        setChunksIndexed(totalChunks);
        setDocsUploaded(totalDocs);
      } catch {
        if (cancelled) {
          return;
        }

        setChunksIndexed(null);
        setDocsUploaded(null);
      } finally {
        if (!cancelled) {
          setIsCorpusLoading(false);
        }
      }
    };

    if (companySlug) {
      void loadCorpusStatus();
    } else {
      setChunksIndexed(null);
      setDocsUploaded(null);
      setIsCorpusLoading(false);
    }

    return () => {
      cancelled = true;
    };
  }, [companySlug]);

  const chunksValue = isCorpusLoading ? "Loading..." : chunksIndexed === null ? "Unavailable" : new Intl.NumberFormat("en-IN").format(chunksIndexed);
  const docsValue = isCorpusLoading ? "Loading..." : docsUploaded === null ? "Unavailable" : new Intl.NumberFormat("en-IN").format(docsUploaded);

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
        title="Chunks Indexed"
        value={chunksValue}
        subtext={isCorpusLoading ? "Fetching corpus status..." : "Across all collections"}
        emphasis="warning"
      />
      <KpiCard
        title="Docs Uploaded"
        value={docsValue}
        subtext={isCorpusLoading ? "Fetching corpus status..." : "From corpus status API"}
      />
    </section>
  );
}