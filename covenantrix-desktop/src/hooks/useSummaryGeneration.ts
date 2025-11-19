/**
 * useSummaryGeneration Hook
 * Handles background summary generation with progress tracking
 */

import { useState, useCallback, useEffect } from 'react'
import { useSummaryStore } from '../stores/summaryStore'
import { DocumentsApi } from '../services/api/DocumentsApi'
import { DocumentSummary } from '../types/document'

export const useSummaryGeneration = (documentId: string) => {
  const store = useSummaryStore()
  const [error, setError] = useState<string | null>(null)
  const [summary, setSummary] = useState<DocumentSummary | null>(null)
  const [loading, setLoading] = useState(false)
  
  const documentsApi = new DocumentsApi()

  // Check if summary exists on mount
  useEffect(() => {
    checkExistingSummary()
  }, [documentId])

  const checkExistingSummary = async () => {
    try {
      const existingSummary = await documentsApi.getSummary(documentId)
      setSummary(existingSummary)
      store.completeSummary(documentId)
    } catch (err) {
      // Summary doesn't exist yet - that's fine
      console.log(`No existing summary for ${documentId}`)
    }
  }

  const startGeneration = useCallback(async () => {
    setError(null)
    setLoading(true)
    store.startSummary(documentId)

    try {
      const generatedSummary = await documentsApi.generateSummaryStream(
        documentId,
        (update) => {
          store.updateProgress(documentId, update)
        }
      )

      setSummary(generatedSummary)
      store.completeSummary(documentId)
      setLoading(false)
      
      return generatedSummary
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to generate summary'
      setError(errorMessage)
      store.failSummary(documentId, errorMessage)
      setLoading(false)
      throw err
    }
  }, [documentId])

  const deleteSummary = useCallback(async () => {
    try {
      await documentsApi.deleteSummary(documentId)
      setSummary(null)
      store.clearSummary(documentId)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete summary'
      setError(errorMessage)
      throw err
    }
  }, [documentId])

  const translateSummary = useCallback(async (targetLanguage: string) => {
    setError(null)
    setLoading(true)

    try {
      const translatedSummary = await documentsApi.translateSummary(documentId, targetLanguage)
      setSummary(translatedSummary)
      setLoading(false)
      
      return translatedSummary
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to translate summary'
      setError(errorMessage)
      setLoading(false)
      throw err
    }
  }, [documentId])

  return {
    // State
    summary,
    isGenerating: store.isGenerating(documentId),
    hasCompleted: store.hasCompleted(documentId) || summary !== null,
    progress: store.getProgress(documentId),
    error: error || store.getError(documentId),
    loading,

    // Actions
    startGeneration,
    deleteSummary,
    translateSummary,
    checkExistingSummary
  }
}

