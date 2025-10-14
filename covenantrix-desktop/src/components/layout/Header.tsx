import React, { useState } from 'react'
import { Search, Settings, Bell, User } from 'lucide-react'
import SettingsModal from '../../features/settings/SettingsModal'
import { NotificationModal } from '../../features/notifications/NotificationModal'
import { useNotifications } from '../../contexts/NotificationContext'

interface HeaderProps {
  onProfileClick?: () => void
}

const Header: React.FC<HeaderProps> = ({ onProfileClick }) => {
  const [isSettingsOpen, setIsSettingsOpen] = useState(false)
  const [isNotificationModalOpen, setIsNotificationModalOpen] = useState(false)
  const { unreadCount } = useNotifications()
  
  const handleSettingsClick = () => {
    setIsSettingsOpen(true);
  };
  
  return (
    <header className="header flex items-center justify-between px-6 drag-region">
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
            <span className="text-primary-foreground font-bold text-sm">C</span>
          </div>
          <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
            Covenantrix
          </h1>
        </div>
      </div>

      <div className="flex-1 max-w-2xl mx-8">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <input
            type="text"
            placeholder="Search documents, ask questions..."
            className="w-full pl-10 pr-4 py-2 bg-gray-100 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
          />
        </div>
      </div>

      <div className="flex items-center space-x-4">
        <button 
          onClick={() => setIsNotificationModalOpen(true)}
          className="relative p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors no-drag"
        >
          <Bell className="w-5 h-5" />
          {unreadCount > 0 && (
            <span className="absolute top-1 right-1 flex h-4 w-4 items-center justify-center">
              <span className="absolute inline-flex h-full w-full rounded-full bg-red-500 opacity-75 animate-ping"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500 border border-white dark:border-gray-900"></span>
            </span>
          )}
        </button>
        <button 
          onClick={handleSettingsClick}
          className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors no-drag"
        >
          <Settings className="w-5 h-5" />
        </button>
        <button 
          onClick={onProfileClick}
          className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors no-drag"
        >
          <User className="w-5 h-5" />
        </button>
      </div>
      
      <SettingsModal 
        isOpen={isSettingsOpen} 
        onClose={() => setIsSettingsOpen(false)} 
      />
      
      <NotificationModal
        isOpen={isNotificationModalOpen}
        onClose={() => setIsNotificationModalOpen(false)}
      />
    </header>
  )
}

export default Header
