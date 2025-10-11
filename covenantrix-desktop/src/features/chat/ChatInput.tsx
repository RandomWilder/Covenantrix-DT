import React, { useState, useRef } from 'react'
import { Send, Loader2 } from '../../components/icons'
import { detectTextDirection } from '../../utils/textDirection'

interface ChatInputProps {
  onSubmit: (message: string) => void
  disabled: boolean
}

export const ChatInput: React.FC<ChatInputProps> = ({ onSubmit, disabled }) => {
  const [inputValue, setInputValue] = useState('')
  const [textDirection, setTextDirection] = useState<'rtl' | 'ltr'>('ltr')
  const inputRef = useRef<HTMLTextAreaElement>(null)

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value
    setInputValue(value)
    
    // Detect and update text direction
    const direction = detectTextDirection(value)
    setTextDirection(direction)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!inputValue.trim() || disabled) return

    const message = inputValue.trim()
    onSubmit(message)
    setInputValue('')
    setTextDirection('ltr') // Reset direction after submit
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  const handleInput = (e: React.FormEvent<HTMLTextAreaElement>) => {
    const target = e.target as HTMLTextAreaElement
    target.style.height = 'auto'
    target.style.height = `${Math.min(target.scrollHeight, 120)}px`
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-3">
      <div className="flex-1 relative">
        <textarea
          ref={inputRef}
          value={inputValue}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onInput={handleInput}
          dir={textDirection}
          placeholder="Type your message... (Shift+Enter for new line)"
          className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
          rows={1}
          style={{
            minHeight: '48px',
            maxHeight: '120px',
            height: 'auto'
          }}
          disabled={disabled}
        />
      </div>
      
      <button
        type="submit"
        disabled={!inputValue.trim() || disabled}
        className="px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
      >
        {disabled ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : (
          <Send className="w-4 h-4" />
        )}
      </button>
    </form>
  )
}

