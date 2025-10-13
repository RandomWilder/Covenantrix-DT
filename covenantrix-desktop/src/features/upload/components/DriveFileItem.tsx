import React from 'react'
import { FileText, Image, File as FileIcon, Folder, Table, Presentation } from 'lucide-react'

export interface DriveFile {
  id: string
  name: string
  mimeType?: string
  size?: number
  modifiedTime?: string
  webViewLink?: string
  iconLink?: string
}

interface DriveFileItemProps {
  file: DriveFile
  isSelected: boolean
  onToggle: () => void
  onNavigate?: (folderId: string) => void
  disabled?: boolean
  viewMode: 'list' | 'grid'
}

const DriveFileItem: React.FC<DriveFileItemProps> = ({
  file,
  isSelected,
  onToggle,
  onNavigate,
  disabled = false,
  viewMode = 'list'
}) => {
  const isFolder = file.mimeType === 'application/vnd.google-apps.folder'

  const getFileIcon = () => {
    const mimeType = file.mimeType || ''
    
    if (isFolder) {
      return <Folder className="w-5 h-5 text-blue-500" />
    } else if (mimeType.includes('pdf')) {
      return <FileText className="w-5 h-5 text-red-500" />
    } else if (mimeType.startsWith('image/')) {
      return <Image className="w-5 h-5 text-green-500" />
    } else if (mimeType.includes('word') || mimeType.includes('document')) {
      return <FileText className="w-5 h-5 text-blue-600" />
    } else if (mimeType.includes('sheet') || mimeType.includes('excel')) {
      return <Table className="w-5 h-5 text-green-600" />
    } else if (mimeType.includes('presentation') || mimeType.includes('powerpoint')) {
      return <Presentation className="w-5 h-5 text-orange-600" />
    } else {
      return <FileIcon className="w-5 h-5 text-gray-500" />
    }
  }

  const formatFileSize = (bytes?: number) => {
    if (!bytes || isFolder) return ''
    const mb = bytes / (1024 * 1024)
    if (mb < 1) {
      const kb = bytes / 1024
      return `${kb.toFixed(0)} KB`
    }
    return `${mb.toFixed(1)} MB`
  }

  const formatDate = (dateString?: string) => {
    if (!dateString) return ''
    
    try {
      const date = new Date(dateString)
      const now = new Date()
      const diffMs = now.getTime() - date.getTime()
      const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

      if (diffDays === 0) return 'Today'
      if (diffDays === 1) return 'Yesterday'
      if (diffDays < 7) return `${diffDays} days ago`
      if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`
      
      return date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric',
        year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
      })
    } catch {
      return dateString
    }
  }

  const handleClick = () => {
    // Single click on folder just highlights it (no action)
    // For files, clicking selects them via checkbox
    // This allows users to see folder info before navigating
  }

  const handleDoubleClick = () => {
    // Double-click navigates into folder
    if (isFolder && onNavigate) {
      onNavigate(file.id)
    }
  }

  if (viewMode === 'grid') {
    return (
      <div
        className={`relative p-4 rounded-lg border transition-all ${
          isFolder ? 'cursor-pointer hover:border-blue-400 dark:hover:border-blue-500' : 'cursor-default'
        } ${
          isSelected
            ? 'bg-primary/10 border-primary ring-2 ring-primary/20'
            : isFolder
            ? 'bg-blue-50 dark:bg-blue-900/10 border-blue-200 dark:border-blue-800 hover:bg-blue-100 dark:hover:bg-blue-900/20'
            : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700'
        } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
        onClick={handleClick}
        onDoubleClick={handleDoubleClick}
      >
        {/* Checkbox */}
        {!isFolder && (
          <div className="absolute top-2 left-2">
            <input
              type="checkbox"
              checked={isSelected}
              onChange={(e) => {
                e.stopPropagation()
                onToggle()
              }}
              disabled={disabled}
              className="w-4 h-4 text-primary rounded border-gray-300 dark:border-gray-600 focus:ring-primary"
              onClick={(e) => e.stopPropagation()}
            />
          </div>
        )}

        {/* Icon */}
        <div className="flex justify-center mb-3">
          <div className="p-3 bg-gray-100 dark:bg-gray-700 rounded-lg">
            {getFileIcon()}
          </div>
        </div>

        {/* Name */}
        <div className="text-center">
          <div className="text-sm font-medium text-gray-900 dark:text-white truncate" title={file.name}>
            {file.name}
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            {formatFileSize(file.size) || formatDate(file.modifiedTime)}
          </div>
        </div>
      </div>
    )
  }

  // List view
  return (
    <div
      className={`flex items-center space-x-3 p-3 rounded-lg border transition-all ${
        isFolder ? 'cursor-pointer hover:border-blue-400 dark:hover:border-blue-500' : 'cursor-default'
      } ${
        isSelected
          ? 'bg-primary/10 border-primary'
          : isFolder
          ? 'bg-blue-50 dark:bg-blue-900/10 border-blue-200 dark:border-blue-800 hover:bg-blue-100 dark:hover:bg-blue-900/20'
          : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700'
      } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
      onClick={handleClick}
      onDoubleClick={handleDoubleClick}
    >
      {/* Checkbox */}
      {!isFolder && (
        <input
          type="checkbox"
          checked={isSelected}
          onChange={onToggle}
          disabled={disabled}
          className="w-4 h-4 text-primary rounded border-gray-300 dark:border-gray-600 focus:ring-primary"
          onClick={(e) => e.stopPropagation()}
        />
      )}

      {/* Icon */}
      {getFileIcon()}

      {/* File Info */}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
          {file.name}
        </p>
        <p className="text-xs text-gray-500 dark:text-gray-400">
          {formatDate(file.modifiedTime)}
          {file.size && ` • ${formatFileSize(file.size)}`}
        </p>
      </div>
    </div>
  )
}

export default DriveFileItem

