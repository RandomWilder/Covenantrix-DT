/**
 * Utility functions for detecting text direction (RTL/LTR)
 */

/**
 * Checks if a character is from an RTL language (Hebrew or Arabic)
 * @param char - Single character to check
 * @returns true if character is RTL, false otherwise
 */
export function isRTLCharacter(char: string): boolean {
  if (!char || char.length === 0) return false
  
  const code = char.charCodeAt(0)
  
  // Hebrew: U+0590 to U+05FF
  if (code >= 0x0590 && code <= 0x05FF) return true
  
  // Arabic: U+0600 to U+06FF
  if (code >= 0x0600 && code <= 0x06FF) return true
  
  // Arabic Supplement: U+0750 to U+077F
  if (code >= 0x0750 && code <= 0x077F) return true
  
  // Arabic Extended-A: U+08A0 to U+08FF
  if (code >= 0x08A0 && code <= 0x08FF) return true
  
  return false
}

/**
 * Detects text direction based on the first non-whitespace character
 * @param text - Text to analyze
 * @returns 'rtl' for right-to-left languages, 'ltr' for left-to-right
 */
export function detectTextDirection(text: string): 'rtl' | 'ltr' {
  if (!text || text.trim().length === 0) return 'ltr'
  
  // Find first non-whitespace character
  const trimmedText = text.trim()
  const firstChar = trimmedText[0]
  
  return isRTLCharacter(firstChar) ? 'rtl' : 'ltr'
}

