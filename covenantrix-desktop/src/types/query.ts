/**
 * Query Type Definitions
 * Chat interface and query response types
 */

import { QueryMode } from './document';

export interface Query {
  id: string;
  query: string;
  response: string;
  mode: QueryMode;
  timestamp: Date;
  processingTime: number;
  documentIds?: string[];
  citations?: Citation[];
}

export interface Citation {
  documentId: string;
  documentName: string;
  chunkId?: string;
  relevanceScore: number;
  excerpt: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  citations?: Citation[];
  error?: string;
}

export interface QueryHistoryItem {
  id: string;
  query: string;
  preview: string;
  timestamp: Date;
  mode: QueryMode;
}