import React from 'react'
import { X, FileText, Image, File, CheckCircle, XCircle, Computer, Cloud } from 'lucide-react'

interface FileItem {
  id: string
  file: File
  status?: 'pending' | 'uploading' | 'processing' | 'completed' | 'failed'
  progress?: number
  error?: string
  source?: 'local' | 'drive'
  sourceAccount?: string  // Email for display
  driveAccountId?: string // Account ID for API calls (not displayed)
}

interface FileListProps {
  files: FileItem[]
  onRemoveFile: (id: string) => void
  disabled?: boolean
}

const FileList: React.FC<FileListProps> = ({
  files,
  onRemoveFile,
  disabled = false
}) => {
  const getFileIcon = (file: File) => {
    const type = file.type
    if (type.startsWith('image/')) {
      return <Image className="w-5 h-5 text-blue-500" />
    } else if (type.includes('pdf')) {
      return <FileText className="w-5 h-5 text-red-500" />
    } else if (type.includes('word') || type.includes('document')) {
      return <FileText className="w-5 h-5 text-blue-600" />
    } else {
      return <File className="w-5 h-5 text-gray-500" />
    }
  }

  const getStatusIcon = (status?: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-500" />
      default:
        return null
    }
  }

  const getStatusText = (status?: string) => {
    switch (status) {
      case 'pending':
        return 'Ready to upload'
      case 'uploading':
        return 'Uploading...'
      case 'processing':
        return 'Processing...'
      case 'completed':
        return 'Completed'
      case 'failed':
        return 'Failed'
      default:
        return 'Ready'
    }
  }

  const getStatusColor = (status?: string) => {
    switch (status) {
      case 'completed':
        return 'text-green-600 dark:text-green-400'
      case 'failed':
        return 'text-red-600 dark:text-red-400'
      case 'uploading':
      case 'processing':
        return 'text-blue-600 dark:text-blue-400'
      default:
        return 'text-gray-600 dark:text-gray-400'
    }
  }

  const formatFileSize = (bytes: number) => {
    const mb = bytes / (1024 * 1024)
    return `${mb.toFixed(1)} MB`
  }

  if (files.length === 0) {
    return null
  }

  return (
    <div className="space-y-2">
      <h3 className="text-sm font-medium text-gray-900 dark:text-white">
        Selected Files ({files.length})
      </h3>
      
      <div className="space-y-2">
        {files.map((fileItem) => (
          <div
            key={fileItem.id}
            className="flex items-center space-x-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700"
          >
            {getFileIcon(fileItem.file)}
            
            <div className="flex-1 min-w-0">
              <div className="flex items-center space-x-2">
                {/* Source indicator */}
                <span title={fileItem.source === 'drive' ? 'Google Drive' : 'Local file'}>
                  {fileItem.source === 'drive' ? (
                    <Cloud className="w-4 h-4 text-blue-500 flex-shrink-0" />
                  ) : (
                    <Computer className="w-4 h-4 text-gray-500 flex-shrink-0" />
                  )}
                </span>
                <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                  {fileItem.file.name}
                </p>
              </div>
              <div className="flex items-center space-x-2 mt-1">
                {fileItem.file.size > 0 && (
                  <>
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      {formatFileSize(fileItem.file.size)}
                    </span>
                    <span className="text-xs text-gray-400">•</span>
                  </>
                )}
                {fileItem.source === 'drive' && fileItem.sourceAccount && (
                  <>
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      Drive - {fileItem.sourceAccount}
                    </span>
                    <span className="text-xs text-gray-400">•</span>
                  </>
                )}
                <span className={`text-xs ${getStatusColor(fileItem.status)}`}>
                  {getStatusText(fileItem.status)}
                </span>
                {fileItem.progress !== undefined && fileItem.status === 'uploading' && (
                  <>
                    <span className="text-xs text-gray-400">•</span>
                    <span className="text-xs text-gray-500">
                      {Math.round(fileItem.progress)}%
                    </span>
                  </>
                )}
              </div>
              
              {fileItem.error && (
                <p className="text-xs text-red-600 dark:text-red-400 mt-1">
                  {fileItem.error}
                </p>
              )}
              
              {fileItem.status === 'uploading' && fileItem.progress !== undefined && (
                <div className="mt-2">
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1">
                    <div
                      className="bg-blue-500 h-1 rounded-full transition-all duration-300"
                      style={{ width: `${fileItem.progress}%` }}
                    />
                  </div>
                </div>
              )}
            </div>
            
            <div className="flex items-center space-x-2">
              {getStatusIcon(fileItem.status)}
              
              {!disabled && fileItem.status !== 'uploading' && fileItem.status !== 'processing' && (
                <button
                  onClick={() => onRemoveFile(fileItem.id)}
                  className="p-1 text-gray-400 hover:text-red-500 transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default FileList
