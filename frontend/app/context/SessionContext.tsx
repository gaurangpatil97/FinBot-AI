"use client";

import React, { createContext, useContext, useState, useCallback } from "react";
import { getSessions, getSessionMessages, renameSession, deleteSession } from "../../lib/api";
import type { ChatSession, ChatMessage } from "../components/finbot-types";

interface SessionContextType {
  activeSessionId: string | null;
  sessions: ChatSession[];
  messages: ChatMessage[];
  setActiveSessionId: (id: string | null) => void;
  setMessages: React.Dispatch<React.SetStateAction<ChatMessage[]>>;
  loadSessions: (companySlug: string) => Promise<void>;
  switchSession: (id: string) => Promise<void>;
  renameSessionOptimistic: (id: string, newTitle: string) => Promise<void>;
  deleteSessionOptimistic: (id: string) => Promise<void>;
  clearState: () => void;
  isRailOpen: boolean;
  setIsRailOpen: (open: boolean) => void;
}

const SessionContext = createContext<SessionContextType | undefined>(undefined);

export function SessionProvider({ children }: { children: React.ReactNode }) {
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isRailOpen, setIsRailOpen] = useState(false);

  const loadSessions = useCallback(async (companySlug: string) => {
    try {
      const data = await getSessions(companySlug);
      setSessions(data?.value || data || []);
    } catch (err) {
      console.error("Failed to load sessions:", err);
      setSessions([]);
    }
  }, []);

  const switchSession = useCallback(async (id: string) => {
    try {
      const data = await getSessionMessages(id);
      const rawMessages = data?.value || data || [];
      const formattedMessages: ChatMessage[] = rawMessages.map((m: any) => {
        let citations = [];
        let routingSource = "Unknown";
        
        try {
          if (m.citations) citations = JSON.parse(m.citations);
        } catch(e) {}
        
        try {
          if (m.routing_debug) {
             const debug = JSON.parse(m.routing_debug);
             if (debug?.source_types?.length > 0) {
               routingSource = debug.source_types.map((s: string) => s.charAt(0).toUpperCase() + s.slice(1)).join(", ");
             }
          }
        } catch(e) {}

        return {
          id: m.id,
          role: m.role,
          content: m.content,
          citations,
          routingSource,
          latency: m.latency ? m.latency.toString() : undefined,
        };
      });
      setMessages(formattedMessages);
      setActiveSessionId(id);
      if (typeof window !== "undefined") {
         window.localStorage.setItem("activeSessionId", id);
      }
    } catch (err) {
      console.error("Failed to switch session:", err);
    }
  }, []);

  const renameSessionOptimistic = useCallback(async (id: string, newTitle: string) => {
    setSessions(prev => prev.map(s => s.id === id ? { ...s, title: newTitle } : s));
    try {
      await renameSession(id, newTitle);
    } catch (err) {
      console.error("Failed to rename:", err);
      // Rollback could be handled here
    }
  }, []);

  const deleteSessionOptimistic = useCallback(async (id: string) => {
    setSessions(prev => prev.filter(s => s.id !== id));
    if (activeSessionId === id) {
      setActiveSessionId(null);
      setMessages([]);
      if (typeof window !== "undefined") {
         window.localStorage.removeItem("activeSessionId");
      }
    }
    try {
      await deleteSession(id);
    } catch (err) {
      console.error("Failed to delete:", err);
    }
  }, [activeSessionId]);

  const clearState = useCallback(() => {
    setActiveSessionId(null);
    setMessages([]);
    if (typeof window !== "undefined") {
       window.localStorage.removeItem("activeSessionId");
    }
  }, []);

  return (
    <SessionContext.Provider
      value={{
        activeSessionId,
        sessions,
        messages,
        setActiveSessionId,
        setMessages,
        loadSessions,
        switchSession,
        renameSessionOptimistic,
        deleteSessionOptimistic,
        clearState,
        isRailOpen,
        setIsRailOpen
      }}
    >
      {children}
    </SessionContext.Provider>
  );
}

export function useSessions() {
  const context = useContext(SessionContext);
  if (context === undefined) {
    throw new Error("useSessions must be used within a SessionProvider");
  }
  return context;
}
