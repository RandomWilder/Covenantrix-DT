import React from 'react'
import { usePanelLayout } from '../../hooks/usePanelLayout'
import { useTheme } from '../../hooks/useTheme'
import { useServiceStatus } from '../../hooks/useServiceStatus'
import { Resizer } from '../../components/ui/Resizer'
import { PanelLeft, PanelRight, Reset } from '../../components/icons'
import { HistoryPanel } from './HistoryPanel'
import { ChatPanel } from './ChatPanel'
import { ContextPanel } from './ContextPanel'

const ChatTopBar: React.FC<{
  onToggleLeft: () => void
  onToggleRight: () => void
  onReset: () => void
  leftCollapsed: boolean
  rightCollapsed: boolean
}> = ({ onToggleLeft, onToggleRight, onReset, leftCollapsed, rightCollapsed }) => (
  <div className="h-12 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between px-4">
    <h1 className="text-lg font-semibold text-gray-900 dark:text-white">AI Assistant</h1>
    
    {/* Panel Control Buttons */}
    <div className="flex items-center gap-2">
      <button
        onClick={onToggleLeft}
        className="p-1.5 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors"
        title={leftCollapsed ? 'Show History Panel' : 'Hide History Panel'}
      >
        <PanelLeft className="w-4 h-4" />
      </button>
      <button
        onClick={onToggleRight}
        className="p-1.5 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors"
        title={rightCollapsed ? 'Show Context Panel' : 'Hide Context Panel'}
      >
        <PanelRight className="w-4 h-4" />
      </button>
      <button
        onClick={onReset}
        className="p-1.5 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors"
        title="Reset Panel Layout"
      >
        <Reset className="w-4 h-4" />
      </button>
    </div>
  </div>
)

export const ChatScreen: React.FC = () => {
  const {
    layout,
    resizeLeftPanel,
    resizeRightPanel,
    toggleLeftPanel,
    toggleRightPanel,
    resetLayout
  } = usePanelLayout()
  const { effectiveTheme } = useTheme()
  const { features, isLoading } = useServiceStatus()
  
  const chatAvailable = features.chat

  const handleLeftResize = (deltaX: number) => {
    const deltaPercent = (deltaX / window.innerWidth) * 100
    const newWidth = layout.leftWidth + deltaPercent
    resizeLeftPanel(newWidth)
  }

  const handleRightResize = (deltaX: number) => {
    const deltaPercent = (deltaX / window.innerWidth) * 100
    const newWidth = layout.rightWidth - deltaPercent
    resizeRightPanel(newWidth)
  }

  const handleGoToSettings = () => {
    // TODO: Implement navigation to settings modal
    console.log('Navigate to settings')
  }

  return (
    <div className={`h-full flex flex-col ${effectiveTheme === 'dark' ? 'bg-gray-900' : 'bg-gray-100'}`}>
      <ChatTopBar 
        onToggleLeft={toggleLeftPanel}
        onToggleRight={toggleRightPanel}
        onReset={resetLayout}
        leftCollapsed={layout.leftCollapsed}
        rightCollapsed={layout.rightCollapsed}
      />
      
      {/* Chat Feature Guard Banner */}
      {!isLoading && !chatAvailable && (
        <div className="bg-yellow-50 dark:bg-yellow-900/20 border-b border-yellow-200 dark:border-yellow-800 px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <svg className="w-5 h-5 text-yellow-600 dark:text-yellow-500" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              <div>
                <p className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
                  ⚠️ Chat Disabled
                </p>
                <p className="text-xs text-yellow-700 dark:text-yellow-300 mt-0.5">
                  OpenAI API key not configured. Configure your API key in Settings → API Keys to enable chat.
                </p>
              </div>
            </div>
            <button
              onClick={handleGoToSettings}
              className="px-3 py-1.5 text-sm font-medium text-yellow-800 dark:text-yellow-200 bg-yellow-100 dark:bg-yellow-800/30 hover:bg-yellow-200 dark:hover:bg-yellow-700/30 rounded transition-colors"
            >
              Go to Settings
            </button>
          </div>
        </div>
      )}
      
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel - History */}
        <HistoryPanel 
          width={layout.leftWidth} 
          collapsed={layout.leftCollapsed} 
        />
        
        {/* Left Resizer */}
        {!layout.leftCollapsed && (
          <Resizer 
            onResize={handleLeftResize}
            onDoubleClick={toggleLeftPanel}
            className="bg-gray-300 dark:bg-gray-600 hover:bg-gray-400 dark:hover:bg-gray-500"
          />
        )}
        
        {/* Center Panel - Chat */}
        <ChatPanel width={layout.centerWidth} disabled={!chatAvailable} />
        
        {/* Right Resizer */}
        {!layout.rightCollapsed && (
          <Resizer 
            onResize={handleRightResize}
            onDoubleClick={toggleRightPanel}
            className="bg-gray-300 dark:bg-gray-600 hover:bg-gray-400 dark:hover:bg-gray-500"
          />
        )}
        
        {/* Right Panel - Context */}
        <ContextPanel 
          width={layout.rightWidth} 
          collapsed={layout.rightCollapsed} 
        />
      </div>
    </div>
  )
}
