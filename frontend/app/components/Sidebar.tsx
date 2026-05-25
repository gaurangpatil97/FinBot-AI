"use client";

import { useState } from "react";

import CompanyCard from "./CompanyCard";
import CorpusStatus from "./CorpusStatus";
import type { CollectionKey, CollectionRecord, CorpusFileRecord, StockSummary } from "./finbot-types";

interface SidebarProps {
  stock: StockSummary;
  activeCompany: string;
  activeCompanySlug: string;
  companies: string[];
  collections: CollectionRecord[];
  filesByCollection: Record<CollectionKey, CorpusFileRecord[]>;
  onSelectCompany: (value: string) => void;
  onOpenUpload: () => void;
}

export default function Sidebar({
  stock,
  activeCompany,
  activeCompanySlug,
  companies,
  collections,
  filesByCollection,
  onSelectCompany,
  onOpenUpload,
}: SidebarProps) {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <aside className="flex w-full shrink-0 flex-col border-b border-white/8 bg-[#161b22] lg:h-screen lg:w-70 lg:border-b-0 lg:border-r lg:border-white/8">
      <div className="border-b border-white/8 px-4 py-4">
        <div className="flex items-center gap-3">
          <div className="grid h-9 w-9 place-items-center rounded-xl border border-blue-400/35 bg-blue-500/10 text-lg font-semibold text-blue-300">
            ⚡
          </div>
          <div>
            <p className="text-lg font-semibold text-white">FinbotAI</p>
            <p className="text-xs text-[#8b949e]">Beta research workspace</p>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        <div className="relative">
          <button
            type="button"
            onClick={() => setMenuOpen((current) => !current)}
            className="flex w-full items-center justify-between rounded-2xl border border-white/8 bg-[#1c2128] px-4 py-3 text-left transition hover:border-white/12"
          >
            <div>
              <p className="text-xs uppercase tracking-[0.22em] text-[#8b949e]">Company</p>
              <p className="mt-1 text-sm font-semibold text-white">{activeCompany}</p>
            </div>
            <span className={`text-[#8b949e] transition ${menuOpen ? "rotate-180" : ""}`}>⌄</span>
          </button>

          {menuOpen ? (
            <div className="absolute left-0 right-0 top-[calc(100%+8px)] z-10 overflow-hidden rounded-2xl border border-white/8 bg-[#1c2128] shadow-[0_20px_40px_rgba(0,0,0,0.35)]">
              {companies.map((company) => (
                <button
                  key={company}
                  type="button"
                  onClick={() => {
                    setMenuOpen(false);
                    onSelectCompany(company);
                  }}
                  className={`flex w-full items-center justify-between px-4 py-3 text-left text-sm transition hover:bg-white/5 ${
                    company === activeCompany ? "text-white" : "text-[#8b949e]"
                  }`}
                >
                  <span>{company}</span>
                  {company === activeCompany ? <span className="text-blue-400">●</span> : null}
                </button>
              ))}
              <button
                type="button"
                onClick={() => {
                  setMenuOpen(false);
                  onSelectCompany("New Dataset");
                }}
                className="flex w-full items-center justify-between border-t border-white/8 px-4 py-3 text-left text-sm font-medium text-blue-300 transition hover:bg-blue-500/10"
              >
                <span>New Dataset</span>
                <span>+</span>
              </button>
            </div>
          ) : null}
        </div>

        <CompanyCard stock={stock} />
        <CorpusStatus
          collections={collections}
          filesByCollection={filesByCollection}
          companySlug={activeCompanySlug}
        />
      </div>

      <div className="border-t border-white/8 p-4">
        <button
          type="button"
          onClick={onOpenUpload}
          className="flex w-full items-center justify-center gap-2 rounded-2xl bg-blue-500 px-4 py-3 text-sm font-semibold text-white transition hover:bg-blue-400"
        >
          <span className="text-base">＋</span>
          Upload Dataset
        </button>
      </div>
    </aside>
  );
}