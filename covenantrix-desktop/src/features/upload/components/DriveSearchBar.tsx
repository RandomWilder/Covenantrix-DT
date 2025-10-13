import React, { useState, useEffect } from 'react'
import { Search, X, Filter } from 'lucide-react'

interface DriveSearchBarProps {
  onSearch: (query: string) => void
  onFilterChange?: (mimeType: string | null) => void
  disabled?: boolean
  placeholder?: string
}

const DriveSearchBar: React.FC<DriveSearchBarProps> = ({
  onSearch,
  onFilterChange,
  disabled = false,
  placeholder = 'Search files...'
}) => {
  const [query, setQuery] = useState('')
  const [showFilters, setShowFilters] = useState(false)
  const [selectedFilter, setSelectedFilter] = useState<string | null>(null)

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      onSearch(query)
    }, 300)

    return () => clearTimeout(timer)
  }, [query, onSearch])

  const handleClear = () => {
    setQuery('')
    onSearch('')
  }

  const handleFilterSelect = (mimeType: string | null) => {
    setSelectedFilter(mimeType)
    if (onFilterChange) {
      onFilterChange(mimeType)
    }
    setShowFilters(false)
  }

  const filters = [
    { label: 'All Files', value: null },
    { label: 'Documents', value: 'application/pdf' },
    { label: 'Images', value: 'image/' },
    { label: 'Spreadsheets', value: 'application/vnd.google-apps.spreadsheet' }
  ]

  return (
    <div className="space-y-2">
      {/* Search Input */}
      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <Search className="w-5 h-5 text-gray-400" />
        </div>
        
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          disabled={disabled}
          placeholder={placeholder}
          className="w-full pl-10 pr-20 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
        />

        <div className="absolute inset-y-0 right-0 flex items-center space-x-1 pr-2">
          {/* Clear Button */}
          {query && (
            <button
              onClick={handleClear}
              disabled={disabled}
              className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded transition-colors"
              title="Clear search"
            >
              <X className="w-4 h-4" />
            </button>
          )}

          {/* Filter Button */}
          {onFilterChange && (
            <div className="relative">
              <button
                onClick={() => setShowFilters(!showFilters)}
                disabled={disabled}
                className={`p-1 rounded transition-colors ${
                  selectedFilter
                    ? 'text-primary'
                    : 'text-gray-400 hover:text-gray-600 dark:hover:text-gray-300'
                }`}
                title="Filter by type"
              >
                <Filter className="w-4 h-4" />
              </button>

              {/* Filter Dropdown */}
              {showFilters && (
                <>
                  <div
                    className="fixed inset-0 z-10"
                    onClick={() => setShowFilters(false)}
                  />
                  <div className="absolute right-0 top-full mt-2 w-48 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-20 overflow-hidden">
                    {filters.map((filter) => (
                      <button
                        key={filter.label}
                        onClick={() => handleFilterSelect(filter.value)}
                        className={`w-full text-left px-4 py-2 text-sm transition-colors ${
                          selectedFilter === filter.value
                            ? 'bg-primary/10 text-primary font-medium'
                            : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
                        }`}
                      >
                        {filter.label}
                      </button>
                    ))}
                  </div>
                </>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Active Filter Badge */}
      {selectedFilter && (
        <div className="flex items-center space-x-2">
          <span className="text-xs text-gray-600 dark:text-gray-400">
            Filter:
          </span>
          <button
            onClick={() => handleFilterSelect(null)}
            className="inline-flex items-center space-x-1 px-2 py-1 bg-primary/10 text-primary text-xs rounded-full hover:bg-primary/20 transition-colors"
          >
            <span>
              {filters.find(f => f.value === selectedFilter)?.label}
            </span>
            <X className="w-3 h-3" />
          </button>
        </div>
      )}
    </div>
  )
}

export default DriveSearchBar

