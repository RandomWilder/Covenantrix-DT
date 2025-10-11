export interface Conversation {
  id: string
  title: string
  created_at: string
  updated_at: string
  messages: Message[]
}

export interface ConversationSummary {
  id: string
  title: string
  created_at: string
  updated_at: string
  message_count: number
  last_message_preview?: string
}

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources: Source[]
  timestamp: string
  isStreaming?: boolean
  isError?: boolean
}

export interface Source {
  document_id: string
  document_name: string
  page_number?: number
  confidence?: number
  excerpt?: string
}

export interface ChatMessageRequest {
  conversation_id?: string
  message: string
  agent_id?: string
  document_ids?: string[]
}

export interface ChatMessageResponse {
  success: boolean
  conversation_id: string
  message_id: string
  response: string
  sources: Source[]
}

export interface ConversationResponse {
  success: boolean
  conversation: ConversationSummary
}

export interface ConversationListResponse {
  success: boolean
  conversations: ConversationSummary[]
  total_count: number
}

export interface MessageListResponse {
  success: boolean
  messages: Message[]
  total_count: number
}

export interface ChatContextValue {
  // Conversation state
  activeConversation: Conversation | null
  conversations: ConversationSummary[]
  
  // UI state
  selectedAgent: string | null
  selectedDocuments: string[]
  
  // Actions
  sendMessage: (message: string, documentIds?: string[]) => Promise<void>
  createConversation: () => Promise<string>
  deleteConversation: (id: string) => Promise<void>
  selectAgent: (agentId: string | null) => void
  setActiveConversationById: (conversationId: string) => Promise<void>
  setSelectedDocuments: (documentIds: string[]) => void
}
