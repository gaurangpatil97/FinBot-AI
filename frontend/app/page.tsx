import FinbotDashboard from "./components/FinbotDashboard";
import type { StockSummary } from "./components/finbot-types";

async function fetchStockSummary(): Promise<StockSummary> {
  const fallback: StockSummary = {
    companyName: "Craftsman Automation Ltd",
    exchangeLabel: "NSE · CRAFTSMAN",
    ticker: "CRAFTSMAN.NS",
    price: 1842,
    changePercent: 2.3,
    direction: "up",
    points: [
      { label: "Mon", price: 1782 },
      { label: "Tue", price: 1794 },
      { label: "Wed", price: 1812 },
      { label: "Thu", price: 1803 },
      { label: "Fri", price: 1829 },
      { label: "Sat", price: 1836 },
      { label: "Sun", price: 1842 },
    ],
    lastUpdated: "Today",
  };

  try {
    const response = await fetch(
      "https://query1.finance.yahoo.com/v8/finance/chart/CRAFTSMAN.NS?interval=1d&range=7d",
      { cache: "no-store" },
    );

    if (!response.ok) {
      return fallback;
    }

    const payload: unknown = await response.json();
    const result = (payload as {
      chart?: {
        result?: Array<{
          meta?: {
            regularMarketPrice?: number;
            previousClose?: number;
            exchangeName?: string;
            symbol?: string;
            regularMarketTime?: number;
          };
          indicators?: {
            quote?: Array<{
              close?: Array<number | null>;
            }>;
          };
        }>;
      };
    })?.chart?.result?.[0];

    const closes = result?.indicators?.quote?.[0]?.close?.filter(
      (price): price is number => typeof price === "number",
    );

    if (!result || !closes || closes.length === 0) {
      return fallback;
    }

    const previousClose = result.meta?.previousClose ?? closes[0];
    const currentPrice = result.meta?.regularMarketPrice ?? closes[closes.length - 1];
    const changePercent = ((currentPrice - previousClose) / previousClose) * 100;
    const direction: StockSummary["direction"] = changePercent >= 0 ? "up" : "down";

    const points = closes.map((price, index) => ({
      label: `D${index + 1}`,
      price,
    }));

    return {
      companyName: "Craftsman Automation Ltd",
      exchangeLabel: result.meta?.exchangeName ? `${result.meta.exchangeName} · CRAFTSMAN` : "NSE · CRAFTSMAN",
      ticker: result.meta?.symbol ?? "CRAFTSMAN.NS",
      price: currentPrice,
      changePercent,
      direction,
      points,
      lastUpdated: result.meta?.regularMarketTime
        ? new Date(result.meta.regularMarketTime * 1000).toLocaleDateString("en-IN", {
            day: "numeric",
            month: "short",
          })
        : "Today",
    };
  } catch {
    return fallback;
  }
}

export default async function Home() {
  const stock = await fetchStockSummary();

  return (
    <FinbotDashboard stock={stock} />
  );
}
