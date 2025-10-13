import React, { useState } from 'react'
import { Upload, Cloud } from 'lucide-react'
import FileUploadArea from './components/FileUploadArea'
import GoogleDriveSelector from './components/GoogleDriveSelector'
import UploadProgress from './components/UploadProgress'
import FileList from './components/FileList'
import { useUpload } from '../../hooks/useUpload'
import { useServiceStatus } from '../../hooks/useServiceStatus'

const UploadScreen: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'local' | 'drive'>('local')
  const { features, isLoading } = useServiceStatus()
  const uploadAvailable = features.upload
  const {
    files,
    uploadProgress,
    isUploading,
    addFiles,
    addDriveFiles,
    removeFile,
    startUpload,
    clearFiles
  } = useUpload()

  const handleFilesSelected = (selectedFiles: File[]) => {
    addFiles(selectedFiles)
  }

  const handleAddDriveFiles = (files: Array<{id: string; name: string}>, accountId: string, accountEmail: string) => {
    addDriveFiles(files, accountId, accountEmail)
  }

  const handleStartUpload = async () => {
    await startUpload()
  }

  const handleGoToSettings = () => {
    // TODO: Implement navigation to settings modal
    console.log('Navigate to settings')
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-6 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              Upload Documents
            </h1>
            <p className="text-gray-600 dark:text-gray-400 mt-1">
              Upload documents from your computer or Google Drive
            </p>
          </div>
        </div>
      </div>

      {/* Upload Feature Guard Banner */}
      {!isLoading && !uploadAvailable && (
        <div className="bg-yellow-50 dark:bg-yellow-900/20 border-b border-yellow-200 dark:border-yellow-800 px-6 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <svg className="w-5 h-5 text-yellow-600 dark:text-yellow-500" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              <div>
                <p className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
                  ⚠️ Upload Disabled
                </p>
                <p className="text-xs text-yellow-700 dark:text-yellow-300 mt-0.5">
                  OpenAI API key not configured. Configure your API key in Settings → API Keys to enable upload.
                </p>
              </div>
            </div>
            <button
              onClick={handleGoToSettings}
              className="px-3 py-1.5 text-sm font-medium text-yellow-800 dark:text-yellow-200 bg-yellow-100 dark:bg-yellow-800/30 hover:bg-yellow-200 dark:hover:bg-yellow-700/30 rounded transition-colors"
            >
              Go to Settings
            </button>
          </div>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex space-x-1 bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
          <button
            onClick={() => setActiveTab('local')}
            className={`flex-1 flex items-center justify-center space-x-2 px-4 py-2 rounded-md transition-colors ${
              activeTab === 'local'
                ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
            }`}
          >
            <Upload className="w-4 h-4" />
            <span>Local Files</span>
          </button>
          <button
            onClick={() => setActiveTab('drive')}
            className={`flex-1 flex items-center justify-center space-x-2 px-4 py-2 rounded-md transition-colors ${
              activeTab === 'drive'
                ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
            }`}
          >
            <Cloud className="w-4 h-4" />
            <span>Google Drive</span>
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 p-6">
        <div className="space-y-6">
          {activeTab === 'local' ? (
            <FileUploadArea
              onFilesSelected={handleFilesSelected}
              disabled={isUploading || !uploadAvailable}
            />
          ) : (
            <GoogleDriveSelector
              onAddToQueue={handleAddDriveFiles}
              disabled={isUploading || !uploadAvailable}
            />
          )}
          
          {/* Unified FileList - shows all files regardless of source */}
          {files.length > 0 && !isUploading && (
            <FileList
              files={files}
              onRemoveFile={removeFile}
              disabled={isUploading || !uploadAvailable}
            />
          )}
        </div>
      </div>

      {/* Upload Progress */}
      {(isUploading || files.some(f => f.status === 'uploading' || f.status === 'processing')) && (
        <div className="p-6 border-t border-gray-200 dark:border-gray-700">
          <UploadProgress progress={{...uploadProgress, files: files}} />
        </div>
      )}

      {/* Action Buttons */}
      {files.length > 0 && !isUploading && !files.some(f => f.status === 'uploading' || f.status === 'processing') && (
        <div className="p-6 border-t border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-600 dark:text-gray-400">
              {files.length} file{files.length !== 1 ? 's' : ''} selected
            </div>
            <div className="flex space-x-3">
              <button
                onClick={clearFiles}
                className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors"
              >
                Clear All
              </button>
              <button
                onClick={handleStartUpload}
                className="px-6 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
              >
                Start Upload
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default UploadScreen
