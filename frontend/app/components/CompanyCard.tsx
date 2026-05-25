"use client";

import { useEffect, useState } from "react";

import {
  Area,
  AreaChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { StockSummary } from "./finbot-types";

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
  const strokeColor = stock.direction === "up" ? "#63b365" : "#ef6767";

  useEffect(() => {
    setHasMounted(true);
  }, []);

  return (
    <article className="rounded-2xl border border-white/8 bg-[#1c2128] p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-white">{stock.companyName}</p>
          <div className="mt-2 flex gap-2">
            <span className="rounded-full border border-white/8 bg-white/5 px-2.5 py-1 text-[11px] font-medium text-zinc-200">
              NSE
            </span>
            <span className="rounded-full border border-white/8 bg-white/5 px-2.5 py-1 text-[11px] font-medium text-zinc-200">
              BSE
            </span>
          </div>
        </div>
        <div className={`text-sm font-semibold ${stock.direction === "up" ? "text-emerald-400" : "text-rose-400"}`}>
          {formatChange(stock.changePercent)}
        </div>
      </div>

      <div className="mt-3 flex items-end justify-between gap-3">
        <p className="text-3xl font-semibold tracking-tight text-white">₹{formatCurrency(stock.price)}</p>
        <p className="pb-1 text-xs uppercase tracking-[0.22em] text-zinc-500">{stock.exchangeLabel}</p>
      </div>

      <div className="mt-4 h-20 rounded-xl border border-white/8 bg-[#11161d] p-2">
        {hasMounted ? (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={stock.points} margin={{ top: 8, right: 0, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="company-sparkline" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={strokeColor} stopOpacity={0.32} />
                  <stop offset="95%" stopColor={strokeColor} stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <XAxis dataKey="label" hide />
              <YAxis hide domain={["dataMin - 10", "dataMax + 10"]} />
              <Tooltip
                contentStyle={{
                  background: "#0f1117",
                  border: "1px solid rgba(255,255,255,0.08)",
                  borderRadius: 12,
                  color: "#fff",
                }}
                cursor={{ stroke: "rgba(255,255,255,0.08)" }}
              />
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
          <div className="flex h-full items-center justify-center rounded-lg bg-[linear-gradient(90deg,rgba(47,129,247,0.16),rgba(99,179,101,0.08),rgba(239,103,103,0.08))]">
            <div className="h-2 w-20 rounded-full bg-white/10" />
          </div>
        )}
      </div>

      <div className="mt-3 flex items-center justify-between text-xs text-[#8b949e]">
        <span>Last 7 sessions</span>
        <span>{stock.lastUpdated}</span>
      </div>
    </article>
  );
}