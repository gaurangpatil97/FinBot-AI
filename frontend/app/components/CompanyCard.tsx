"use client";

import { useEffect, useState } from "react";

import {
  Area,
  AreaChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  ReferenceLine,
} from "recharts";

import type { StockSummary } from "./finbot-types";

function SparklineTooltip({ active, payload, label }: any) {
  if (active && payload && payload.length) {
    return (
      <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-2)] px-3 py-2 text-xs text-[var(--text-primary)] shadow-[0_12px_30px_rgba(0,0,0,0.35)]">
        <div className="font-medium text-[var(--text-secondary)] uppercase tracking-wider">{label}</div>
        <div className="mt-1 text-[var(--text-primary)] font-mono tabular-nums num">₹{formatCurrency(payload[0].value)}</div>
      </div>
    );
  }
  return null;
}

interface CompanyCardProps {
  stock: StockSummary;
}

function formatCurrency(price: number) {
  return new Intl.NumberFormat("en-IN", {
    maximumFractionDigits: 0,
  }).format(price);
}

function formatChange(changePercent: number) {
  const sign = changePercent >= 0 ? "+" : "";
  return `${sign}${changePercent.toFixed(1)}%`;
}

export default function CompanyCard({ stock }: CompanyCardProps) {
  const [hasMounted, setHasMounted] = useState(false);
  const strokeColor = "#ffffff";

  useEffect(() => {
    setHasMounted(true);
  }, []);

  const minPrice = Math.min(...stock.points.map(p => p.price));
  const maxPrice = Math.max(...stock.points.map(p => p.price));

  return (
    <article className="rounded-2xl border border-[var(--border)] bg-[var(--surface-1)] p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-[var(--text-primary)]">{stock.companyName}</p>
          <div className="mt-2 flex gap-2">
            <span className="rounded-full border border-white/8 bg-white/5 px-2.5 py-1 text-[11px] font-medium text-zinc-200">
              NSE
            </span>
            <span className="rounded-full border border-white/8 bg-white/5 px-2.5 py-1 text-[11px] font-medium text-zinc-200">
              BSE
            </span>
          </div>
        </div>
        <div className={`text-sm font-semibold ${stock.direction === "up" ? "text-[#22c55e]" : "text-[#ef4444]"}`}>
          {formatChange(stock.changePercent)}
        </div>
      </div>

      <div className="mt-3 flex items-end justify-between gap-3">
        <p className="text-3xl font-semibold tracking-tight text-[var(--text-primary)] font-mono tabular-nums num">₹{formatCurrency(stock.price)}</p>
        <p className="pb-1 text-xs uppercase tracking-[0.22em] text-[var(--text-secondary)]">{stock.exchangeLabel.replace("NSI", "NSE")}</p>
      </div>

      <div className="mt-4 h-20 rounded-xl border border-[var(--border)] bg-[var(--surface-2)] p-2">
        {hasMounted ? (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={stock.points} margin={{ top: 8, right: 0, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="company-sparkline" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={strokeColor} stopOpacity={0.15} />
                  <stop offset="95%" stopColor={strokeColor} stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="label" hide />
              <YAxis hide domain={["dataMin - 10", "dataMax + 10"]} />
              <Tooltip
                content={<SparklineTooltip />}
                cursor={{ stroke: "rgba(255,255,255,0.08)" }}
              />
              <ReferenceLine y={maxPrice} stroke="none" label={{ position: 'insideTopLeft', value: formatCurrency(maxPrice), fill: 'var(--text-secondary)', fontSize: 10, offset: 2, className: 'num' }} />
              <ReferenceLine y={minPrice} stroke="none" label={{ position: 'insideBottomLeft', value: formatCurrency(minPrice), fill: 'var(--text-secondary)', fontSize: 10, offset: 2, className: 'num' }} />
              <Area
                type="monotone"
                dataKey="price"
                stroke={strokeColor}
                fill="url(#company-sparkline)"
                strokeWidth={2}
                dot={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <div className="flex h-full items-center justify-center rounded-lg bg-[var(--surface-1)]">
            <div className="h-2 w-20 rounded-full bg-white/10" />
          </div>
        )}
      </div>

      <div className="mt-3 flex items-center justify-between text-xs text-[var(--text-secondary)]">
        <span>Last 7 sessions</span>
        <span>{stock.lastUpdated}</span>
      </div>
    </article>
  );
}