/**
 * TranslationDialog Component
 * Dialog for translating summaries with natural language input
 */

import React, { useState } from 'react'
import { X, Globe, Loader2 } from 'lucide-react'

interface TranslationDialogProps {
  isOpen: boolean
  onClose: () => void
  onTranslate: (targetLanguage: string) => Promise<void>
  documentName: string
  currentLanguage: string
}

const TranslationDialog: React.FC<TranslationDialogProps> = ({
  isOpen,
  onClose,
  onTranslate,
  documentName,
  currentLanguage
}) => {
  const [targetLanguage, setTargetLanguage] = useState('')
  const [isTranslating, setIsTranslating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (!isOpen) return null

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!targetLanguage.trim()) {
      setError('Please enter a language')
      return
    }

    setError(null)
    setIsTranslating(true)

    try {
      await onTranslate(targetLanguage.trim())
      onClose()
      setTargetLanguage('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Translation failed')
    } finally {
      setIsTranslating(false)
    }
  }

  const handleClose = () => {
    if (!isTranslating) {
      setTargetLanguage('')
      setError(null)
      onClose()
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black bg-opacity-50"
        onClick={handleClose}
      />

      {/* Dialog */}
      <div className="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-indigo-100 dark:bg-indigo-900 rounded-lg">
              <Globe className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
            </div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Translate Summary
            </h2>
          </div>
          <button
            onClick={handleClose}
            disabled={isTranslating}
            className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors disabled:opacity-50"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Document Info */}
        <div className="mb-4 p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
          <p className="text-sm text-gray-600 dark:text-gray-400">Document</p>
          <p className="text-gray-900 dark:text-white font-medium truncate">
            {documentName}
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
            Current language: {currentLanguage}
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Language Input */}
          <div>
            <label 
              htmlFor="target-language" 
              className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
            >
              What language would you like to translate to?
            </label>
            <input
              id="target-language"
              type="text"
              value={targetLanguage}
              onChange={(e) => setTargetLanguage(e.target.value)}
              placeholder="e.g., English, עברית, Español, 中文"
              disabled={isTranslating}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-indigo-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
              autoFocus
            />
            <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
              Type in any language - we'll automatically detect what you mean
            </p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
              <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center justify-end space-x-3 pt-2">
            <button
              type="button"
              onClick={handleClose}
              disabled={isTranslating}
              className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isTranslating || !targetLanguage.trim()}
              className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center"
            >
              {isTranslating ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Translating...
                </>
              ) : (
                'Translate'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default TranslationDialog

