import React from 'react'
import { usePanelLayout } from '../../hooks/usePanelLayout'
import { useTheme } from '../../hooks/useTheme'
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

  return (
    <div className={`h-full flex flex-col ${effectiveTheme === 'dark' ? 'bg-gray-900' : 'bg-gray-100'}`}>
      <ChatTopBar 
        onToggleLeft={toggleLeftPanel}
        onToggleRight={toggleRightPanel}
        onReset={resetLayout}
        leftCollapsed={layout.leftCollapsed}
        rightCollapsed={layout.rightCollapsed}
      />
      
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
        <ChatPanel width={layout.centerWidth} />
        
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
