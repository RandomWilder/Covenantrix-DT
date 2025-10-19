// Simplified error handling utilities for the Covenantrix application
// Provides basic error handling without over-engineering

export const getErrorMessage = (error: Error, fallback: string = 'An error occurred'): string => {
  if (error.message) {
    return error.message
  }
  
  if (error.name) {
    return `${error.name}: ${fallback}`
  }
  
  return fallback
}

export const isRetryableError = (error: Error): boolean => {
  const retryablePatterns = [
    'network',
    'timeout',
    'connection',
    'fetch',
    'ECONNRESET',
    'ENOTFOUND',
    'ETIMEDOUT'
  ]
  
  const errorMessage = error.message.toLowerCase()
  return retryablePatterns.some(pattern => errorMessage.includes(pattern))
}

export const getRetryDelay = (retryCount: number, baseDelay: number = 1000): number => {
  // Exponential backoff with jitter
  const exponentialDelay = baseDelay * Math.pow(2, retryCount)
  const jitter = Math.random() * 0.1 * exponentialDelay
  return Math.min(exponentialDelay + jitter, 30000) // Cap at 30 seconds
}

export const formatErrorForUser = (error: Error): string => {
  let message = getErrorMessage(error, 'An unexpected error occurred')
  
  // Add basic context based on error type
  if (error.message.includes('network') || error.message.includes('fetch')) {
    message += ' - Check your internet connection'
  } else if (error.message.includes('timeout')) {
    message += ' - The request timed out'
  } else if (error.message.includes('size') || error.message.includes('too large')) {
    message += ' - File size exceeds the limit'
  } else if (error.message.includes('quota') || error.message.includes('limit')) {
    message += ' - Upload limit reached'
  }
  
  return message
}

export const logError = (error: Error, context?: string): void => {
  console.error('Error occurred:', {
    message: error.message,
    stack: error.stack,
    name: error.name,
    context
  })
}
