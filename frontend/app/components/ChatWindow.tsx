"use client";

import { useEffect, useRef } from "react";

import CitationBadge from "./CitationBadge";
import type { ChatMessage } from "./finbot-types";

interface ChatWindowProps {
  messages: ChatMessage[];
}

export default function ChatWindow({ messages }: ChatWindowProps) {
  const viewportRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const viewport = viewportRef.current;

    if (!viewport) {
      return;
    }

    viewport.scrollTo({ top: viewport.scrollHeight, behavior: "smooth" });
  }, [messages]);

  return (
    <section
      ref={viewportRef}
      className="flex h-full flex-1 flex-col gap-4 overflow-y-auto p-4"
    >
      {messages.map((message) => {
        const assistant = message.role === "assistant";

        return (
          <div
            key={message.id}
            className={`flex items-end gap-3 ${assistant ? "justify-start" : "justify-end"}`}
          >
            {assistant ? (
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[#11161d] text-sm font-semibold text-blue-300 ring-1 ring-blue-400/20">
                AI
              </div>
            ) : null}

            <div
              className={`max-w-[min(34rem,82%)] rounded-2xl border px-4 py-3 text-sm leading-6 ${
                assistant
                  ? "border-white/8 bg-[#11161d] text-zinc-100"
                  : "border-blue-400/20 bg-[#dfeeff] text-slate-900"
              }`}
            >
              {message.isLoading ? (
                <div className="flex items-center gap-2 text-zinc-300">
                  <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-blue-300" />
                  <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-blue-300 [animation-delay:120ms]" />
                  <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-blue-300 [animation-delay:240ms]" />
                </div>
              ) : (
                <p className="whitespace-pre-line">{message.content}</p>
              )}
              {!message.isLoading && message.citations && message.citations.length > 0 ? (
                <div className="mt-3 flex flex-wrap gap-2">
                  {message.citations.map((citation, index) => (
                    <CitationBadge key={`${citation.label}-${index}`} label={citation.label} />
                  ))}
                </div>
              ) : null}
            </div>

            {!assistant ? (
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[#11161d] text-sm font-semibold text-emerald-300 ring-1 ring-emerald-400/20">
                U
              </div>
            ) : null}
          </div>
        );
      })}
    </section>
  );
}