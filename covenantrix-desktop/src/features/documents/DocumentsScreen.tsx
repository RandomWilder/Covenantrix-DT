/**
 * DocumentsScreen Component
 * Displays the list of uploaded documents with entity extraction
 */

import React, { useState, useEffect } from 'react'
import { FileText, Search, Filter, RefreshCw, Trash2 } from 'lucide-react'
import { DocumentInfo } from '../../types/document'
import { DocumentsApi } from '../../services/api/DocumentsApi'
import DocumentCard from './DocumentCard'
import ConfirmationModal from '../../components/ui/ConfirmationModal'

const DocumentsScreen: React.FC = () => {
  const [documents, setDocuments] = useState<DocumentInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [filterType, setFilterType] = useState<string>('all')
  const [showResetModal, setShowResetModal] = useState(false)
  const [isResetting, setIsResetting] = useState(false)

  const documentsApi = new DocumentsApi()

  const loadDocuments = async () => {
    setLoading(true)
    setError(null)

    try {
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

  const handleDeleteDocument = async (documentId: string) => {
    try {
      await documentsApi.deleteDocument(documentId)
      setDocuments(documents.filter(doc => doc.document_id !== documentId))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete document')
    }
  }

  const handleResetStorage = async () => {
    setIsResetting(true)
    setError(null)

    try {
      const response = await documentsApi.resetStorage()
      if (response.success) {
        // Refresh the document list to show empty state
        await loadDocuments()
        setShowResetModal(false)
        // You could add a toast notification here if you have a toast system
        console.log('Storage reset successfully:', response.message)
      } else {
        setError(response.error || 'Failed to reset storage')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reset storage')
    } finally {
      setIsResetting(false)
    }
  }

  const filteredDocuments = documents.filter(doc => {
    const matchesSearch = doc.filename.toLowerCase().includes(searchTerm.toLowerCase())
    // Note: document_type might not be available in API response, so we'll filter by status for now
    const matchesFilter = filterType === 'all' || doc.status === filterType
    return matchesSearch && matchesFilter
  })

  const documentTypes = Array.from(new Set(documents.map(doc => doc.status)))

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Loading documents...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-500 mb-4">
            <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">Error Loading Documents</h3>
          <p className="text-gray-600 dark:text-gray-400 mb-4">{error}</p>
          <button
            onClick={loadDocuments}
            className="inline-flex items-center px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Try Again
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-6 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              Documents
            </h1>
            <p className="text-gray-600 dark:text-gray-400 mt-1">
              {documents.length} document{documents.length !== 1 ? 's' : ''} uploaded
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={loadDocuments}
              className="inline-flex items-center px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh
            </button>
            <button
              onClick={() => setShowResetModal(true)}
              className="inline-flex items-center px-3 py-2 text-sm font-medium text-red-700 dark:text-red-300 bg-white dark:bg-gray-800 border border-red-300 dark:border-red-600 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
              title="Reset all documents"
            >
              <Trash2 className="w-4 h-4 mr-2" />
              Reset
            </button>
          </div>
        </div>
      </div>

      {/* Search and Filter */}
      <div className="p-6 border-b border-gray-200 dark:border-gray-700">
        <div className="flex flex-col sm:flex-row gap-4">
          {/* Search */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search documents..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
          </div>

          {/* Filter */}
          <div className="flex items-center space-x-2">
            <Filter className="w-4 h-4 text-gray-400" />
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            >
              <option value="all">All Types</option>
              {documentTypes.map(type => (
                <option key={type} value={type}>
                  {type?.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()) || 'Unknown'}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Documents Grid */}
      <div className="flex-1 p-6 overflow-auto">
        {filteredDocuments.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                {documents.length === 0 ? 'No Documents' : 'No Matching Documents'}
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                {documents.length === 0 
                  ? 'Upload your first document to get started'
                  : 'Try adjusting your search or filter criteria'
                }
              </p>
              {documents.length === 0 && (
                <button
                  onClick={() => window.location.hash = '#upload'}
                  className="inline-flex items-center px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
                >
                  Upload Document
                </button>
              )}
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredDocuments.map((document) => (
              <DocumentCard
                key={document.document_id}
                document={document}
                onDelete={handleDeleteDocument}
              />
            ))}
          </div>
        )}
      </div>

      {/* Reset Confirmation Modal */}
      <ConfirmationModal
        isOpen={showResetModal}
        onClose={() => setShowResetModal(false)}
        onConfirm={handleResetStorage}
        title="Reset Document Storage"
        message="This will permanently delete all documents and their processing data. This action cannot be undone. Are you sure you want to continue?"
        confirmText="Reset All Documents"
        cancelText="Cancel"
        isLoading={isResetting}
        isDestructive={true}
      />
    </div>
  )
}

export default DocumentsScreen
