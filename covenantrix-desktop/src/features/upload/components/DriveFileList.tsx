import React from 'react'
import { Grid, List } from 'lucide-react'
import DriveFileItem, { DriveFile } from './DriveFileItem'

interface DriveFileListProps {
  files: DriveFile[]
  selectedFiles: Set<string>
  onToggleSelect: (fileId: string) => void
  onNavigate: (folderId: string) => void
  viewMode: 'list' | 'grid'
  onViewModeChange: (mode: 'list' | 'grid') => void
  disabled?: boolean
}

const DriveFileList: React.FC<DriveFileListProps> = ({
  files,
  selectedFiles,
  onToggleSelect,
  onNavigate,
  viewMode,
  onViewModeChange,
  disabled = false
}) => {
  return (
    <div className="space-y-3">
      {/* View Mode Toggle */}
      <div className="flex items-center justify-between">
        <div className="text-sm text-gray-600 dark:text-gray-400">
          {files.length} item{files.length !== 1 ? 's' : ''}
        </div>
        
        <div className="flex space-x-1 bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
          <button
            onClick={() => onViewModeChange('list')}
            className={`p-2 rounded transition-colors ${
              viewMode === 'list'
                ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
            }`}
            title="List view"
          >
            <List className="w-4 h-4" />
          </button>
          
          <button
            onClick={() => onViewModeChange('grid')}
            className={`p-2 rounded transition-colors ${
              viewMode === 'grid'
                ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
            }`}
            title="Grid view"
          >
            <Grid className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Files Grid/List */}
      {viewMode === 'grid' ? (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
          {files.map((file) => (
            <DriveFileItem
              key={file.id}
              file={file}
              isSelected={selectedFiles.has(file.id)}
              onToggle={() => onToggleSelect(file.id)}
              onNavigate={onNavigate}
              disabled={disabled}
              viewMode="grid"
            />
          ))}
        </div>
      ) : (
        <div className="space-y-1">
          {files.map((file) => (
            <DriveFileItem
              key={file.id}
              file={file}
              isSelected={selectedFiles.has(file.id)}
              onToggle={() => onToggleSelect(file.id)}
              onNavigate={onNavigate}
              disabled={disabled}
              viewMode="list"
            />
          ))}
        </div>
      )}
    </div>
  )
}

export default DriveFileList

