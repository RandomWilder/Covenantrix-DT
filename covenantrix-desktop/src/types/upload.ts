// Simplified upload types for the Covenantrix application
// Consolidated interfaces with reduced complexity

export interface FileItem {
  id: string
  file: File
  filename: string
  documentId?: string
  status: 'pending' | 'uploading' | 'processing' | 'completed' | 'failed' | 'paused' | 'queued'
  progress?: number
  error?: string
  stage?: DocumentProgressStage
  stageMessage?: string
  source: 'local' | 'drive'
  sourceAccount?: string
  driveAccountId?: string
  driveFileId?: string
  priority?: number
  retryCount?: number
  maxRetries?: number
  createdAt: number
  updatedAt: number
}

// Document progress stages from backend
export type DocumentProgressStage = 
  | 'uploading'
  | 'processing'
  | 'ocr'
  | 'analysis'
  | 'completed'
  | 'failed'

// Simplified UploadProgress interface
export interface UploadProgress {
  total: number
  completed: number
  failed: number
  current?: string
  files: FileItem[]
  overallProgress: number
}

// Simplified UploadQueue interface
export interface UploadQueue {
  pending: FileItem[]
  uploading: FileItem[]
  processing: FileItem[]
  completed: FileItem[]
  failed: FileItem[]
  paused: FileItem[]
}

// Simplified UploadStats interface
export interface UploadStats {
  startTime: number
  totalFiles: number
  completedFiles: number
  failedFiles: number
  totalSize: number
  uploadedSize: number
  averageSpeed: number
  estimatedTimeRemaining: number
}

// Simplified UploadProgressProps (unified component)
export interface UploadProgressProps {
  progress: UploadProgress
  stats: UploadStats
  queue: UploadQueue
  onPauseUpload: () => void
  onResumeUpload: () => void
  onPauseFile: (fileId: string) => void
  onResumeFile: (fileId: string) => void
  onRetryFile: (fileId: string) => void
  onRemoveFile?: (fileId: string) => void
  onSetPriority?: (fileId: string, priority: number) => void
  disabled?: boolean
}
