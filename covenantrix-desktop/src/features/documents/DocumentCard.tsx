/**
 * DocumentCard Component
 * Displays document information with entity summary
 */

import React, { useState, useEffect } from 'react'
import { DocumentInfo, DocumentEntitiesResponse } from '../../types/document'
import { DocumentsApi } from '../../services/api/DocumentsApi'
import EntitySummary from './EntitySummary'

interface DocumentCardProps {
  document: DocumentInfo
  onDelete?: (documentId: string) => void
  className?: string
}

const DocumentCard: React.FC<DocumentCardProps> = ({ 
  document, 
  onDelete, 
  className = '' 
}) => {
  const [entities, setEntities] = useState<DocumentEntitiesResponse | null>(null)
  const [loadingEntities, setLoadingEntities] = useState(false)
  const [showEntities, setShowEntities] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const documentsApi = new DocumentsApi()

  useEffect(() => {
    console.log(`DocumentCard mounted for: ${document.document_id} (${document.filename})`)
  }, [document.document_id])

  const loadEntities = async () => {
    // Only prevent loading if THIS specific document already has entities loaded
    if (entities || loadingEntities) return

    setLoadingEntities(true)
    setError(null)

    try {
      console.log(`Loading entities for document: ${document.document_id} (${document.filename})`)
      const entityData = await documentsApi.getDocumentEntities(document.document_id)
      console.log(`Loaded entities for ${document.document_id}:`, entityData)
      setEntities(entityData)
    } catch (err) {
      console.error(`Failed to load entities for ${document.document_id}:`, err)
      setError(err instanceof Error ? err.message : 'Failed to load entities')
    } finally {
      setLoadingEntities(false)
    }
  }

  const toggleEntities = () => {
    if (!showEntities && !entities) {
      loadEntities()
    }
    setShowEntities(!showEntities)
  }

  const formatFileSize = (sizeInMB: number): string => {
    if (sizeInMB < 1) {
      return `${(sizeInMB * 1024).toFixed(0)} KB`
    }
    return `${sizeInMB.toFixed(1)} MB`
  }

  const formatDate = (dateString: string | null): string => {
    if (!dateString) return 'Not processed'
    return new Date(dateString).toLocaleDateString()
  }


  const getDocumentTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      contract: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
      lease_agreement: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
      employment: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
      legal: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
      financial: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
      technical: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-200',
      general: 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200'
    }
    return colors[type] || colors.general
  }

  return (
    <div className={`bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm hover:shadow-md transition-shadow ${className}`}>
      {/* Document Header */}
      <div className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 truncate">
              {document.filename}
            </h3>
            {/* One-line document details */}
            <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500 dark:text-gray-400">
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${getDocumentTypeColor(document.document_type || 'general')}`}>
                {(document.document_type || 'Document').replace('_', ' ')}
              </span>
              <span>{formatFileSize(document.file_size_mb)}</span>
              <span>{document.char_count.toLocaleString()} chars</span>
              <span>{document.chunk_count} chunks</span>
              <span>Processed: {formatDate(document.processed_at)}</span>
              <span>OCR: {(document.ocr_used || document.ocr_applied) ? 'Yes' : 'No'}</span>
            </div>
            
            {/* Risk Level and Key Insights - only show if present */}
            {(document.risk_level || (document.key_insights && document.key_insights.length > 0)) && (
              <div className="flex items-center space-x-4 mt-2">
                {document.risk_level && (
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    document.risk_level === 'high' ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200' :
                    document.risk_level === 'medium' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200' :
                    'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                  }`}>
                    Risk: {document.risk_level.toUpperCase()}
                  </span>
                )}
                {document.key_insights && document.key_insights.length > 0 && (
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    {document.key_insights.length} insight{document.key_insights.length !== 1 ? 's' : ''}
                  </span>
                )}
              </div>
            )}
          </div>
          
          {onDelete && (
            <button
              onClick={() => onDelete(document.document_id)}
              className="ml-2 p-1 text-gray-400 hover:text-red-500 transition-colors"
              title="Delete document"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* Entity Summary Section */}
      <div className="border-t border-gray-200 dark:border-gray-700">
        <button
          onClick={toggleEntities}
          className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
        >
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-indigo-500">
              <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="text-left">
              <h4 className="font-medium text-gray-900 dark:text-gray-100">Document Entities</h4>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {loadingEntities ? 'Loading...' : 
                 entities ? 'View extracted entities' : 
                 'Extract entities from document'}
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            {entities && (
              <span className="px-2 py-1 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-200">
                {entities.entity_summary.people.length + 
                 entities.entity_summary.organizations.length + 
                 entities.entity_summary.locations.length + 
                 entities.entity_summary.financial.length + 
                 entities.entity_summary.dates_and_terms.length}
              </span>
            )}
            <svg
              className={`w-5 h-5 text-gray-400 transition-transform ${showEntities ? 'rotate-180' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </div>
        </button>

        {showEntities && (
          <div className="px-4 pb-4">
            {loadingEntities ? (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500"></div>
                <span className="ml-3 text-gray-500 dark:text-gray-400">Loading entities...</span>
              </div>
            ) : error ? (
              <div className="text-center py-8">
                <div className="text-red-500 mb-2">
                  <svg className="w-8 h-8 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <p className="text-red-600 dark:text-red-400 text-sm">{error}</p>
                <button
                  onClick={loadEntities}
                  className="mt-2 text-indigo-600 hover:text-indigo-500 text-sm font-medium"
                >
                  Try again
                </button>
              </div>
            ) : entities ? (
              <div>
                <p className="text-xs text-gray-400 mb-2">Entities for: {document.document_id}</p>
                <EntitySummary entitySummary={entities.entity_summary} />
              </div>
            ) : (
              <div className="text-center py-8">
                <p className="text-gray-500 dark:text-gray-400 mb-2">No entities loaded</p>
                <button
                  onClick={loadEntities}
                  className="text-indigo-600 hover:text-indigo-500 text-sm font-medium"
                >
                  Load entities
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default DocumentCard
