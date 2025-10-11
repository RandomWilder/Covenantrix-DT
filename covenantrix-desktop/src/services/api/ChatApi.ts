/**
 * Chat API Service
 * Handles chat-related API calls
 */

import { ApiService } from './ApiService'
import { 
  ChatMessageRequest, 
  ChatMessageResponse,
  ConversationListResponse,
  ConversationResponse,
  MessageListResponse
} from '../../types/chat'

export class ChatApi extends ApiService {
  protected getBaseURL(): string {
    // Access the baseURL through a method since it's private in parent
    // Default to localhost:8000 if not set
    return (this as any).baseURL || 'http://localhost:8000'
  }
  /**
   * Send a message and get response
   */
  async sendMessage(request: ChatMessageRequest): Promise<ChatMessageResponse> {
    const response = await this.post<ChatMessageResponse>('/chat/message', request)
    return response.data
  }

  /**
   * Send a message and stream the response token by token
   */
  async *sendMessageStream(request: ChatMessageRequest): AsyncGenerator<{
    token?: string
    done: boolean
    message_id?: string
    conversation_id?: string
    sources?: any[]
  }> {
    const url = `${this.getBaseURL()}/chat/message/stream`
    
    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('Response body is not readable')
      }

      const decoder = new TextDecoder()
      let buffer = ''

      try {
        while (true) {
          const { done, value } = await reader.read()
          
          if (done) break

          buffer += decoder.decode(value, { stream: true })
          
          // Process complete SSE messages (ending with \n\n)
          const lines = buffer.split('\n\n')
          buffer = lines.pop() || '' // Keep incomplete message in buffer

          for (const line of lines) {
            if (line.trim().startsWith('data: ')) {
              const data = line.trim().substring(6) // Remove 'data: ' prefix
              try {
                const parsed = JSON.parse(data)
                yield parsed
                
                // If done, exit the loop
                if (parsed.done) {
                  return
                }
              } catch (e) {
                console.error('Failed to parse SSE data:', data, e)
              }
            }
          }
        }
      } finally {
        reader.releaseLock()
      }
    } catch (error) {
      console.error('Stream error:', error)
      throw error
    }
  }

  /**
   * Get list of conversations
   */
  async getConversations(): Promise<ConversationListResponse> {
    const response = await this.get<ConversationListResponse>('/chat/conversations')
    return response.data
  }

  /**
   * Create a new conversation
   */
  async createConversation(title: string): Promise<ConversationResponse> {
    const response = await this.post<ConversationResponse>('/chat/conversations', { title })
    return response.data
  }

  /**
   * Delete a conversation
   */
  async deleteConversation(id: string): Promise<void> {
    await this.delete(`/chat/conversations/${id}`)
  }

  /**
   * Get messages for a specific conversation
   */
  async getConversationMessages(id: string): Promise<MessageListResponse> {
    const response = await this.get<MessageListResponse>(`/chat/conversations/${id}/messages`)
    return response.data
  }
}
