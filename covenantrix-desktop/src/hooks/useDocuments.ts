import { useState, useEffect } from 'react'
import { DocumentsApi } from '../services/api/DocumentsApi'
import { DocumentInfo } from '../types/document'

export const useDocuments = () => {
  const [documents, setDocuments] = useState<DocumentInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadDocuments = async () => {
    setLoading(true)
    setError(null)

    try {
      const documentsApi = new DocumentsApi()
      const response = await documentsApi.getDocuments()
      setDocuments(response.documents)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load documents')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadDocuments()
  }, [])

  return {
    documents,
    loading,
    error,
    refetch: loadDocuments
  }
}
