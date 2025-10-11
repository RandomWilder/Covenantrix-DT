import React from 'react'
import { 
  Home, 
  FileText, 
  MessageSquare, 
  BarChart3, 
  Settings, 
  Upload,
  FolderOpen,
  History
} from 'lucide-react'

interface SidebarProps {
  className?: string
  onNavigate?: (screen: string) => void
  activeScreen?: string
}

const Sidebar: React.FC<SidebarProps> = ({ 
  className = '', 
  onNavigate,
  activeScreen = 'dashboard'
}) => {
  const navigationItems = [
    { icon: Home, label: 'Dashboard', screen: 'dashboard' },
    { icon: FileText, label: 'Documents', screen: 'documents' },
    { icon: MessageSquare, label: 'Chat', screen: 'chat' },
    { icon: BarChart3, label: 'Analytics', screen: 'analytics' },
    { icon: Upload, label: 'Upload', screen: 'upload' },
    { icon: FolderOpen, label: 'Library', screen: 'library' },
    { icon: History, label: 'History', screen: 'history' },
  ]

  const bottomItems = [
    { icon: Settings, label: 'Settings', active: false },
  ]

  return (
    <aside className={`sidebar flex flex-col ${className}`}>
      <div className="p-6">
        <h2 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-4">
          Navigation
        </h2>
        <nav className="space-y-1">
          {navigationItems.map((item) => {
            const Icon = item.icon
            const isActive = activeScreen === item.screen
            return (
              <button
                key={item.label}
                onClick={() => onNavigate?.(item.screen)}
                className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-left transition-colors ${
                  isActive
                    ? 'bg-primary text-primary-foreground'
                    : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                }`}
              >
                <Icon className="w-5 h-5" />
                <span className="font-medium">{item.label}</span>
              </button>
            )
          })}
        </nav>
      </div>

      <div className="flex-1" />

      <div className="p-6 border-t border-gray-200 dark:border-gray-700">
        <nav className="space-y-1">
          {bottomItems.map((item) => {
            const Icon = item.icon
            return (
              <button
                key={item.label}
                className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-left transition-colors ${
                  item.active
                    ? 'bg-primary text-primary-foreground'
                    : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                }`}
              >
                <Icon className="w-5 h-5" />
                <span className="font-medium">{item.label}</span>
              </button>
            )
          })}
        </nav>
      </div>
    </aside>
  )
}

export default Sidebar
