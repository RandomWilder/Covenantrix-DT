import React from 'react'
import { ChevronRight, Home } from 'lucide-react'

export interface BreadcrumbItem {
  id: string
  name: string
}

interface DriveBreadcrumbsProps {
  items: BreadcrumbItem[]
  onNavigate: (folderId: string | null) => void
  disabled?: boolean
}

const DriveBreadcrumbs: React.FC<DriveBreadcrumbsProps> = ({
  items,
  onNavigate,
  disabled = false
}) => {
  return (
    <div className="flex items-center space-x-1 overflow-x-auto">
      {/* Root / Home */}
      <button
        onClick={() => onNavigate(null)}
        disabled={disabled}
        className="flex items-center space-x-1 px-2 py-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        title="Go to root"
      >
        <Home className="w-4 h-4 text-gray-600 dark:text-gray-400" />
        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
          My Drive
        </span>
      </button>

      {/* Folder Path */}
      {items.map((item, index) => (
        <React.Fragment key={item.id}>
          <ChevronRight className="w-4 h-4 text-gray-400" />
          <button
            onClick={() => onNavigate(item.id)}
            disabled={disabled}
            className="px-2 py-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            title={item.name}
          >
            <span className={`text-sm ${
              index === items.length - 1
                ? 'font-medium text-gray-900 dark:text-white'
                : 'text-gray-600 dark:text-gray-400'
            }`}>
              {item.name}
            </span>
          </button>
        </React.Fragment>
      ))}
    </div>
  )
}

export default DriveBreadcrumbs

