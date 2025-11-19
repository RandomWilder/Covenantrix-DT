/**
 * Summary Store - Background Progress Tracking
 * Using Zustand for summary generation state management
 */

import { create } from 'zustand'
import { SummaryProgressUpdate } from '../types/document'

export interface SummaryProgress {
  documentId: string
  stage: string
  progress: number
  message: string
  currentBatch?: number
  totalBatches?: number
  error?: string
}

interface SummaryStore {
  // Active summaries being generated
  activeSummaries: Map<string, SummaryProgress>
  
  // Completed summaries (cached)
  completedSummaries: Set<string>
  
  // Failed summaries
  failedSummaries: Map<string, string> // documentId -> error message
  
  // Actions
  startSummary: (documentId: string) => void
  updateProgress: (documentId: string, update: SummaryProgressUpdate) => void
  completeSummary: (documentId: string) => void
  failSummary: (documentId: string, error: string) => void
  clearSummary: (documentId: string) => void
  isGenerating: (documentId: string) => boolean
  hasCompleted: (documentId: string) => boolean
  getProgress: (documentId: string) => SummaryProgress | undefined
  getError: (documentId: string) => string | undefined
}

export const useSummaryStore = create<SummaryStore>((set, get) => ({
  activeSummaries: new Map(),
  completedSummaries: new Set(),
  failedSummaries: new Map(),

  startSummary: (documentId: string) => {
    set((state) => {
      const newActiveSummaries = new Map(state.activeSummaries)
      newActiveSummaries.set(documentId, {
        documentId,
        stage: 'initializing',
        progress: 0,
        message: 'Starting summary generation...'
      })

      // Remove from completed/failed sets
      const newCompletedSummaries = new Set(state.completedSummaries)
      newCompletedSummaries.delete(documentId)
      
      const newFailedSummaries = new Map(state.failedSummaries)
      newFailedSummaries.delete(documentId)

      return {
        activeSummaries: newActiveSummaries,
        completedSummaries: newCompletedSummaries,
        failedSummaries: newFailedSummaries
      }
    })
  },

  updateProgress: (documentId: string, update: SummaryProgressUpdate) => {
    set((state) => {
      const newActiveSummaries = new Map(state.activeSummaries)
      newActiveSummaries.set(documentId, {
        documentId,
        stage: update.stage,
        progress: update.progress_percent,
        message: update.message,
        currentBatch: update.current_batch,
        totalBatches: update.total_batches
      })

      return { activeSummaries: newActiveSummaries }
    })
  },

  completeSummary: (documentId: string) => {
    set((state) => {
      const newActiveSummaries = new Map(state.activeSummaries)
      newActiveSummaries.delete(documentId)

      const newCompletedSummaries = new Set(state.completedSummaries)
      newCompletedSummaries.add(documentId)

      return {
        activeSummaries: newActiveSummaries,
        completedSummaries: newCompletedSummaries
      }
    })
  },

  failSummary: (documentId: string, error: string) => {
    set((state) => {
      const newActiveSummaries = new Map(state.activeSummaries)
      newActiveSummaries.delete(documentId)

      const newFailedSummaries = new Map(state.failedSummaries)
      newFailedSummaries.set(documentId, error)

      return {
        activeSummaries: newActiveSummaries,
        failedSummaries: newFailedSummaries
      }
    })
  },

  clearSummary: (documentId: string) => {
    set((state) => {
      const newActiveSummaries = new Map(state.activeSummaries)
      newActiveSummaries.delete(documentId)

      const newCompletedSummaries = new Set(state.completedSummaries)
      newCompletedSummaries.delete(documentId)

      const newFailedSummaries = new Map(state.failedSummaries)
      newFailedSummaries.delete(documentId)

      return {
        activeSummaries: newActiveSummaries,
        completedSummaries: newCompletedSummaries,
        failedSummaries: newFailedSummaries
      }
    })
  },

  isGenerating: (documentId: string) => {
    return get().activeSummaries.has(documentId)
  },

  hasCompleted: (documentId: string) => {
    return get().completedSummaries.has(documentId)
  },

  getProgress: (documentId: string) => {
    return get().activeSummaries.get(documentId)
  },

  getError: (documentId: string) => {
    return get().failedSummaries.get(documentId)
  }
}))

