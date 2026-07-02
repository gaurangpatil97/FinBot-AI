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
    <aside className="flex w-full shrink-0 flex-col border-b border-[var(--border)] bg-[var(--bg)] lg:h-screen lg:w-[295px] lg:border-b-0 lg:border-[var(--border)] no-scrollbar overflow-x-hidden" style={{ overflow: "hidden", scrollbarWidth: "none" }}>
      <div className="border-b border-[var(--border)] px-4 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="grid h-9 w-9 place-items-center rounded-xl border border-[var(--border)] bg-[var(--surface-1)] text-lg font-semibold text-[var(--text-primary)]">
            ⚡
          </div>
          <div>
            <div className="flex items-center gap-2">
              <p className="text-lg font-semibold text-[var(--text-primary)]">FinBot</p>
              <span className="rounded bg-[var(--surface-3)] px-1.5 py-0.5 text-[10px] font-medium text-[var(--text-primary)]">beta</span>
            </div>
            <p className="text-xs text-[var(--text-secondary)]">Research workspace</p>
          </div>
        </div>
        <button
          type="button"
          onClick={onOpenUpload}
          title="Upload new dataset"
          className="grid h-9 w-9 place-items-center rounded-xl border border-[var(--border)] bg-[var(--surface-1)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--border-strong)] transition shadow-sm cursor-pointer"
        >
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="h-4 w-4"
          >
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="17 8 12 3 7 8" />
            <line x1="12" y1="3" x2="12" y2="15" />
          </svg>
        </button>
      </div>

      <div className="flex-1 overflow-hidden px-4 py-4 space-y-4">
        <div className="relative">
          <button
            type="button"
            onClick={() => setMenuOpen((current) => !current)}
            className="flex w-full items-center justify-between rounded-2xl border border-[var(--border)] bg-[var(--surface-1)] px-4 py-3 text-left transition hover:border-[var(--border-strong)] shadow-[inset_0_1px_0_rgba(245,243,238,0.04)]"
          >
            <div>
              <p className="text-sm font-medium text-[var(--text-secondary)]">Company</p>
              <p className="mt-1 text-sm font-semibold text-[var(--text-primary)]">{activeCompany}</p>
            </div>
            <span className={`text-[var(--text-secondary)] transition ${menuOpen ? "rotate-180" : ""}`}>⌄</span>
          </button>

          {menuOpen ? (
            <div className="absolute left-0 right-0 top-[calc(100%+8px)] z-10 overflow-hidden rounded-2xl border border-[var(--border)] bg-[var(--surface-1)] shadow-[0_20px_40px_rgba(0,0,0,0.35)]">
              {companies.map((company) => (
                <button
                  key={company}
                  type="button"
                  onClick={() => {
                    setMenuOpen(false);
                    onSelectCompany(company);
                  }}
                  className={`flex w-full items-center justify-between px-4 py-3 text-left text-sm transition hover:bg-[var(--surface-2)] ${
                    company === activeCompany ? "text-[var(--text-primary)]" : "text-[var(--text-secondary)]"
                  }`}
                >
                  <span>{company}</span>
                  {company === activeCompany ? <span className="text-[var(--text-primary)]">●</span> : null}
                </button>
              ))}
              <button
                type="button"
                onClick={() => {
                  setMenuOpen(false);
                  onSelectCompany("New Dataset");
                }}
                className="flex w-full items-center justify-between border-t border-[var(--border)] px-4 py-3 text-left text-sm font-medium text-[var(--text-primary)] transition hover:bg-[var(--surface-2)]"
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

      <div className="border-t border-[var(--border)] p-4">
        <button
          type="button"
          onClick={onOpenUpload}
          className="flex w-full items-center justify-center gap-2 rounded-2xl bg-[#e8ddc7] px-4 py-3 text-sm font-semibold text-[#0a0a0c] transition hover:opacity-90"
        >
          <span className="text-base">＋</span>
          Upload Dataset
        </button>
      </div>
    </aside>
  );
}