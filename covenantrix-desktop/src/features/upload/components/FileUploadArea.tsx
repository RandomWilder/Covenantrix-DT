import React, { useCallback, useState } from 'react'
import { Upload } from 'lucide-react'

interface FileUploadAreaProps {
  onFilesSelected: (files: File[]) => void
  disabled?: boolean
}

const FileUploadArea: React.FC<FileUploadAreaProps> = ({
  onFilesSelected,
  disabled = false
}) => {
  const [isDragOver, setIsDragOver] = useState(false)

  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (!disabled) {
      setIsDragOver(true)
    }
  }, [disabled])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    
    // Only set isDragOver to false if we're leaving the component entirely
    const target = e.currentTarget as HTMLElement
    const relatedTarget = e.relatedTarget as HTMLElement
    
    if (!target.contains(relatedTarget)) {
      setIsDragOver(false)
    }
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(false)
    
    if (disabled) return

    const files = Array.from(e.dataTransfer.files)
    if (files.length > 0) {
      onFilesSelected(files)
    }
  }, [disabled, onFilesSelected])

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (disabled) return

    const files = Array.from(e.target.files || [])
    if (files.length > 0) {
      onFilesSelected(files)
    }
  }, [disabled, onFilesSelected])

  return (
    <div
      className={`relative border-2 border-dashed rounded-lg transition-colors ${
        isDragOver
          ? 'border-primary bg-primary/5'
          : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'
      } ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
      onDragEnter={handleDragEnter}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <div className="p-8 text-center">
        <div className="flex flex-col items-center space-y-4">
          <div className="p-4 bg-gray-100 dark:bg-gray-800 rounded-full">
            <Upload className="w-8 h-8 text-gray-600 dark:text-gray-400" />
          </div>
          
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Drop files here or click to browse
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mt-1">
              Support for PDF, DOCX, DOC, TXT, PNG, JPG, JPEG, TIFF, XLSX, XLS, PPTX, PPT, RTF, GIF, BMP
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-500 mt-1">
              Maximum 50MB per file, up to 10 files at once
            </p>
          </div>

          <input
            type="file"
            multiple
            accept=".pdf,.docx,.doc,.txt,.png,.jpg,.jpeg,.tiff,.xlsx,.xls,.pptx,.ppt,.rtf,.gif,.bmp"
            onChange={handleFileInput}
            disabled={disabled}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed"
          />
        </div>
      </div>

      {/* Drag overlay - pointer-events-none prevents blocking drop events */}
      {isDragOver && (
        <div className="absolute inset-0 bg-primary/10 border-2 border-primary border-dashed rounded-lg flex items-center justify-center pointer-events-none">
          <div className="text-center">
            <Upload className="w-12 h-12 text-primary mx-auto mb-2" />
            <p className="text-primary font-semibold">Drop files to upload</p>
          </div>
        </div>
      )}
    </div>
  )
}

export default FileUploadArea
