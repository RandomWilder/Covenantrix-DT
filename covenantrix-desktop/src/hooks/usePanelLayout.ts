import { useState, useEffect, useCallback } from 'react'

export interface PanelLayout {
  leftWidth: number      // 10-30%
  rightWidth: number      // 10-30%
  leftCollapsed: boolean
  rightCollapsed: boolean
  centerWidth: number     // Calculated: 100 - leftWidth - rightWidth
}

const STORAGE_KEY = 'chat-panel-layout'
const MIN_PANEL_WIDTH = 10
const MAX_PANEL_WIDTH = 30
const DEFAULT_LEFT_WIDTH = 20
const DEFAULT_RIGHT_WIDTH = 20

const getDefaultLayout = (): PanelLayout => ({
  leftWidth: DEFAULT_LEFT_WIDTH,
  rightWidth: DEFAULT_RIGHT_WIDTH,
  leftCollapsed: false,
  rightCollapsed: false,
  centerWidth: 60 // 100 - 20 - 20
})

const calculateCenterWidth = (leftWidth: number, rightWidth: number, leftCollapsed: boolean, rightCollapsed: boolean): number => {
  let centerWidth = 100
  if (!leftCollapsed) centerWidth -= leftWidth
  if (!rightCollapsed) centerWidth -= rightWidth
  return Math.max(40, centerWidth) // Ensure center is at least 40%
}

export const usePanelLayout = () => {
  const [layout, setLayout] = useState<PanelLayout>(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        const parsed = JSON.parse(stored)
        const centerWidth = calculateCenterWidth(
          parsed.leftWidth || DEFAULT_LEFT_WIDTH,
          parsed.rightWidth || DEFAULT_RIGHT_WIDTH,
          parsed.leftCollapsed || false,
          parsed.rightCollapsed || false
        )
        return {
          leftWidth: parsed.leftWidth || DEFAULT_LEFT_WIDTH,
          rightWidth: parsed.rightWidth || DEFAULT_RIGHT_WIDTH,
          leftCollapsed: parsed.leftCollapsed || false,
          rightCollapsed: parsed.rightCollapsed || false,
          centerWidth
        }
      }
    } catch (error) {
      console.warn('Failed to load panel layout from localStorage:', error)
    }
    return getDefaultLayout()
  })

  // Save to localStorage whenever layout changes
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({
        leftWidth: layout.leftWidth,
        rightWidth: layout.rightWidth,
        leftCollapsed: layout.leftCollapsed,
        rightCollapsed: layout.rightCollapsed
      }))
    } catch (error) {
      console.warn('Failed to save panel layout to localStorage:', error)
    }
  }, [layout])

  const updateLayout = useCallback((updates: Partial<PanelLayout>) => {
    setLayout(prev => {
      const newLayout = { ...prev, ...updates }
      
      // Recalculate center width
      newLayout.centerWidth = calculateCenterWidth(
        newLayout.leftWidth,
        newLayout.rightWidth,
        newLayout.leftCollapsed,
        newLayout.rightCollapsed
      )
      
      return newLayout
    })
  }, [])

  const resizeLeftPanel = useCallback((newWidth: number) => {
    const clampedWidth = Math.max(MIN_PANEL_WIDTH, Math.min(MAX_PANEL_WIDTH, newWidth))
    updateLayout({ leftWidth: clampedWidth })
  }, [updateLayout])

  const resizeRightPanel = useCallback((newWidth: number) => {
    const clampedWidth = Math.max(MIN_PANEL_WIDTH, Math.min(MAX_PANEL_WIDTH, newWidth))
    updateLayout({ rightWidth: clampedWidth })
  }, [updateLayout])

  const toggleLeftPanel = useCallback(() => {
    updateLayout({ leftCollapsed: !layout.leftCollapsed })
  }, [layout.leftCollapsed, updateLayout])

  const toggleRightPanel = useCallback(() => {
    updateLayout({ rightCollapsed: !layout.rightCollapsed })
  }, [layout.rightCollapsed, updateLayout])

  const resetLayout = useCallback(() => {
    setLayout(getDefaultLayout())
  }, [])

  return {
    layout,
    resizeLeftPanel,
    resizeRightPanel,
    toggleLeftPanel,
    toggleRightPanel,
    resetLayout
  }
}
