import React, { useState, useRef, useEffect } from 'react'
import { useChat } from '../../contexts/ChatContext'
import { useSubscription } from '../../contexts/SubscriptionContext'
import { useUpgradeModal } from '../../contexts/UpgradeModalContext'
import { Bot, Settings } from '../../components/icons'
import { ChatInput } from './ChatInput'
import { Message } from './Message'

interface ChatPanelProps {
  width: number
  disabled?: boolean
}

export const ChatPanel: React.FC<ChatPanelProps> = ({ width, disabled = false }) => {
  const { 
    activeConversation, 
    sendMessage, 
    selectedAgent,
    selectAgent,
    selectedDocuments
  } = useChat()
  
  const { subscription, canSendQuery, getRemainingQuota, refreshSubscription } = useSubscription()
  const { showUpgradeModal } = useUpgradeModal()
  
  const [isSubmitting, setIsSubmitting] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [activeConversation?.messages])

  const handleSubmit = async (message: string) => {
    if (isSubmitting) return

    // Check query limits before sending
    const allowed = await canSendQuery()
    if (!allowed) {
      const remaining = getRemainingQuota('queries')
      showUpgradeModal({
        title: 'Query Limit Reached',
        message: `You've used all your queries for the ${subscription?.tier} tier.`,
        currentTier: subscription?.tier,
        details: `Remaining queries: ${remaining}`
      })
      return
    }

    setIsSubmitting(true)

    try {
      await sendMessage(message, selectedDocuments)
      // Refresh subscription data after successful message send
      await refreshSubscription()
    } catch (error) {
      console.error('Failed to send message:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div 
      className="bg-white dark:bg-gray-800 h-full flex flex-col"
      style={{ width: `${width}%` }}
    >
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {activeConversation ? (
          activeConversation.messages.length > 0 ? (
            activeConversation.messages.map((message) => (
              <Message key={message.id} message={message} />
            ))
          ) : (
            <div className="flex-1 flex items-center justify-center text-gray-500 dark:text-gray-400">
              <div className="text-center">
                <Bot className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
                <p className="text-lg font-medium mb-2">Start a conversation</p>
                <p className="text-sm">Ask me anything about your documents or use an AI agent.</p>
              </div>
            </div>
          )
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-500 dark:text-gray-400">
            <div className="text-center">
              <Bot className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
              <p className="text-lg font-medium mb-2">No conversation selected</p>
              <p className="text-sm">Create a new conversation to get started.</p>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Agent Selector */}
      <div className="border-t border-gray-200 dark:border-gray-700 px-4 py-2 bg-gray-50 dark:bg-gray-800">
        <div className="flex items-center gap-2">
          <Settings className="w-4 h-4 text-gray-500 dark:text-gray-400" />
          <span className="text-sm text-gray-600 dark:text-gray-300">Agent:</span>
          <select
            value={selectedAgent || ''}
            onChange={(e) => selectAgent(e.target.value || null)}
            className="text-sm border border-gray-300 dark:border-gray-600 rounded px-2 py-1 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">General Assistant</option>
            <option value="market-research">Market Research</option>
            <option value="legal-analysis">Legal Analysis</option>
            <option value="financial-review">Financial Review</option>
          </select>
        </div>
      </div>

      {/* Input Area */}
      <div className="border-t border-gray-200 dark:border-gray-700 p-4">
        <ChatInput 
          onSubmit={handleSubmit} 
          disabled={isSubmitting || disabled} 
        />
      </div>
    </div>
  )
}
