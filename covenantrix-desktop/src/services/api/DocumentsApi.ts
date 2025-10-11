/**
 * Documents API Service
 * Handles document-related API calls
 */

import { ApiService } from './ApiService'
import { 
  DocumentListResponse, 
  DocumentUploadResponse, 
  DocumentDeleteResponse,
  DocumentEntitiesResponse,
  BatchProgressEvent
} from '../../types/document'

export class DocumentsApi extends ApiService {
  /**
   * Get list of documents
   */
  async getDocuments(): Promise<DocumentListResponse> {
    const response = await this.get<DocumentListResponse>('/documents')
    return response.data
  }

  /**
   * Upload a document
   */
  async uploadDocument(file: File): Promise<DocumentUploadResponse> {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await this.post<DocumentUploadResponse>('/documents/upload', formData)
    return response.data
  }

  /**
   * Upload documents with streaming progress
   */
  async *uploadDocumentsStream(files: File[]): AsyncGenerator<BatchProgressEvent, void, unknown> {
    const formData = new FormData()
    files.forEach(file => {
      formData.append('files', file)
    })

    const response = await fetch('http://localhost:8000/documents/upload/stream', {
      method: 'POST',
      body: formData,
      headers: {
        // Don't set Content-Type - browser will set it with boundary for FormData
      },
    })

    if (!response.ok) {
      throw new Error(`Upload failed: ${response.statusText}`)
    }

    const reader = response.body?.getReader()
    if (!reader) {
      throw new Error('No response body')
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
              
              // Check for error event
              if (parsed.error) {
                throw new Error(parsed.error)
              }
              
              // Yield progress event
              yield parsed as BatchProgressEvent
              
            } catch (e) {
              console.error('Failed to parse SSE data:', data, e)
              throw e
            }
          }
        }
      }
    } finally {
      reader.releaseLock()
    }
  }

  /**
   * Delete a document
   */
  async deleteDocument(documentId: string): Promise<DocumentDeleteResponse> {
    const response = await this.delete<DocumentDeleteResponse>(`/documents/${documentId}`)
    return response.data
  }

  /**
   * Get extracted entities for a document
   */
  async getDocumentEntities(documentId: string): Promise<DocumentEntitiesResponse> {
    const response = await this.get<DocumentEntitiesResponse>(`/documents/${documentId}/entities`)
    return response.data
  }
}
