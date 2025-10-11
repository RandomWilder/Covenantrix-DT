import React, { useState } from 'react'
import { useChat } from '../../contexts/ChatContext'
import { useDocuments } from '../../hooks/useDocuments'
import { FileText, Eye, Search } from '../../components/icons'

interface ContextPanelProps {
  width: number
  collapsed: boolean
}

export const ContextPanel: React.FC<ContextPanelProps> = ({ width, collapsed }) => {
  const { activeConversation, selectedDocuments, setSelectedDocuments } = useChat()
  const { documents } = useDocuments()
  const [searchQuery, setSearchQuery] = useState('')

  // Get unique sources from the current conversation
  const getUniqueSources = () => {
    if (!activeConversation) return []
    
    const sources = activeConversation.messages
      .filter(msg => msg.role === 'assistant')
      .flatMap(msg => msg.sources)
    
    // Remove duplicates based on source document_id
    const uniqueSources = sources.filter((source, index, self) => 
      index === self.findIndex(s => s.document_id === source.document_id)
    )
    
    return uniqueSources
  }

  const sources = getUniqueSources()
  const filteredDocuments = documents.filter(doc =>
    doc.filename.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const handleDocumentSelect = (documentId: string) => {
    const isSelected = selectedDocuments.includes(documentId)
    if (isSelected) {
      setSelectedDocuments(selectedDocuments.filter(id => id !== documentId))
    } else {
      setSelectedDocuments([...selectedDocuments, documentId])
    }
  }

  const handleClearContext = () => {
    setSelectedDocuments([])
  }

  if (collapsed) {
    return null
  }

  return (
    <div 
      className="bg-gray-50 dark:bg-gray-800 border-l border-gray-200 dark:border-gray-700 h-full flex flex-col"
      style={{ width: `${width}%` }}
    >
      {/* Header */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-medium text-gray-700 dark:text-gray-300">Context</h2>
          {sources.length > 0 && (
            <button
              onClick={handleClearContext}
              className="text-xs text-gray-500 dark:text-gray-400 hover:text-red-600 transition-colors"
              title="Clear context"
            >
              Clear
            </button>
          )}
        </div>
        
        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400 dark:text-gray-500" />
          <input
            type="text"
            placeholder="Search documents..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-2 text-sm border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {/* Active Sources */}
        {sources.length > 0 && (
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <h3 className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-3">Cited Sources</h3>
            <div className="space-y-2">
              {sources.map((source, index) => (
                <div
                  key={index}
                  className="p-2 bg-blue-50 dark:bg-blue-900 border border-blue-200 dark:border-blue-600 rounded-md"
                >
                  <div className="flex items-start gap-2">
                    <FileText className="w-4 h-4 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-blue-900 dark:text-blue-100 truncate">
                        {source.document_name}
                      </div>
                      {source.page_number && (
                        <div className="text-xs text-blue-600 dark:text-blue-300 mt-1">
                          Page {source.page_number}
                        </div>
                      )}
                      {source.excerpt && (
                        <div className="text-xs text-blue-700 dark:text-blue-200 mt-1 line-clamp-2">
                          {source.excerpt}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Available Documents */}
        <div className="p-4">
          <h3 className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-3">Available Documents</h3>
          
          {filteredDocuments.length === 0 ? (
            <div className="text-center text-gray-500 dark:text-gray-400 py-4">
              {searchQuery ? 'No documents found' : 'No documents available'}
            </div>
          ) : (
            <div className="space-y-2">
              {filteredDocuments.map((document) => (
                <div
                  key={document.document_id}
                  className={`p-3 rounded-md border cursor-pointer transition-colors ${
                    selectedDocuments.includes(document.document_id)
                      ? 'bg-blue-50 dark:bg-blue-900 border-blue-200 dark:border-blue-600'
                      : 'bg-white dark:bg-gray-700 border-gray-200 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-600'
                  }`}
                  onClick={() => handleDocumentSelect(document.document_id)}
                >
                  <div className="flex items-start gap-3">
                    <FileText className="w-4 h-4 text-gray-400 dark:text-gray-500 mt-0.5 flex-shrink-0" />
                    
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-gray-900 dark:text-white truncate">
                        {document.filename}
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        {document.document_type?.toUpperCase()} • {document.file_size_mb ? `${document.file_size_mb.toFixed(1)} MB` : 'Unknown size'}
                      </div>
                      {document.uploaded_at && (
                        <div className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                          {new Date(document.uploaded_at).toLocaleDateString()}
                        </div>
                      )}
                    </div>
                    
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        // This would open document preview
                        console.log('Preview document:', document.document_id)
                      }}
                      className="p-1 text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                      title="Preview document"
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      {selectedDocuments.length > 0 && (
        <div className="p-4 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-700">
          <div className="text-xs text-gray-600 dark:text-gray-300">
            <div className="font-medium mb-1">Selected Documents ({selectedDocuments.length})</div>
            <div className="space-y-1">
              {selectedDocuments.map(docId => {
                const doc = documents.find(d => d.document_id === docId)
                return doc ? (
                  <div key={docId} className="truncate text-gray-500 dark:text-gray-400">
                    {doc.filename}
                  </div>
                ) : null
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
