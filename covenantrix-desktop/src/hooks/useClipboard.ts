import { useState, useEffect, useCallback } from 'react'

interface UseClipboardReturn {
  copied: boolean
  copyToClipboard: (text: string) => Promise<void>
  error: string | null
}

/**
 * Custom hook for copy-to-clipboard functionality with visual feedback
 * Uses the browser's native Clipboard API
 * 
 * @param resetTimeout - Time in milliseconds before resetting copied state (default: 2000ms)
 * @returns Object with copied state, copyToClipboard function, and error state
 */
export const useClipboard = (resetTimeout: number = 2000): UseClipboardReturn => {
  const [copied, setCopied] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Auto-reset copied state after timeout
  useEffect(() => {
    if (copied) {
      const timer = setTimeout(() => {
        setCopied(false)
      }, resetTimeout)

      return () => clearTimeout(timer)
    }
  }, [copied, resetTimeout])

  // Copy text to clipboard
  const copyToClipboard = useCallback(async (text: string) => {
    try {
      // Check if Clipboard API is available
      if (!navigator.clipboard) {
        throw new Error('Clipboard API not available')
      }

      // Write text to clipboard
      await navigator.clipboard.writeText(text)
      
      // Set success state
      setCopied(true)
      setError(null)
    } catch (err) {
      // Handle errors
      const errorMessage = err instanceof Error ? err.message : 'Failed to copy to clipboard'
      setError(errorMessage)
      console.error('Copy to clipboard failed:', err)
      
      // Reset error after timeout
      setTimeout(() => setError(null), resetTimeout)
    }
  }, [resetTimeout])

  return {
    copied,
    copyToClipboard,
    error
  }
}

