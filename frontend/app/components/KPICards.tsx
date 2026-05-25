"use client";

interface KPICardsProps {
  revenue: string;
  margin: string;
  chunksIndexed: string;
  docsUploaded: string;
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
  emphasis?: "neutral" | "positive" | "warning" | "danger";
}) {
  const accentClass =
    emphasis === "positive"
      ? "text-emerald-400"
      : emphasis === "warning"
        ? "text-amber-300"
        : emphasis === "danger"
          ? "text-rose-300"
          : "text-zinc-400";

  return (
    <article className="rounded-2xl border border-[#30363d] bg-[#1c2128] p-4">
      <p className="text-sm font-medium text-zinc-400">{title}</p>
      <p className="mt-2 text-2xl font-semibold tracking-tight text-white">{value}</p>
      <p className={`mt-3 text-sm ${accentClass}`}>{subtext}</p>
    </article>
  );
}

export default function KPICards({
  revenue,
  margin,
  chunksIndexed,
  docsUploaded,
}: KPICardsProps) {
  return (
    <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
      <KpiCard
        title="Revenue FY24"
        value={revenue}
        subtext="+4.2% YoY"
        emphasis="positive"
      />
      <KpiCard
        title="Net Profit Margin"
        value={margin}
        subtext="-1.8pp YoY"
        emphasis="danger"
      />
      <KpiCard
        title="Chunks Indexed"
        value={chunksIndexed}
        subtext="Across 4 collections"
        emphasis="warning"
      />
      <KpiCard
        title="Docs Uploaded"
        value={docsUploaded}
        subtext="Last sync: today"
      />
    </section>
  );
}