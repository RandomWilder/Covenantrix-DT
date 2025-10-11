import React, { useRef, useCallback, useState } from 'react'

interface ResizerProps {
  onResize: (deltaX: number) => void
  onDoubleClick?: () => void
  className?: string
  orientation?: 'vertical' | 'horizontal'
}

export const Resizer: React.FC<ResizerProps> = ({
  onResize,
  onDoubleClick,
  className = '',
  orientation = 'vertical'
}) => {
  const [isDragging, setIsDragging] = useState(false)
  const [isHovering, setIsHovering] = useState(false)
  const startX = useRef<number>(0)
  const startY = useRef<number>(0)
  const isDraggingRef = useRef(false)

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!isDraggingRef.current) return
    
    const deltaX = e.clientX - startX.current
    const deltaY = e.clientY - startY.current
    
    if (orientation === 'vertical') {
      onResize(deltaX)
    } else {
      onResize(deltaY)
    }
  }, [onResize, orientation])

  const handleMouseUp = useCallback(() => {
    setIsDragging(false)
    isDraggingRef.current = false
    
    // Remove global mouse event listeners
    document.removeEventListener('mousemove', handleMouseMove)
    document.removeEventListener('mouseup', handleMouseUp)
    document.body.style.cursor = ''
    document.body.style.userSelect = ''
  }, [handleMouseMove])

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    setIsDragging(true)
    isDraggingRef.current = true
    startX.current = e.clientX
    startY.current = e.clientY
    
    // Add global mouse event listeners
    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)
    document.body.style.cursor = orientation === 'vertical' ? 'col-resize' : 'row-resize'
    document.body.style.userSelect = 'none'
  }, [orientation, handleMouseMove, handleMouseUp])

  const handleDoubleClick = useCallback(() => {
    if (onDoubleClick) {
      onDoubleClick()
    }
  }, [onDoubleClick])

  const baseClasses = `
    relative group transition-all duration-200
    ${orientation === 'vertical' ? 'w-1 h-full' : 'h-1 w-full'}
    ${isDragging ? 'bg-blue-500' : isHovering ? 'bg-gray-400' : 'bg-gray-300'}
    hover:bg-gray-400 cursor-${orientation === 'vertical' ? 'col' : 'row'}-resize
    ${className}
  `.trim()

  return (
    <div
      className={baseClasses}
      onMouseDown={handleMouseDown}
      onDoubleClick={handleDoubleClick}
      onMouseEnter={() => setIsHovering(true)}
      onMouseLeave={() => setIsHovering(false)}
      role="separator"
      aria-orientation={orientation}
      aria-label={`Resize ${orientation} panel`}
    >
      {/* Visual indicator */}
      <div className={`
        absolute inset-0 flex items-center justify-center
        ${orientation === 'vertical' ? 'flex-col' : 'flex-row'}
        opacity-0 group-hover:opacity-100 transition-opacity
      `}>
        <div className={`
          bg-white rounded-full shadow-sm
          ${orientation === 'vertical' ? 'w-1 h-6' : 'h-1 w-6'}
        `} />
      </div>
    </div>
  )
}
