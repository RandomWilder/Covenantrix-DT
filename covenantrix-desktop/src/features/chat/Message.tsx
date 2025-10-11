import React from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Message as MessageType } from '../../types/chat'
import { Bot, User, Loader2 } from '../../components/icons'
import { detectTextDirection } from '../../utils/textDirection'

interface MessageProps {
  message: MessageType
  isStreaming?: boolean
}

export const Message: React.FC<MessageProps> = ({ message, isStreaming = false }) => {
  // Detect text direction for the message content
  const textDirection = detectTextDirection(message.content)
  
  const formatTime = (timestamp: string) => {
    try {
      return new Date(timestamp).toLocaleTimeString([], { 
        hour: '2-digit', 
        minute: '2-digit' 
      })
    } catch {
      return ''
    }
  }

  return (
    <div
      className={`flex gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
    >
      {message.role === 'assistant' && (
        <div className="flex-shrink-0 w-8 h-8 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center">
          <Bot className="w-4 h-4 text-blue-600 dark:text-blue-400" />
        </div>
      )}
      
      <div className={`max-w-[80%] ${message.role === 'user' ? 'order-first' : ''}`}>
        <div
          className={`px-4 py-3 rounded-lg ${
            message.role === 'user'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white'
          }`}
          dir={textDirection}
        >
          {message.isError ? (
            <div className="text-red-600 dark:text-red-400">{message.content}</div>
          ) : message.role === 'user' ? (
            <div className="whitespace-pre-wrap">{message.content}</div>
          ) : (message.isStreaming || isStreaming) && !message.content ? (
            <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Thinking...</span>
            </div>
          ) : (
            <>
              <ReactMarkdown 
                className="markdown-content"
                remarkPlugins={[remarkGfm]}
              >
                {message.content}
              </ReactMarkdown>
              {(message.isStreaming || isStreaming) && (
                <span className="inline-block w-2 h-4 ml-1 bg-blue-600 animate-pulse" />
              )}
            </>
          )}
        </div>
        
        {!message.isStreaming && !isStreaming && message.sources && message.sources.length > 0 && (
          <div className="mt-2 space-y-1">
            {message.sources.map((source, index) => (
              <div
                key={index}
                className="text-xs text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 px-2 py-1 rounded border-l-2 border-blue-200 dark:border-blue-600"
              >
                <span className="font-medium">{source.document_name}</span>
                {source.page_number && <span> (Page {source.page_number})</span>}
                {source.excerpt && (
                  <div className="mt-1 text-gray-400 dark:text-gray-500 truncate">
                    {source.excerpt}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
        
        <div className="text-xs text-gray-400 dark:text-gray-500 mt-1">
          {formatTime(message.timestamp)}
        </div>
      </div>
      
      {message.role === 'user' && (
        <div className="flex-shrink-0 w-8 h-8 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center">
          <User className="w-4 h-4 text-gray-600 dark:text-gray-400" />
        </div>
      )}
    </div>
  )
}

