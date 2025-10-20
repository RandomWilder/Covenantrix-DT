/**
 * Centralized date utility functions for consistent timestamp handling
 * All timestamps from backend are in UTC and need to be converted to local time
 */

/**
 * Format a UTC timestamp to local time string
 * @param timestamp - ISO string timestamp from backend
 * @param options - Intl.DateTimeFormatOptions for formatting
 * @returns Formatted time string
 */
export const formatTimestamp = (timestamp: string, options?: Intl.DateTimeFormatOptions): string => {
  try {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], options || { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  } catch {
    return '';
  }
};

/**
 * Format a UTC timestamp to relative time string (e.g., "2h ago", "just now")
 * @param timestamp - ISO string timestamp from backend
 * @returns Relative time string
 */
export const formatRelativeTime = (timestamp: string): string => {
  try {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  } catch {
    return 'Unknown';
  }
};

/**
 * Format a UTC timestamp to local date string
 * @param timestamp - ISO string timestamp from backend (can be null/undefined)
 * @param options - Intl.DateTimeFormatOptions for formatting
 * @returns Formatted date string
 */
export const formatDate = (timestamp: string | null | undefined, options?: Intl.DateTimeFormatOptions): string => {
  if (!timestamp) return 'Not processed';
  
  try {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    // Show relative dates for recent items
    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
    
    // For older dates, show formatted date
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined,
      ...options
    });
  } catch {
    return 'Unknown';
  }
};

/**
 * Format a UTC timestamp to local date and time string
 * @param timestamp - ISO string timestamp from backend
 * @param options - Intl.DateTimeFormatOptions for formatting
 * @returns Formatted date and time string
 */
export const formatDateTime = (timestamp: string, options?: Intl.DateTimeFormatOptions): string => {
  try {
    const date = new Date(timestamp);
    return date.toLocaleString([], {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      ...options
    });
  } catch {
    return 'Unknown';
  }
};

/**
 * Get relative time for Google account connections
 * @param timestamp - ISO string timestamp from backend
 * @returns Relative time string with proper pluralization
 */
export const getRelativeTime = (timestamp: string): string => {
  try {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes} min ago`;
    if (hours < 24) return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    if (days < 30) return `${days} day${days > 1 ? 's' : ''} ago`;
    return formatDate(timestamp);
  } catch {
    return 'Unknown';
  }
};

/**
 * Format file dates for Google Drive items
 * @param dateString - ISO string timestamp from backend
 * @returns Formatted date string for file listings
 */
export const formatFileDate = (dateString?: string): string => {
  if (!dateString) return '';
  
  try {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
    
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
    });
  } catch {
    return dateString;
  }
};

/**
 * Create a new ISO timestamp string in UTC
 * @returns ISO string timestamp
 */
export const createTimestamp = (): string => {
  return new Date().toISOString();
};
