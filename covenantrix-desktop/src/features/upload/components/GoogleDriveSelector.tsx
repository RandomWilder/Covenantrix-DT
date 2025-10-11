import React, { useState, useEffect } from 'react'
import { Cloud, FolderOpen, FileText, Image, File, RefreshCw } from 'lucide-react'
import { useToast } from '../../../hooks/useToast'

interface GoogleDriveFile {
  file_id: string
  name: string
  mime_type: string
  size?: number
  modified_time?: string
  web_view_link?: string
}

interface GoogleDriveSelectorProps {
  onFilesSelected: (fileIds: string[]) => void
  disabled?: boolean
}

const GoogleDriveSelector: React.FC<GoogleDriveSelectorProps> = ({
  onFilesSelected,
  disabled = false
}) => {
  const [files, setFiles] = useState<GoogleDriveFile[]>([])
  const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set())
  const [isLoading, setIsLoading] = useState(false)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const { showToast } = useToast()

  useEffect(() => {
    checkAuthentication()
  }, [])

  const checkAuthentication = async () => {
    try {
      // Check if user is authenticated with Google
      const response = await fetch('http://localhost:8000/auth/google/status')
      if (response.ok) {
        setIsAuthenticated(true)
        loadFiles()
      }
    } catch (error) {
      console.error('Authentication check failed:', error)
    }
  }

  const loadFiles = async () => {
    setIsLoading(true)
    try {
      const response = await fetch('http://localhost:8000/documents/drive/files')
      if (response.ok) {
        const data = await response.json()
        setFiles(data.files || [])
      } else {
        showToast('Failed to load Google Drive files', 'error')
      }
    } catch (error) {
      console.error('Failed to load files:', error)
      showToast('Failed to load Google Drive files', 'error')
    } finally {
      setIsLoading(false)
    }
  }

  const handleAuthenticate = async () => {
    try {
      // Open Google OAuth flow
      const response = await fetch('http://localhost:8000/auth/google/authorize', {
        method: 'POST'
      })
      
      if (response.ok) {
        const { authUrl } = await response.json()
        // Open OAuth URL in new window
        window.open(authUrl, 'google-auth', 'width=500,height=600')
        
        // Listen for authentication completion
        const checkAuth = setInterval(async () => {
          try {
            const statusResponse = await fetch('http://localhost:8000/auth/google/status')
            if (statusResponse.ok) {
              clearInterval(checkAuth)
              setIsAuthenticated(true)
              loadFiles()
            }
          } catch (error) {
            // Continue checking
          }
        }, 1000)
      }
    } catch (error) {
      console.error('Authentication failed:', error)
      showToast('Google authentication failed', 'error')
    }
  }

  const handleFileSelect = (fileId: string) => {
    const newSelected = new Set(selectedFiles)
    if (newSelected.has(fileId)) {
      newSelected.delete(fileId)
    } else {
      newSelected.add(fileId)
    }
    setSelectedFiles(newSelected)
  }

  const handleSelectAll = () => {
    if (selectedFiles.size === files.length) {
      setSelectedFiles(new Set())
    } else {
      setSelectedFiles(new Set(files.map(f => f.file_id)))
    }
  }

  const handleConfirmSelection = () => {
    onFilesSelected(Array.from(selectedFiles))
  }

  const getFileIcon = (mimeType: string) => {
    if (mimeType.includes('pdf')) {
      return <FileText className="w-5 h-5 text-red-500" />
    } else if (mimeType.startsWith('image/')) {
      return <Image className="w-5 h-5 text-blue-500" />
    } else if (mimeType.includes('word') || mimeType.includes('document')) {
      return <FileText className="w-5 h-5 text-blue-600" />
    } else {
      return <File className="w-5 h-5 text-gray-500" />
    }
  }

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return 'Unknown size'
    const mb = bytes / (1024 * 1024)
    return `${mb.toFixed(1)} MB`
  }

  if (!isAuthenticated) {
    return (
      <div className="text-center py-12">
        <div className="p-4 bg-gray-100 dark:bg-gray-800 rounded-full w-16 h-16 mx-auto mb-4 flex items-center justify-center">
          <Cloud className="w-8 h-8 text-gray-600 dark:text-gray-400" />
        </div>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
          Connect to Google Drive
        </h3>
        <p className="text-gray-600 dark:text-gray-400 mb-6">
          Authenticate with Google to access your Drive files
        </p>
        <button
          onClick={handleAuthenticate}
          disabled={disabled}
          className="px-6 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50"
        >
          Connect Google Drive
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Select Files from Google Drive
          </h3>
          <p className="text-gray-600 dark:text-gray-400 text-sm">
            Choose files to download and process
          </p>
        </div>
        <button
          onClick={loadFiles}
          disabled={isLoading || disabled}
          className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-5 h-5 ${isLoading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* File List */}
      {isLoading ? (
        <div className="text-center py-8">
          <RefreshCw className="w-8 h-8 text-gray-400 animate-spin mx-auto mb-2" />
          <p className="text-gray-600 dark:text-gray-400">Loading files...</p>
        </div>
      ) : files.length === 0 ? (
        <div className="text-center py-8">
          <FolderOpen className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400">No supported files found in Google Drive</p>
        </div>
      ) : (
        <div className="space-y-2">
          {/* Select All */}
          <div className="flex items-center space-x-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <input
              type="checkbox"
              checked={selectedFiles.size === files.length && files.length > 0}
              onChange={handleSelectAll}
              disabled={disabled}
              className="w-4 h-4 text-primary rounded border-gray-300 dark:border-gray-600"
            />
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Select All ({files.length} files)
            </span>
          </div>

          {/* Files */}
          <div className="max-h-96 overflow-y-auto space-y-1">
            {files.map((file) => (
              <div
                key={file.file_id}
                className={`flex items-center space-x-3 p-3 rounded-lg border transition-colors ${
                  selectedFiles.has(file.file_id)
                    ? 'bg-primary/10 border-primary'
                    : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700'
                }`}
              >
                <input
                  type="checkbox"
                  checked={selectedFiles.has(file.file_id)}
                  onChange={() => handleFileSelect(file.file_id)}
                  disabled={disabled}
                  className="w-4 h-4 text-primary rounded border-gray-300 dark:border-gray-600"
                />
                {getFileIcon(file.mime_type)}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                    {file.name}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {formatFileSize(file.size)} • {file.mime_type}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Action Buttons */}
      {selectedFiles.size > 0 && (
        <div className="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-700">
          <span className="text-sm text-gray-600 dark:text-gray-400">
            {selectedFiles.size} file{selectedFiles.size !== 1 ? 's' : ''} selected
          </span>
          <button
            onClick={handleConfirmSelection}
            disabled={disabled}
            className="px-6 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50"
          >
            Download & Process
          </button>
        </div>
      )}
    </div>
  )
}

export default GoogleDriveSelector
