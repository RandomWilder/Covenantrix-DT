/**
 * SummaryProgressBar Component
 * Displays progress during summary generation
 */

import React from 'react'
import { Loader2 } from 'lucide-react'

interface SummaryProgressBarProps {
  progress: number
  stage: string
  message: string
  currentBatch?: number
  totalBatches?: number
}

const SummaryProgressBar: React.FC<SummaryProgressBarProps> = ({
  progress,
  stage,
  message,
  currentBatch,
  totalBatches
}) => {
  // Map backend stages to user-friendly messages
  const getStageMessage = () => {
    switch (stage) {
      case 'initializing':
        return 'Preparing document...'
      case 'batch_processing':
        return currentBatch && totalBatches
          ? `Analyzing sections... (${currentBatch}/${totalBatches})`
          : 'Analyzing sections...'
      case 'section_merging':
        return 'Organizing information...'
      case 'finalizing':
        return 'Creating final summary...'
      case 'completed':
        return 'Summary ready!'
      case 'failed':
        return 'Summary generation failed'
      default:
        return message
    }
  }

  return (
    <div className="space-y-2">
      {/* Progress Bar */}
      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 overflow-hidden">
        <div
          className="bg-indigo-600 h-full transition-all duration-300 ease-out"
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* Status Message */}
      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center space-x-2 text-gray-700 dark:text-gray-300">
          <Loader2 className="w-4 h-4 animate-spin" />
          <span>{getStageMessage()}</span>
        </div>
        <span className="text-gray-500 dark:text-gray-400 font-medium">
          {progress}%
        </span>
      </div>
    </div>
  )
}

export default SummaryProgressBar

