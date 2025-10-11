import React, { useState } from 'react'
import { Upload, Cloud } from 'lucide-react'
import FileUploadArea from './components/FileUploadArea'
import GoogleDriveSelector from './components/GoogleDriveSelector'
import UploadProgress from './components/UploadProgress'
import FileList from './components/FileList'
import { useUpload } from '../../hooks/useUpload'

const UploadScreen: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'local' | 'drive'>('local')
  const {
    files,
    uploadProgress,
    isUploading,
    addFiles,
    removeFile,
    startUpload,
    clearFiles
  } = useUpload()

  const handleFilesSelected = (selectedFiles: File[]) => {
    addFiles(selectedFiles)
  }

  const handleGoogleDriveFiles = (fileIds: string[]) => {
    // This will be handled by the GoogleDriveSelector component
    console.log('Google Drive files selected:', fileIds)
  }

  const handleStartUpload = async () => {
    if (activeTab === 'local') {
      await startUpload('local')
    } else {
      await startUpload('drive')
    }
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
        {activeTab === 'local' ? (
          <div className="space-y-6">
            <FileUploadArea
              onFilesSelected={handleFilesSelected}
              disabled={isUploading}
            />
            
            {files.length > 0 && !isUploading && (
              <FileList
                files={files}
                onRemoveFile={removeFile}
                disabled={isUploading}
              />
            )}
          </div>
        ) : (
          <GoogleDriveSelector
            onFilesSelected={handleGoogleDriveFiles}
            disabled={isUploading}
          />
        )}
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
