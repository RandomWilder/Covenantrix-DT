import React, { createContext, useContext, useState, useCallback, useEffect } from 'react'
import { 
  Conversation, 
  ConversationSummary,
  ChatContextValue, 
  ChatMessageRequest, 
  ChatMessageResponse,
  ConversationResponse
} from '../types/chat'
import { useToast } from '../hooks/useToast'
import { createTimestamp } from '../utils/dateUtils'
import { ChatApi } from '../services/api/ChatApi'

const ChatContext = createContext<ChatContextValue | undefined>(undefined)

export const useChat = () => {
  const context = useContext(ChatContext)
  if (!context) {
    throw new Error('useChat must be used within a ChatProvider')
  }
  return context
}

interface ChatProviderProps {
  children: React.ReactNode
}

export const ChatProvider: React.FC<ChatProviderProps> = ({ children }) => {
  const [activeConversation, setActiveConversation] = useState<Conversation | null>(null)
  const [conversations, setConversations] = useState<ConversationSummary[]>([])
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null)
  const [selectedDocuments, setSelectedDocuments] = useState<string[]>([])
  
  const { showToast } = useToast()
  const chatApi = new ChatApi()

  // Helper function to convert Conversation to ConversationSummary
  const conversationToSummary = (conv: Conversation): ConversationSummary => ({
    id: conv.id,
    title: conv.title,
    created_at: conv.created_at,
    updated_at: conv.updated_at,
    message_count: conv.messages.length,
    last_message_preview: conv.messages.length > 0 
      ? conv.messages[conv.messages.length - 1].content.slice(0, 100) + (conv.messages[conv.messages.length - 1].content.length > 100 ? '...' : '')
      : undefined
  })

  // Load conversations on mount
  useEffect(() => {
    loadConversations()
  }, [])

  const loadConversations = useCallback(async () => {
    try {
      const response = await chatApi.getConversations()
      setConversations(response.conversations)
    } catch (error) {
      console.error('Failed to load conversations:', error)
      showToast('Failed to load conversations', 'error')
    }
  }, [showToast])

  const sendMessage = useCallback(async (message: string, documentIds?: string[]) => {
    if (!message.trim()) return

    const userMessageId = `user-${Date.now()}`
    const assistantMessageId = `assistant-${Date.now()}`
    const timestamp = createTimestamp()
    
    // Create user message
    const userMessage = {
      id: userMessageId,
      role: 'user' as const,
      content: message.trim(),
      sources: [],
      timestamp
    }
    
    // Create placeholder assistant message (streaming)
    const placeholderAssistantMessage = {
      id: assistantMessageId,
      role: 'assistant' as const,
      content: '',
      sources: [],
      timestamp,
      isStreaming: true
    }
    
    // Optimistically add user message and placeholder assistant message immediately
    if (activeConversation) {
      const updatedConversation = {
        ...activeConversation,
        messages: [
          ...activeConversation.messages,
          userMessage,
          placeholderAssistantMessage
        ],
        updated_at: timestamp
      }
      setActiveConversation(updatedConversation)
    } else {
      // Create new conversation optimistically
      const newConversation: Conversation = {
        id: `temp-${Date.now()}`, // Temporary ID until we get the real one
        title: message.slice(0, 50) + (message.length > 50 ? '...' : ''),
        created_at: timestamp,
        updated_at: timestamp,
        messages: [userMessage, placeholderAssistantMessage]
      }
      setActiveConversation(newConversation)
    }
    
    try {
      const request: ChatMessageRequest = {
        conversation_id: activeConversation?.id?.startsWith('temp-') ? undefined : activeConversation?.id,
        message: message.trim(),
        agent_id: selectedAgent || undefined,
        document_ids: documentIds
      }

      // Try to use streaming, fall back to regular API if streaming fails
      let streamingSucceeded = false
      let accumulatedContent = ''
      let finalConversationId = ''
      let finalMessageId = ''
      let finalSources: any[] = []
      let finalTitle = ''

      try {
        // Use streaming API
        for await (const chunk of chatApi.sendMessageStream(request)) {
          if (chunk.token) {
            // Accumulate content
            accumulatedContent += chunk.token
            
            // Update the placeholder assistant message with accumulated content
            setActiveConversation(currentConversation => {
              if (!currentConversation) return null
              
              return {
                ...currentConversation,
                messages: currentConversation.messages.map((msg) => {
                  if (msg.id === assistantMessageId) {
                    return {
                      ...msg,
                      content: accumulatedContent,
                      isStreaming: true
                    }
                  }
                  return msg
                }),
                updated_at: createTimestamp()
              }
            })
          }
          
          if (chunk.done) {
            // Stream is complete
            streamingSucceeded = true
            finalConversationId = chunk.conversation_id || activeConversation?.id || ''
            finalMessageId = chunk.message_id || assistantMessageId
            finalSources = chunk.sources || []
            finalTitle = chunk.conversation_title || activeConversation?.title || ''
            break
          }
        }
      } catch (streamError) {
        console.error('Streaming failed, falling back to regular API:', streamError)
        
        // Fall back to non-streaming API
        const response: ChatMessageResponse = await chatApi.sendMessage(request)
        accumulatedContent = response.response
        finalConversationId = response.conversation_id
        finalMessageId = response.message_id
        finalSources = response.sources
        finalTitle = '' // Non-streaming API doesn't return title, keep existing
        streamingSucceeded = true
      }
      
      if (streamingSucceeded) {
        // Update conversation with final response using callback to get current state
        setActiveConversation(currentConversation => {
          if (!currentConversation) return null
          
          const updatedConversation = {
            ...currentConversation,
            id: finalConversationId, // Update with real conversation ID if it was temp
            title: finalTitle || currentConversation.title, // Use backend-generated title
            messages: currentConversation.messages.map((msg) => {
              // Replace the placeholder assistant message with final response
              if (msg.id === assistantMessageId) {
                return {
                  id: finalMessageId,
                  role: 'assistant' as const,
                  content: accumulatedContent,
                  sources: finalSources,
                  timestamp: createTimestamp(),
                  isStreaming: false
                }
              }
              return msg
            }),
            updated_at: new Date().toISOString()
          }
          
          // Update conversations list with summary
          setConversations(prev => {
            const existingIndex = prev.findIndex(conv => conv.id === finalConversationId)
            const summary = conversationToSummary(updatedConversation)
            
            if (existingIndex >= 0) {
              // Update existing conversation
              return prev.map(conv => 
                conv.id === finalConversationId ? summary : conv
              )
            } else {
              // Add new conversation
              return [summary, ...prev]
            }
          })
          
          return updatedConversation
        })
      }
    } catch (error) {
      console.error('Failed to send message:', error)
      showToast('Failed to send message', 'error')
      
      // Update the placeholder assistant message to show error using callback
      setActiveConversation(currentConversation => {
        if (!currentConversation) return null
        
        return {
          ...currentConversation,
          messages: currentConversation.messages.map((msg) => {
            if (msg.id === assistantMessageId) {
              return {
                ...msg,
                content: 'Failed to get response. Please try again.',
                isStreaming: false,
                isError: true
              }
            }
            return msg
          })
        }
      })
    }
  }, [activeConversation, selectedAgent, showToast, chatApi])

  const createConversation = useCallback(async (): Promise<string> => {
    try {
      const response: ConversationResponse = await chatApi.createConversation('New Chat')
      const newConversationSummary = response.conversation
      
      setConversations(prev => [newConversationSummary, ...prev])
      
      // Create a minimal conversation object for active conversation
      const newConversation: Conversation = {
        id: newConversationSummary.id,
        title: newConversationSummary.title,
        created_at: newConversationSummary.created_at,
        updated_at: newConversationSummary.updated_at,
        messages: []
      }
      
      setActiveConversation(newConversation)
      
      return newConversation.id
    } catch (error) {
      console.error('Failed to create conversation:', error)
      showToast('Failed to create conversation', 'error')
      throw error
    }
  }, [showToast])

  const deleteConversation = useCallback(async (id: string) => {
    try {
      await chatApi.deleteConversation(id)
      
      setConversations(prev => prev.filter(conv => conv.id !== id))
      
      if (activeConversation?.id === id) {
        setActiveConversation(null)
      }
      
      showToast('Conversation deleted', 'success')
    } catch (error) {
      console.error('Failed to delete conversation:', error)
      showToast('Failed to delete conversation', 'error')
    }
  }, [activeConversation, showToast])

  const selectAgent = useCallback((agentId: string | null) => {
    setSelectedAgent(agentId)
  }, [])


  const setActiveConversationById = useCallback(async (conversationId: string) => {
    try {
      // Load the full conversation with messages
      const response = await chatApi.getConversationMessages(conversationId)
      const conversationSummary = conversations.find(conv => conv.id === conversationId)
      
      if (conversationSummary) {
        const fullConversation: Conversation = {
          id: conversationSummary.id,
          title: conversationSummary.title,
          created_at: conversationSummary.created_at,
          updated_at: conversationSummary.updated_at,
          messages: response.messages
        }
        setActiveConversation(fullConversation)
      }
    } catch (error) {
      console.error('Failed to load conversation:', error)
      showToast('Failed to load conversation', 'error')
    }
  }, [conversations, showToast])

  const value: ChatContextValue = {
    activeConversation,
    conversations,
    selectedAgent,
    selectedDocuments,
    sendMessage,
    createConversation,
    deleteConversation,
    selectAgent,
    setActiveConversationById,
    setSelectedDocuments
  }

  return (
    <ChatContext.Provider value={value}>
      {children}
    </ChatContext.Provider>
  )
}
