import React from 'react'
import { Wifi, Battery, Clock, User } from 'lucide-react'

interface StatusBarProps {
  onProfileClick?: () => void;
}

const StatusBar: React.FC<StatusBarProps> = ({ onProfileClick }) => {
  const currentTime = new Date().toLocaleTimeString([], { 
    hour: '2-digit', 
    minute: '2-digit' 
  })

  return (
    <div className="status-bar flex items-center justify-between px-4 text-sm text-gray-600 dark:text-gray-400">
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-1">
          <Wifi className="w-4 h-4" />
          <span>Connected</span>
        </div>
        <div className="flex items-center space-x-1">
          <Battery className="w-4 h-4" />
          <span>100%</span>
        </div>
      </div>

      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-1">
          <Clock className="w-4 h-4" />
          <span>{currentTime}</span>
        </div>
        <div className="text-xs">
          Covenantrix v1.1.65
        </div>
        <button
          onClick={onProfileClick}
          className="p-1.5 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
          title="Profile & Settings"
        >
          <User className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}

export default StatusBar
