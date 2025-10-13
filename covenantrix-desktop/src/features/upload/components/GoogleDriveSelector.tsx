import React, { useState, useEffect } from 'react'
import { Cloud, FolderOpen, RefreshCw, AlertCircle, ArrowLeft } from 'lucide-react'
import { useToast } from '../../../hooks/useToast'
import { googleService, GoogleAccountResponse } from '../../../services/googleService'
import DriveAccountSelector from './DriveAccountSelector'
import DriveBreadcrumbs, { BreadcrumbItem } from './DriveBreadcrumbs'
import DriveFileList from './DriveFileList'
import DriveSearchBar from './DriveSearchBar'
import { DriveFile } from './DriveFileItem'

interface GoogleDriveSelectorProps {
  onAddToQueue: (files: DriveFile[], accountId: string, accountEmail: string) => void
  disabled?: boolean
}

const GoogleDriveSelector: React.FC<GoogleDriveSelectorProps> = ({
  onAddToQueue,
  disabled = false
}) => {
  // State
  const [accounts, setAccounts] = useState<GoogleAccountResponse[]>([])
  const [selectedAccount, setSelectedAccount] = useState<string | null>(null)
  const [currentFolder, setCurrentFolder] = useState<string | null>(null)
  const [files, setFiles] = useState<DriveFile[]>([])
  const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set())
  const [breadcrumbs, setBreadcrumbs] = useState<BreadcrumbItem[]>([])
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('list')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [filterMimeType, setFilterMimeType] = useState<string | null>(null)
  
  const { showToast } = useToast()

  // Load accounts on mount
  useEffect(() => {
    loadAccounts()
  }, [])

  // Load files when account or folder changes
  useEffect(() => {
    if (selectedAccount) {
      loadFiles()
    }
  }, [selectedAccount, currentFolder, searchQuery, filterMimeType])

  const loadAccounts = async () => {
    try {
      const response = await googleService.listAccounts()
      setAccounts(response.accounts)
      
      // Auto-select first account if available
      if (response.accounts.length > 0 && !selectedAccount) {
        setSelectedAccount(response.accounts[0].account_id)
      }
    } catch (error) {
      console.error('Failed to load Google accounts:', error)
      showToast('Failed to load Google accounts', 'error')
    }
  }

  const loadFiles = async () => {
    if (!selectedAccount) return

    setIsLoading(true)
    setError(null)
    
    try {
      const response = await googleService.listDriveFiles(
        selectedAccount,
        currentFolder || undefined
      )
      
      // Convert to DriveFile format
      const driveFiles: DriveFile[] = response.files.map(file => ({
        id: file.id,
        name: file.name,
        mimeType: file.mimeType,  // Backend sends camelCase
        size: file.size,
        modifiedTime: file.modifiedTime,  // Backend sends camelCase
        webViewLink: file.webViewLink,  // Backend sends camelCase
        iconLink: file.iconLink  // Backend sends camelCase
      }))

      // Apply client-side filtering
      let filteredFiles = driveFiles

      // Filter by search query
      if (searchQuery) {
        filteredFiles = filteredFiles.filter(file =>
          file.name.toLowerCase().includes(searchQuery.toLowerCase())
        )
      }

      // Filter by MIME type
      if (filterMimeType) {
        filteredFiles = filteredFiles.filter(file =>
          file.mimeType?.startsWith(filterMimeType) || false
        )
      }

      // Sort: folders first, then alphabetically
      filteredFiles.sort((a, b) => {
        const aIsFolder = a.mimeType === 'application/vnd.google-apps.folder'
        const bIsFolder = b.mimeType === 'application/vnd.google-apps.folder'
        
        if (aIsFolder && !bIsFolder) return -1
        if (!aIsFolder && bIsFolder) return 1
        return a.name.localeCompare(b.name)
      })

      setFiles(filteredFiles)
    } catch (error: any) {
      console.error('Failed to load Drive files:', error)
      setError(error.message || 'Failed to load files from Google Drive')
      showToast('Failed to load Drive files', 'error')
    } finally {
      setIsLoading(false)
    }
  }

  const handleAccountSelect = (accountId: string) => {
    setSelectedAccount(accountId)
    setCurrentFolder(null)
    setBreadcrumbs([])
    setSelectedFiles(new Set())
  }

  const handleAddAccount = () => {
    // Open profile modal to connected accounts tab
    // This will be implemented via a context or event system
    showToast('Opening profile settings...', 'info')
    // TODO: Integrate with ProfileModal
  }

  const handleManageAccounts = () => {
    showToast('Opening profile settings...', 'info')
    // TODO: Integrate with ProfileModal
  }

  const handleNavigate = (folderId: string | null) => {
    if (folderId === null) {
      // Navigate to root
      setCurrentFolder(null)
      setBreadcrumbs([])
    } else {
      // Navigate to specific folder
      const folderIndex = breadcrumbs.findIndex(b => b.id === folderId)
      if (folderIndex >= 0) {
        // Navigating backwards - trim breadcrumbs
        setBreadcrumbs(breadcrumbs.slice(0, folderIndex + 1))
        setCurrentFolder(folderId)
      } else {
        // Navigating forwards - add to breadcrumbs
        const folder = files.find(f => f.id === folderId)
        if (folder) {
          setBreadcrumbs([...breadcrumbs, { id: folderId, name: folder.name }])
          setCurrentFolder(folderId)
        }
      }
    }
    setSelectedFiles(new Set())
  }

  const handleToggleSelect = (fileId: string) => {
    const file = files.find(f => f.id === fileId)
    if (file && file.mimeType === 'application/vnd.google-apps.folder') {
      // Folders are not selectable
      return
    }

    const newSelected = new Set(selectedFiles)
    if (newSelected.has(fileId)) {
      newSelected.delete(fileId)
    } else {
      newSelected.add(fileId)
    }
    setSelectedFiles(newSelected)
  }

  const handleSelectAll = () => {
    // Select all non-folder files
    const selectableFiles = files.filter(
      f => f.mimeType !== 'application/vnd.google-apps.folder'
    )
    
    if (selectedFiles.size === selectableFiles.length) {
      setSelectedFiles(new Set())
    } else {
      setSelectedFiles(new Set(selectableFiles.map(f => f.id)))
    }
  }

  const handleAddToQueue = () => {
    if (selectedFiles.size === 0 || !selectedAccount) return
    
    // Get selected file objects
    const selectedDriveFiles = Array.from(selectedFiles)
      .map(fileId => files.find(f => f.id === fileId))
      .filter((f): f is DriveFile => f !== undefined)
    
    // Get account email
    const account = accounts.find(a => a.account_id === selectedAccount)
    const accountEmail = account?.email || 'unknown'
    
    // Call parent handler
    onAddToQueue(selectedDriveFiles, selectedAccount, accountEmail)
    
    // Clear selection
    setSelectedFiles(new Set())
    
    // Show success toast
    showToast(`Added ${selectedDriveFiles.length} file(s) to upload queue`, 'success')
  }

  const calculateTotalSize = () => {
    let total = 0
    selectedFiles.forEach(fileId => {
      const file = files.find(f => f.id === fileId)
      if (file?.size) {
        total += file.size
      }
    })
    return total
  }

  const formatTotalSize = (bytes: number) => {
    const mb = bytes / (1024 * 1024)
    if (mb < 1) {
      return `${(bytes / 1024).toFixed(0)} KB`
    }
    return `${mb.toFixed(1)} MB`
  }

  // Empty state: No accounts
  if (accounts.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="p-4 bg-gray-100 dark:bg-gray-800 rounded-full w-16 h-16 mx-auto mb-4 flex items-center justify-center">
          <Cloud className="w-8 h-8 text-gray-600 dark:text-gray-400" />
        </div>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
          Connect Google Drive
        </h3>
        <p className="text-gray-600 dark:text-gray-400 mb-6">
          Go to your Profile settings to connect your Google Drive account
        </p>
        <button
          onClick={handleAddAccount}
          disabled={disabled}
          className="px-6 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50"
        >
          Open Profile Settings
        </button>
      </div>
    )
  }

  // Error state
  if (error && !isLoading) {
    return (
      <div className="text-center py-12">
        <div className="p-4 bg-red-100 dark:bg-red-900/20 rounded-full w-16 h-16 mx-auto mb-4 flex items-center justify-center">
          <AlertCircle className="w-8 h-8 text-red-600 dark:text-red-500" />
        </div>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
          Failed to load Drive files
        </h3>
        <p className="text-gray-600 dark:text-gray-400 mb-6">
          {error}
        </p>
        <div className="flex items-center justify-center space-x-3">
          <button
            onClick={loadFiles}
            className="px-6 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
          >
            Try Again
          </button>
          <button
            onClick={() => {
              setSelectedAccount(null)
              setAccounts([])
              loadAccounts()
            }}
            className="px-6 py-2 bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
          >
            Reconnect Account
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Account Selector */}
      <DriveAccountSelector
        accounts={accounts}
        selectedAccountId={selectedAccount}
        onAccountSelect={handleAccountSelect}
        onAddAccount={handleAddAccount}
        onManageAccounts={handleManageAccounts}
        disabled={disabled || isLoading}
      />

      {/* Navigation Bar */}
      <div className="flex items-center justify-between space-x-4">
        <div className="flex-1 min-w-0">
          <DriveBreadcrumbs
            items={breadcrumbs}
            onNavigate={handleNavigate}
            disabled={disabled || isLoading}
          />
        </div>
        
        {currentFolder && (
          <button
            onClick={() => {
              const parentIndex = breadcrumbs.length - 2
              if (parentIndex >= 0) {
                handleNavigate(breadcrumbs[parentIndex].id)
              } else {
                handleNavigate(null)
              }
            }}
            disabled={disabled || isLoading}
            className="flex items-center space-x-1 px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors disabled:opacity-50"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back</span>
          </button>
        )}
        
        <button
          onClick={loadFiles}
          disabled={disabled || isLoading}
          className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors disabled:opacity-50"
          title="Refresh"
        >
          <RefreshCw className={`w-5 h-5 ${isLoading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Search Bar */}
      <DriveSearchBar
        onSearch={setSearchQuery}
        onFilterChange={setFilterMimeType}
        disabled={disabled || isLoading}
      />

      {/* Select All */}
      {files.some(f => f.mimeType !== 'application/vnd.google-apps.folder') && (
        <div className="flex items-center space-x-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <input
            type="checkbox"
            checked={
              selectedFiles.size > 0 &&
              selectedFiles.size === files.filter(f => f.mimeType !== 'application/vnd.google-apps.folder').length
            }
            onChange={handleSelectAll}
            disabled={disabled || isLoading}
            className="w-4 h-4 text-primary rounded border-gray-300 dark:border-gray-600"
          />
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Select All
          </span>
          {selectedFiles.size > 0 && (
            <span className="text-sm text-gray-500 dark:text-gray-400">
              ({selectedFiles.size} selected)
            </span>
          )}
        </div>
      )}

      {/* Fixed-height scrollable file list container */}
      <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-y-auto" style={{ maxHeight: 'min(50vh, 500px)' }}>
        {isLoading ? (
          <div className="text-center py-12">
            <RefreshCw className="w-8 h-8 text-gray-400 animate-spin mx-auto mb-2" />
            <p className="text-gray-600 dark:text-gray-400">Loading files...</p>
          </div>
        ) : files.length === 0 ? (
          <div className="text-center py-12">
            <FolderOpen className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600 dark:text-gray-400">
              {searchQuery || filterMimeType
                ? 'No files match your search'
                : 'This folder is empty'}
            </p>
          </div>
        ) : (
          <DriveFileList
            files={files}
            selectedFiles={selectedFiles}
            onToggleSelect={handleToggleSelect}
            onNavigate={handleNavigate}
            viewMode={viewMode}
            onViewModeChange={setViewMode}
            disabled={disabled || isLoading}
          />
        )}
      </div>

      {/* Sticky action bar - only shows when files selected */}
      {selectedFiles.size > 0 && (
        <div className="sticky bottom-0 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 shadow-lg">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <div className="text-sm font-medium text-gray-900 dark:text-white">
                ☑ {selectedFiles.size} file{selectedFiles.size !== 1 ? 's' : ''} selected
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400">
                Total size: {formatTotalSize(calculateTotalSize())}
              </div>
            </div>
            <div className="flex space-x-3">
              <button
                onClick={() => setSelectedFiles(new Set())}
                className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors"
              >
                Clear
              </button>
              <button
                onClick={handleAddToQueue}
                disabled={disabled}
                className="px-6 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50"
              >
                Add to Upload
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default GoogleDriveSelector
