export type CollectionKey = "excel" | "pdf" | "concall" | "images";

export type EmbeddingStatus = "no-embeddings" | "processing" | "uploaded" | "ready" | "failed";

export type DocumentStatus = "none" | "processing" | "ready";

export type FiscalYear = "FY20" | "FY21" | "FY22" | "FY23" | "FY24" | "FY25" | "FY26";

export type FinancialQuarter = "Q1" | "Q2" | "Q3" | "Q4";

export type ChatRole = "user" | "assistant";

export interface StockPoint {
  label: string;
  price: number;
}

export interface StockSummary {
  companyName: string;
  exchangeLabel: string;
  ticker: string;
  price: number;
  changePercent: number;
  direction: "up" | "down";
  points: StockPoint[];
  lastUpdated: string;
}

export interface DocumentRecord {
  id: string;
  group: CollectionKey;
  name: string;
  status: DocumentStatus;
}

export interface CollectionRecord {
  key: CollectionKey;
  label: string;
  fileName: string;
  status: EmbeddingStatus;
  description: string;
  chunks?: number;
}

export interface CorpusFileRecord {
  id: string;
  name: string;
  collection: CollectionKey;
  chunks: number;
}

export interface UploadedFileMetadata {
  id: string;
  collection: CollectionKey;
  name: string;
  status: EmbeddingStatus;
  year?: FiscalYear;
  quarter?: FinancialQuarter;
}

export interface SavedCollectionState {
  key: CollectionKey;
  label: string;
  description: string;
  fileName: string;
  status: EmbeddingStatus;
  files: UploadedFileMetadata[];
}

export interface SavedDatasetSession {
  companyName: string;
  ticker: string;
  collections: SavedCollectionState[];
  readyCollections: number;
  chunks: number;
  savedAt: string;
}

export interface CitationRecord {
  label: string;
}

export interface ChatMessage {
  id: string;
  role: ChatRole;
  content: string;
  citations?: CitationRecord[];
  isLoading?: boolean;
}