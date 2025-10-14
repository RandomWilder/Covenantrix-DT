import { useState, useCallback, useEffect, useRef } from 'react'
import { useToast } from './useToast'
import { useSubscription } from '../contexts/SubscriptionContext'
import { useUpgradeModal } from '../contexts/UpgradeModalContext'
import { DocumentsApi } from '../services/api/DocumentsApi'
import { DocumentProgressStage } from '../types/document'

interface FileItem {
  id: string
  file: File
  filename: string  // Store filename for persistence
  documentId?: string  // Store document ID for backend polling
  status?: 'pending' | 'uploading' | 'processing' | 'completed' | 'failed'
  progress?: number
  error?: string
  stage?: DocumentProgressStage
  stageMessage?: string
  source?: 'local' | 'drive'
  sourceAccount?: string  // Email for Drive files (display only)
  driveAccountId?: string // Google account ID for API calls
  driveFileId?: string    // Google Drive file ID
}

interface UploadProgress {
  total: number
  completed: number
  failed: number
  current?: string
  files: FileItem[]
}

interface PersistedUploadState {
  files: Array<{
    id: string
    filename: string
    documentId?: string
    status?: FileItem['status']
    progress?: number
    error?: string
    stage?: DocumentProgressStage
    stageMessage?: string
    source?: 'local' | 'drive'
    sourceAccount?: string
    driveAccountId?: string
    driveFileId?: string
  }>
  isUploading: boolean
  uploadProgress: UploadProgress
  timestamp: number
}

const UPLOAD_STATE_KEY = 'covenantrix_upload_state'
const STATE_EXPIRY_MS = 24 * 60 * 60 * 1000 // 24 hours

export const useUpload = () => {
  const [files, setFiles] = useState<FileItem[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState<UploadProgress>({
    total: 0,
    completed: 0,
    failed: 0,
    files: []
  })
  const { showToast } = useToast()
  const { subscription, canUploadDocument, getRemainingQuota } = useSubscription()
  const { showUpgradeModal } = useUpgradeModal()
  const pollingIntervalRef = useRef<NodeJS.Timeout>()
  
  // Poll backend for document status updates
  const startPollingBackend = useCallback(() => {
    // Clear existing interval if any
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current)
    }
    
    const documentsApi = new DocumentsApi()
    
    pollingIntervalRef.current = setInterval(async () => {
      try {
        // Check current files state for any that are still processing
        setFiles(currentFiles => {
          const processingFiles = currentFiles.filter(f => 
            (f.status === 'uploading' || f.status === 'processing') && f.documentId
          )
          
          if (processingFiles.length === 0) {
            // No more files to poll, clear interval
            if (pollingIntervalRef.current) {
              clearInterval(pollingIntervalRef.current)
              pollingIntervalRef.current = undefined
            }
            setIsUploading(false)
            return currentFiles
          }
          
          // Continue with current files, will be updated below
          return currentFiles
        })
        
        // Fetch document list from backend
        const response = await documentsApi.getDocuments()
        
        // Update file statuses based on backend response
        setFiles(prev => {
          const updatedFiles = prev.map(file => {
            if (!file.documentId) return file
            
            const backendDoc = response.documents.find(d => d.document_id === file.documentId)
            if (!backendDoc) return file
            
            // Map backend status to UI status
            let newStatus: FileItem['status'] = file.status
            let newProgress = file.progress
            let newStage = file.stage
            let newMessage = file.stageMessage
            
            if (backendDoc.status === 'processed') {
              newStatus = 'completed'
              newProgress = 100
              newStage = 'completed'
              newMessage = 'Document ready'
            } else if (backendDoc.status === 'failed') {
              newStatus = 'failed'
              newStage = 'failed'
              newMessage = 'Processing failed'
            } else if (backendDoc.status === 'processing') {
              newStatus = 'processing'
              newStage = 'building_connections'
              newMessage = 'Building knowledge connections...'
            }
            
            return {
              ...file,
              status: newStatus,
              progress: newProgress,
              stage: newStage,
              stageMessage: newMessage
            }
          })
          
          // Update overall progress based on updated files
          setUploadProgress(prevProgress => {
            const completed = updatedFiles.filter(f => f.status === 'completed').length
            const failed = updatedFiles.filter(f => f.status === 'failed').length
            
            return {
              ...prevProgress,
              completed,
              failed,
              files: updatedFiles
            }
          })
          
          return updatedFiles
        })
        
      } catch (error) {
        console.error('Failed to poll backend for status:', error)
      }
    }, 2000) // Poll every 2 seconds
  }, [])
  
  // Restore state on mount
  useEffect(() => {
    const restoreState = async () => {
      try {
        const savedState = localStorage.getItem(UPLOAD_STATE_KEY)
        if (!savedState) return
        
        const parsed: PersistedUploadState = JSON.parse(savedState)
        
        // Check if state is expired
        if (Date.now() - parsed.timestamp > STATE_EXPIRY_MS) {
          localStorage.removeItem(UPLOAD_STATE_KEY)
          return
        }
        
        // Check if there are any in-progress uploads
        const hasActiveUploads = parsed.files.some(f => 
          f.status === 'uploading' || f.status === 'processing'
        )
        
        if (hasActiveUploads) {
          // Always validate with backend when there are active uploads
          try {
            const documentsApi = new DocumentsApi()
            const response = await documentsApi.getDocuments()
            const backendDocIds = new Set(response.documents.map(d => d.document_id))
            
            // Check if we have files with document IDs
            const documentsWithIds = parsed.files.filter(f => f.documentId)
            
            if (documentsWithIds.length > 0) {
              // Validate that these documents still exist
              const stillExist = documentsWithIds.some(f => backendDocIds.has(f.documentId!))
              
              if (!stillExist) {
                // All documents were removed (e.g., storage reset), clear stale state
                console.log('No persisted documents found in backend, clearing stale upload state')
                localStorage.removeItem(UPLOAD_STATE_KEY)
                return
              }
              
              // Filter out files whose documents no longer exist
              parsed.files = parsed.files.filter(f => 
                !f.documentId || backendDocIds.has(f.documentId)
              )
            } else if (backendDocIds.size === 0) {
              // Files are in uploading state but no document IDs yet, and backend is empty
              // This is stale state from before a reset - clear it
              console.log('Active uploads without document IDs and empty backend, clearing stale state')
              localStorage.removeItem(UPLOAD_STATE_KEY)
              return
            }
            
            // If we get here and parsed.files is empty, don't restore anything
            if (parsed.files.length === 0) {
              localStorage.removeItem(UPLOAD_STATE_KEY)
              return
            }
            
          } catch (error) {
            // If backend validation fails, proceed with restoration
            // (backend might be temporarily unavailable)
            console.warn('Failed to validate upload state with backend:', error)
          }
          
          // Note: We can't restore File objects, so these will be placeholder files
          const restoredFiles: FileItem[] = parsed.files.map(f => ({
            id: f.id,
            filename: f.filename,
            documentId: f.documentId,
            file: new File([], f.filename), // Placeholder - actual file isn't needed for display
            status: f.status,
            progress: f.progress,
            error: f.error,
            stage: f.stage,
            stageMessage: f.stageMessage,
            source: f.source,
            sourceAccount: f.sourceAccount,
            driveAccountId: f.driveAccountId,
            driveFileId: f.driveFileId
          }))
          
          setFiles(restoredFiles)
          setIsUploading(parsed.isUploading)
          setUploadProgress(parsed.uploadProgress)
          
          // Start polling backend for status updates
          startPollingBackend()
        }
      } catch (error) {
        console.error('Failed to restore upload state:', error)
        localStorage.removeItem(UPLOAD_STATE_KEY)
      }
    }
    
    restoreState()
    
    // Cleanup polling on unmount
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current)
      }
    }
  }, [startPollingBackend])
  
  // Persist state whenever it changes
  useEffect(() => {
    if (files.length === 0 && !isUploading) {
      // Clear persisted state when upload is complete
      localStorage.removeItem(UPLOAD_STATE_KEY)
      return
    }
    
    const state: PersistedUploadState = {
      files: files.map(f => ({
        id: f.id,
        filename: f.filename,
        documentId: f.documentId,
        status: f.status,
        progress: f.progress,
        error: f.error,
        stage: f.stage,
        stageMessage: f.stageMessage,
        source: f.source,
        sourceAccount: f.sourceAccount,
        driveAccountId: f.driveAccountId,
        driveFileId: f.driveFileId
      })),
      isUploading,
      uploadProgress,
      timestamp: Date.now()
    }
    
    localStorage.setItem(UPLOAD_STATE_KEY, JSON.stringify(state))
  }, [files, isUploading, uploadProgress])
  
  const addFiles = useCallback((newFiles: File[]) => {
    // Check subscription limits
    if (!canUploadDocument()) {
      const remaining = getRemainingQuota('documents')
      showUpgradeModal({
        title: 'Document Limit Reached',
        message: `You've reached the maximum of ${subscription?.features.max_documents} documents for the ${subscription?.tier} tier.`,
        currentTier: subscription?.tier,
        details: `Remaining documents: ${remaining}`
      })
      return
    }
    
    // Check file sizes
    if (subscription) {
      const maxSizeMB = subscription.features.max_doc_size_mb
      const oversizedFiles = newFiles.filter(f => (f.size / (1024 * 1024)) > maxSizeMB)
      
      if (oversizedFiles.length > 0) {
        showToast(
          `${oversizedFiles.length} file(s) exceed the ${maxSizeMB}MB size limit for your ${subscription.tier} tier`,
          'error'
        )
        // Filter out oversized files
        newFiles = newFiles.filter(f => (f.size / (1024 * 1024)) <= maxSizeMB)
        if (newFiles.length === 0) return
      }
    }
    
    const fileItems: FileItem[] = newFiles.map(file => ({
      id: Math.random().toString(36).substr(2, 9),
      file,
      filename: file.name,
      status: 'pending',
      source: 'local'
    }))
    
    setFiles(prev => [...prev, ...fileItems])
    showToast(`${newFiles.length} file(s) added`, 'success')
  }, [showToast, canUploadDocument, getRemainingQuota, subscription, showUpgradeModal])

  const addDriveFiles = useCallback((driveFiles: Array<{id: string; name: string; size?: number}>, accountId: string, accountEmail: string) => {
    const fileItems: FileItem[] = driveFiles.map(driveFile => ({
      id: driveFile.id, // Use Drive file ID
      file: new File([], driveFile.name), // Placeholder File object
      filename: driveFile.name,
      status: 'pending' as const,
      source: 'drive' as const,
      sourceAccount: accountEmail,  // Email for display
      driveAccountId: accountId,    // Account ID for API calls
      driveFileId: driveFile.id
    }))
    
    setFiles(prev => [...prev, ...fileItems])
    showToast(`Added ${driveFiles.length} Drive file(s) to queue`, 'success')
  }, [showToast])

  const removeFile = useCallback((id: string) => {
    setFiles(prev => prev.filter(f => f.id !== id))
  }, [])

  const clearFiles = useCallback(() => {
    setFiles([])
    setUploadProgress({
      total: 0,
      completed: 0,
      failed: 0,
      files: []
    })
  }, [])

  const updateFileStatus = useCallback((
    id: string, 
    status: FileItem['status'], 
    progress?: number, 
    error?: string,
    stage?: DocumentProgressStage,
    stageMessage?: string,
    documentId?: string
  ) => {
    setFiles(prev => prev.map(f => 
      f.id === id 
        ? { ...f, status, progress, error, stage, stageMessage, documentId: documentId || f.documentId }
        : f
    ))
  }, [])

  const startUpload = useCallback(async () => {
    if (files.length === 0) {
      showToast('No files selected', 'error')
      return
    }
    
    // Double-check subscription limits before upload
    if (!canUploadDocument()) {
      const remaining = getRemainingQuota('documents')
      showUpgradeModal({
        title: 'Upload Limit Reached',
        message: `Cannot upload documents. You've reached your limit for the ${subscription?.tier} tier.`,
        currentTier: subscription?.tier,
        details: `Remaining documents: ${remaining}`
      })
      return
    }

    setIsUploading(true)
    
    // Initialize progress tracking
    const progress: UploadProgress = {
      total: files.length,
      completed: 0,
      failed: 0,
      files: files.map(f => ({ ...f }))
    }
    setUploadProgress(progress)

    try {
      // Group files by source
      const localFiles = files.filter(f => !f.source || f.source === 'local')
      const driveFiles = files.filter(f => f.source === 'drive')
      
      // Start both uploads in parallel if we have both types
      const uploadPromises = []
      
      if (localFiles.length > 0) {
        uploadPromises.push(
          uploadLocalFiles(localFiles, progress, updateFileStatus, setUploadProgress)
        )
      }
      
      if (driveFiles.length > 0) {
        // Group Drive files by account ID
        const driveFilesByAccount = new Map<string, FileItem[]>()
        driveFiles.forEach(file => {
          const accountId = file.driveAccountId || 'unknown'
          if (!driveFilesByAccount.has(accountId)) {
            driveFilesByAccount.set(accountId, [])
          }
          driveFilesByAccount.get(accountId)!.push(file)
        })
        
        // Upload each account's files
        driveFilesByAccount.forEach((accountFiles, accountId) => {
          uploadPromises.push(
            uploadGoogleDriveFiles(accountFiles, accountId, progress, updateFileStatus, setUploadProgress)
          )
        })
      }
      
      // Wait for all uploads to complete
      await Promise.all(uploadPromises)
      
      // Start backend polling for document status
      startPollingBackend()
    } catch (error) {
      console.error('Upload failed:', error)
      showToast('Upload failed', 'error')
    } finally {
      setIsUploading(false)
    }
  }, [files, showToast, updateFileStatus, startPollingBackend, canUploadDocument, getRemainingQuota, subscription, showUpgradeModal])

  return {
    files,
    isUploading,
    uploadProgress,
    addFiles,
    addDriveFiles,
    removeFile,
    clearFiles,
    startUpload
  }
}

const uploadLocalFiles = async (
  files: FileItem[],
  progress: UploadProgress,
  updateFileStatus: (
    id: string, 
    status: FileItem['status'], 
    progress?: number, 
    error?: string,
    stage?: DocumentProgressStage,
    stageMessage?: string,
    documentId?: string
  ) => void,
  setUploadProgress: (progress: UploadProgress) => void
) => {
  // Always use streaming upload for consistent progress updates
  const documentsApi = new DocumentsApi()
  const fileArray = files.map(f => f.file)
  
  // Track which files have been marked as completed/failed to avoid duplication
  const completedFiles = new Set<string>()
  const failedFiles = new Set<string>()
  
  try {
    // Initialize all files as uploading
    files.forEach(fileItem => {
      updateFileStatus(fileItem.id, 'uploading', 0, undefined, 'initializing', 'Preparing document...')
    })

    // Stream progress updates
    for await (const event of documentsApi.uploadDocumentsStream(fileArray)) {
      const { file_progress, current_file_index } = event
      const fileItem = files[current_file_index]
      
      if (!fileItem) continue

      // Map status from stage
      let status: FileItem['status'] = 'processing'
      
      // Only increment counters once per file
      if (file_progress.stage === 'completed' && !completedFiles.has(fileItem.id)) {
        status = 'completed'
        completedFiles.add(fileItem.id)
      } else if (file_progress.stage === 'failed' && !failedFiles.has(fileItem.id)) {
        status = 'failed'
        failedFiles.add(fileItem.id)
      }

      // Update file status with stage information and document ID
      updateFileStatus(
        fileItem.id,
        status,
        file_progress.progress_percent,
        file_progress.error,
        file_progress.stage,
        file_progress.message,
        file_progress.document_id
      )

      // Update overall progress with tracked counters
      setUploadProgress({ 
        ...progress, 
        completed: completedFiles.size,
        failed: failedFiles.size,
        current: file_progress.filename,
        files: [...files]
      })
    }

    setUploadProgress({ 
      ...progress, 
      completed: completedFiles.size,
      failed: failedFiles.size,
      files: [...files]
    })
  } catch (error) {
    // Mark remaining files as failed
    files.forEach(fileItem => {
      if (fileItem.status !== 'completed' && !failedFiles.has(fileItem.id)) {
        updateFileStatus(
          fileItem.id, 
          'failed', 
          0, 
          error instanceof Error ? error.message : 'Upload failed',
          'failed',
          'Processing failed'
        )
        failedFiles.add(fileItem.id)
      }
    })
    
    setUploadProgress({ 
      ...progress, 
      completed: completedFiles.size,
      failed: failedFiles.size,
      files: [...files]
    })
    throw error
  }
}

const uploadGoogleDriveFiles = async (
  files: FileItem[],
  accountId: string,
  progress: UploadProgress,
  updateFileStatus: (
    id: string, 
    status: FileItem['status'], 
    progress?: number, 
    error?: string,
    stage?: DocumentProgressStage,
    stageMessage?: string,
    documentId?: string
  ) => void,
  setUploadProgress: (progress: UploadProgress) => void
) => {
  // Use streaming upload for consistent progress updates
  const { googleService } = await import('../services/googleService')
  const fileIds = files.map(f => f.driveFileId!).filter(Boolean)
  
  // Track which files have been marked as completed/failed to avoid duplication
  const completedFiles = new Set<string>()
  const failedFiles = new Set<string>()
  
  try {
    // Initialize all files as uploading
    files.forEach(fileItem => {
      updateFileStatus(fileItem.id, 'uploading', 0, undefined, 'initializing', 'Preparing to download from Drive...')
    })

    // Stream progress updates
    for await (const event of googleService.downloadDriveFilesStream(accountId, fileIds)) {
      const { file_progress, current_file_index } = event
      const fileItem = files[current_file_index]
      
      if (!fileItem) continue

      // Map status from stage
      let status: FileItem['status'] = 'processing'
      
      // Only increment counters once per file
      if (file_progress.stage === 'completed' && !completedFiles.has(fileItem.id)) {
        status = 'completed'
        completedFiles.add(fileItem.id)
      } else if (file_progress.stage === 'failed' && !failedFiles.has(fileItem.id)) {
        status = 'failed'
        failedFiles.add(fileItem.id)
      }

      // Update file status with stage information and document ID
      updateFileStatus(
        fileItem.id,
        status,
        file_progress.progress_percent,
        file_progress.error,
        file_progress.stage as DocumentProgressStage,
        file_progress.message,
        file_progress.document_id
      )

      // Update overall progress with tracked counters
      setUploadProgress({ 
        ...progress, 
        completed: completedFiles.size,
        failed: failedFiles.size,
        current: file_progress.filename,
        files: [...files]
      })
    }

    setUploadProgress({ 
      ...progress, 
      completed: completedFiles.size,
      failed: failedFiles.size,
      files: [...files]
    })
  } catch (error) {
    // Mark remaining files as failed
    files.forEach(fileItem => {
      if (fileItem.status !== 'completed' && !failedFiles.has(fileItem.id)) {
        updateFileStatus(
          fileItem.id, 
          'failed', 
          0, 
          error instanceof Error ? error.message : 'Upload failed',
          'failed',
          'Processing failed'
        )
        failedFiles.add(fileItem.id)
      }
    })
    
    setUploadProgress({ 
      ...progress, 
      completed: completedFiles.size,
      failed: failedFiles.size,
      files: [...files]
    })
    throw error
  }
}
