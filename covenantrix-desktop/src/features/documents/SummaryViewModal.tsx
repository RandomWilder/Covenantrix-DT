/**
 * SummaryViewModal Component
 * Displays document summary with markdown rendering and translation support
 */

import React, { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { X, Globe, Trash2, Clock, FileText, CheckCircle, Copy, Check } from 'lucide-react'
import { DocumentSummary } from '../../types/document'
import TranslationDialog from './TranslationDialog'
import ConfirmationModal from '../../components/ui/ConfirmationModal'
import { useClipboard } from '../../hooks/useClipboard'

interface SummaryViewModalProps {
  isOpen: boolean
  onClose: () => void
  summary: DocumentSummary
  onTranslate: (targetLanguage: string) => Promise<void>
  onDelete: () => Promise<void>
}

const SummaryViewModal: React.FC<SummaryViewModalProps> = ({
  isOpen,
  onClose,
  summary,
  onTranslate,
  onDelete
}) => {
  const [showTranslationDialog, setShowTranslationDialog] = useState(false)
  const [showDeleteConfirmation, setShowDeleteConfirmation] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)
  
  // Clipboard hook for copy functionality
  const { copied, copyToClipboard } = useClipboard()

  if (!isOpen) return null

  // Handle copy button click
  const handleCopy = () => {
    copyToClipboard(summary.summary_text)
  }

  const handleTranslate = async (targetLanguage: string) => {
    await onTranslate(targetLanguage)
    setShowTranslationDialog(false)
  }

  const handleDelete = async () => {
    setIsDeleting(true)
    try {
      await onDelete()
      setShowDeleteConfirmation(false)
      onClose()
    } catch (err) {
      console.error('Failed to delete summary:', err)
    } finally {
      setIsDeleting(false)
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 60) return `${diffMins} minute${diffMins !== 1 ? 's' : ''} ago`
    if (diffHours < 24) return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`
    if (diffDays < 7) return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`
    
    return date.toLocaleDateString()
  }

  const formatGenerationTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    if (mins > 0) {
      return `${mins}m ${secs}s`
    }
    return `${secs}s`
  }

  // Detect RTL languages (Hebrew, Arabic)
  const isRTL = ['he', 'ar', 'fa', 'ur'].includes(summary.language.toLowerCase())

  return (
    <>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        {/* Backdrop */}
        <div 
          className="absolute inset-0 bg-black bg-opacity-50"
          onClick={onClose}
        />

        {/* Modal */}
        <div className="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] flex flex-col">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
            <div className="flex-1 min-w-0">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2 truncate">
                Document Summary
              </h2>
              <h3 className="text-lg text-gray-600 dark:text-gray-400 truncate">
                {summary.document_name}
              </h3>
            </div>
            <button
              onClick={onClose}
              className="ml-4 p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors"
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          {/* Metadata Bar */}
          <div className="px-6 py-4 bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
            <div className="flex flex-wrap items-center gap-4 text-sm">
              <div className="flex items-center space-x-2 text-gray-600 dark:text-gray-400">
                <Globe className="w-4 h-4" />
                <span>Language: <span className="font-medium text-gray-900 dark:text-white">{summary.language.toUpperCase()}</span></span>
              </div>
              <div className="flex items-center space-x-2 text-gray-600 dark:text-gray-400">
                <Clock className="w-4 h-4" />
                <span>Generated {formatDate(summary.created_at)}</span>
              </div>
              <div className="flex items-center space-x-2 text-gray-600 dark:text-gray-400">
                <FileText className="w-4 h-4" />
                <span>{summary.total_chunks} chunks processed</span>
              </div>
              {summary.structure_detected && (
                <div className="flex items-center space-x-2 text-green-600 dark:text-green-400">
                  <CheckCircle className="w-4 h-4" />
                  <span>Structure detected</span>
                </div>
              )}
              <div className="flex items-center space-x-2 text-gray-600 dark:text-gray-400">
                <span>Generation time: {formatGenerationTime(summary.generation_time_seconds)}</span>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center space-x-3 mt-4">
              <button
                onClick={handleCopy}
                className="inline-flex items-center px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-50 dark:bg-gray-900/30 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800/50 transition-colors"
                title={copied ? 'Copied!' : 'Copy summary'}
              >
                {copied ? (
                  <>
                    <Check className="w-4 h-4 mr-2 text-green-500" />
                    Copied!
                  </>
                ) : (
                  <>
                    <Copy className="w-4 h-4 mr-2" />
                    Copy
                  </>
                )}
              </button>
              <button
                onClick={() => setShowTranslationDialog(true)}
                className="inline-flex items-center px-4 py-2 text-sm font-medium text-indigo-700 dark:text-indigo-300 bg-indigo-50 dark:bg-indigo-900/30 rounded-lg hover:bg-indigo-100 dark:hover:bg-indigo-900/50 transition-colors"
              >
                <Globe className="w-4 h-4 mr-2" />
                Translate
              </button>
              <button
                onClick={() => setShowDeleteConfirmation(true)}
                className="inline-flex items-center px-4 py-2 text-sm font-medium text-red-700 dark:text-red-300 bg-red-50 dark:bg-red-900/30 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/50 transition-colors"
              >
                <Trash2 className="w-4 h-4 mr-2" />
                Delete Summary
              </button>
            </div>
          </div>

          {/* Summary Content */}
          <div className="flex-1 overflow-auto p-6">
            <div 
              className={`prose prose-sm dark:prose-invert max-w-none select-text ${isRTL ? 'text-right' : ''}`}
              dir={isRTL ? 'rtl' : 'ltr'}
              style={{ userSelect: 'text' }}
            >
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {summary.summary_text}
              </ReactMarkdown>
            </div>
          </div>

          {/* Footer */}
          <div className="flex items-center justify-end p-6 border-t border-gray-200 dark:border-gray-700">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>

      {/* Translation Dialog */}
      <TranslationDialog
        isOpen={showTranslationDialog}
        onClose={() => setShowTranslationDialog(false)}
        onTranslate={handleTranslate}
        documentName={summary.document_name}
        currentLanguage={summary.language}
      />

      {/* Delete Confirmation */}
      <ConfirmationModal
        isOpen={showDeleteConfirmation}
        onClose={() => setShowDeleteConfirmation(false)}
        onConfirm={handleDelete}
        title="Delete Summary"
        message="Are you sure you want to delete this summary and all its translations? This action cannot be undone."
        confirmText="Delete Summary"
        cancelText="Cancel"
        isLoading={isDeleting}
        isDestructive={true}
      />
    </>
  )
}

export default SummaryViewModal

