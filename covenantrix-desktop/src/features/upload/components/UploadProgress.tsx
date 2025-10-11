import React from 'react'
import { CheckCircle, XCircle, Clock, Upload, FileText, Sparkles, Network } from 'lucide-react'
import { DocumentProgressStage, UploadProgress as UploadProgressType } from '../../../types/document'

interface UploadProgressProps {
  progress: UploadProgressType
}

const UploadProgress: React.FC<UploadProgressProps> = ({ progress }) => {
  const { total, completed, failed, current, files } = progress
  const overallProgress = total > 0 ? ((completed + failed) / total) * 100 : 0

  const getStageIcon = (stage?: DocumentProgressStage) => {
    switch (stage) {
      case 'initializing':
        return <Clock className="w-4 h-4 text-blue-500 animate-pulse" />
      case 'reading':
        return <FileText className="w-4 h-4 text-blue-500 animate-pulse" />
      case 'understanding':
        return <Sparkles className="w-4 h-4 text-purple-500 animate-pulse" />
      case 'building_connections':
        return <Network className="w-4 h-4 text-indigo-500 animate-pulse" />
      case 'finalizing':
        return <CheckCircle className="w-4 h-4 text-blue-500 animate-pulse" />
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-500" />
      default:
        return <Clock className="w-4 h-4 text-gray-400" />
    }
  }

  const getStatusIcon = (status: string, stage?: DocumentProgressStage) => {
    // Use stage-specific icon if available
    if (stage) {
      return getStageIcon(stage)
    }
    
    // Fallback to status icon
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-500" />
      case 'uploading':
      case 'processing':
        return <Upload className="w-4 h-4 text-blue-500 animate-pulse" />
      default:
        return <Clock className="w-4 h-4 text-gray-400" />
    }
  }

  const getStatusText = (status: string, stageMessage?: string) => {
    // Use stage message if available
    if (stageMessage) {
      return stageMessage
    }
    
    // Fallback to status text
    switch (status) {
      case 'pending':
        return 'Waiting...'
      case 'uploading':
        return 'Uploading...'
      case 'processing':
        return 'Processing...'
      case 'completed':
        return 'Completed'
      case 'failed':
        return 'Failed'
      default:
        return 'Unknown'
    }
  }

  const getStatusColor = (status: string) => {
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

  return (
    <div className="space-y-4">
      {/* Overall Progress */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Upload Progress
          </h3>
          <span className="text-sm text-gray-600 dark:text-gray-400">
            {completed + failed} of {total} files
          </span>
        </div>
        
        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
          <div
            className="bg-primary h-2 rounded-full transition-all duration-300"
            style={{ width: `${overallProgress}%` }}
          />
        </div>
        
        <div className="flex items-center justify-between mt-2 text-sm">
          <span className="text-gray-600 dark:text-gray-400">
            {completed} completed, {failed} failed
          </span>
          <span className="text-gray-500 dark:text-gray-500">
            {Math.round(overallProgress)}%
          </span>
        </div>
      </div>

      {/* Current File */}
      {current && (
        <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
          <div className="flex items-center space-x-2">
            <Upload className="w-4 h-4 text-blue-500 animate-pulse" />
            <span className="text-sm font-medium text-blue-900 dark:text-blue-100">
              {current}
            </span>
          </div>
        </div>
      )}

      {/* File List */}
      <div className="space-y-2">
        <h4 className="text-sm font-medium text-gray-900 dark:text-white">
          File Status
        </h4>
        <div className="max-h-48 overflow-y-auto space-y-1">
          {files.map((file) => (
            <div
              key={file.id}
              className="flex items-start space-x-3 p-2 bg-gray-50 dark:bg-gray-800 rounded-lg"
            >
              {getStatusIcon(file.status || 'pending', file.stage)}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                  {file.file.name}
                </p>
                <div className="flex items-center space-x-2">
                  <span className={`text-xs ${getStatusColor(file.status || 'pending')}`}>
                    {getStatusText(file.status || 'pending', file.stageMessage)}
                  </span>
                  {file.progress !== undefined && !['completed', 'failed', 'pending'].includes(file.status || 'pending') && (
                    <span className="text-xs text-gray-500">
                      {Math.round(file.progress)}%
                    </span>
                  )}
                </div>
                
                {/* Stage progress bar */}
                {file.stage && !['completed', 'failed', 'pending'].includes(file.stage) && file.progress !== undefined && (
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1 mt-1">
                    <div 
                      className="bg-blue-500 h-1 rounded-full transition-all duration-300"
                      style={{ width: `${file.progress}%` }}
                    />
                  </div>
                )}
                
                {file.error && (
                  <p className="text-xs text-red-600 dark:text-red-400 mt-1">
                    {file.error}
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default UploadProgress
