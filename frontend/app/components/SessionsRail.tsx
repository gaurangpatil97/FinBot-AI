"use client";

import React, { useState } from "react";
import { useSessions } from "../context/SessionContext";

function formatRelativeTime(dateString: string) {
  const date = new Date(dateString);
  const now = new Date();
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);
  
  if (diffInSeconds < 60) return "Just now";
  if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
  if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
  return `${Math.floor(diffInSeconds / 86400)}d ago`;
}

export default function SessionsRail({ activeCompanySlug }: { activeCompanySlug: string }) {
  const { 
    sessions, 
    activeSessionId, 
    switchSession, 
    deleteSessionOptimistic, 
    renameSessionOptimistic,
    clearState,
    isRailOpen,
    setIsRailOpen
  } = useSessions();
  
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");

  const handleRename = (e: React.KeyboardEvent, id: string) => {
    if (e.key === "Enter" && editTitle.trim()) {
      renameSessionOptimistic(id, editTitle.trim());
      setEditingId(null);
    } else if (e.key === "Escape") {
      setEditingId(null);
    }
  };

  return (
    <div 
      className={`flex-shrink-0 border-l border-[#222] bg-[#0a0a0a] flex flex-col h-full transition-all duration-200 ease-in-out relative ${isRailOpen ? 'w-64' : 'w-10'}`}
    >
      {/* Collapsed State Strip */}
      {!isRailOpen && (
        <button 
          onClick={() => setIsRailOpen(true)}
          className="w-full h-full flex flex-col items-center py-4 hover:bg-[var(--surface-2)] transition-colors group text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
          title="Chat history"
        >
          <svg className="w-5 h-5 mb-4 group-hover:scale-110 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </button>
      )}

      {/* Expanded State */}
      {isRailOpen && (
        <>
          <div className="p-4 border-b border-[#222] flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold text-[var(--text-primary)]">Chats</h2>
              <button 
                onClick={() => setIsRailOpen(false)}
                className="p-1 rounded hover:bg-[var(--surface-3)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
                title="Collapse chat history"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" /></svg>
              </button>
            </div>
            <button 
              onClick={clearState}
              className="w-full py-2 px-4 rounded-xl border border-[var(--accent)] bg-transparent text-[var(--accent)] hover:bg-[rgba(245,243,238,0.08)] text-sm font-semibold transition-all duration-150 flex items-center justify-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>
              New chat
            </button>
          </div>
          
          <div className="flex-1 overflow-y-auto p-3">
            {sessions.length === 0 ? (
              <div className="text-sm text-[var(--text-secondary)] p-4 text-center mt-4">
                No chats yet — ask something to start.
              </div>
            ) : (
              <div className="flex flex-col gap-1.5">
                {sessions.map(s => {
                  const isActive = s.id === activeSessionId;
                  const isEditing = editingId === s.id;
                  
                  return (
                    <div 
                      key={s.id} 
                      className={`group flex flex-col px-3 py-2.5 rounded-xl cursor-pointer transition-colors relative border-l-2
                        ${isActive ? "bg-[var(--surface-2)] border-[var(--accent)]" : "bg-transparent hover:bg-[var(--surface-2)] border-transparent"}
                      `}
                      onClick={() => { if (!isEditing) switchSession(s.id); }}
                    >
                      <div className="flex items-center justify-between">
                        {isEditing ? (
                          <input 
                            autoFocus
                            type="text" 
                            className="bg-[#111] text-sm text-[var(--text-primary)] outline-none w-full mr-2 rounded px-1.5 py-0.5 border border-[var(--border-strong)]"
                            value={editTitle}
                            onChange={e => setEditTitle(e.target.value)}
                            onKeyDown={e => handleRename(e, s.id)}
                            onBlur={() => setEditingId(null)}
                          />
                        ) : (
                          <div className="text-sm font-medium text-[var(--text-primary)] truncate pr-14" title={s.title}>
                            {s.title}
                          </div>
                        )}
                      </div>
                      <div className="text-xs text-[var(--text-muted)] mt-1.5">
                        {formatRelativeTime(s.updated_at)}
                      </div>
                      
                      {!isEditing && (
                        <div className="absolute right-2 top-3 opacity-0 group-hover:opacity-100 flex items-center gap-1 px-1 py-0.5">
                          <button 
                            onClick={(e) => { e.stopPropagation(); setEditTitle(s.title); setEditingId(s.id); }}
                            className="p-1 text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
                            title="Rename"
                          >
                            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" /></svg>
                          </button>
                          <button 
                            onClick={(e) => { e.stopPropagation(); deleteSessionOptimistic(s.id); }}
                            className="p-1 text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
                            title="Delete"
                          >
                            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                          </button>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
