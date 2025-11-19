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
  BatchProgressEvent,
  ResetStorageResponse,
  DocumentSummary,
  SummaryProgressUpdate,
  TranslateSummaryRequest
} from '../../types/document'
import { isRetryableError, getRetryDelay, logError } from '../../utils/errorHandling'

export class DocumentsApi extends ApiService {
  /**
   * Simple retry mechanism with exponential backoff
   */
  private async retryWithBackoff<T>(
    fn: () => Promise<T>,
    maxRetries: number = 3,
    baseDelay: number = 1000
  ): Promise<T> {
    let lastError: Error
    
    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        return await fn()
      } catch (error) {
        lastError = error as Error
        
        if (attempt === maxRetries || !isRetryableError(lastError)) {
          throw lastError
        }
        
        const delay = getRetryDelay(attempt, baseDelay)
        await new Promise(resolve => setTimeout(resolve, delay))
      }
    }
    
    throw lastError!
  }

  /**
   * Get list of documents with retry mechanism and data alignment
   */
  async getDocuments(): Promise<DocumentListResponse> {
    try {
      return await this.retryWithBackoff(async () => {
        const response = await this.get('/documents')
        
        // Handle both response formats for data alignment
        if (this.isDocumentListResponse(response)) {
          return response
        } else if (this.isDocumentListResponseWithData(response)) {
          return response.data
        } else {
          throw new Error('Invalid response format from documents endpoint')
        }
      }, 3, 1000)
    } catch (error) {
      logError(error as Error, 'getDocuments')
      console.error('Failed to get documents:', error)
      throw new Error(`Failed to fetch documents: ${(error as Error).message}`)
    }
  }

  /**
   * Type guard for direct DocumentListResponse
   */
  private isDocumentListResponse(response: any): response is DocumentListResponse {
    return response && Array.isArray(response.documents)
  }

  /**
   * Type guard for DocumentListResponse wrapped in data property
   */
  private isDocumentListResponseWithData(response: any): response is {data: DocumentListResponse} {
    return response && response.data && Array.isArray(response.data.documents)
  }

  /**
   * Upload a document with retry mechanism
   */
  async uploadDocument(file: File, filename?: string): Promise<DocumentUploadResponse> {
    try {
      return await this.retryWithBackoff(async () => {
        const formData = new FormData()
        formData.append('file', file)
        if (filename) {
          formData.append('filename', filename)
        }
        
        const response = await this.post<DocumentUploadResponse>('/documents/upload', formData)
        return response.data
      }, 3, 1000)
    } catch (error) {
      logError(error as Error, 'uploadDocument')
      console.error('Failed to upload document:', error)
      
      throw new Error(`Upload failed: ${(error as Error).message}`)
    }
  }

  /**
   * Upload from Google Drive with retry mechanism
   */
  async uploadFromDrive(driveFileId: string, accountId: string, filename: string): Promise<DocumentUploadResponse> {
    try {
      return await this.retryWithBackoff(async () => {
        const response = await this.post<DocumentUploadResponse>('/documents/upload-from-drive', {
          drive_file_id: driveFileId,
          account_id: accountId,
          filename
        })
        return response.data
      }, 3, 1000)
    } catch (error) {
      logError(error as Error, 'uploadFromDrive')
      console.error('Failed to upload from Drive:', error)
      
      throw new Error(`Drive upload failed: ${(error as Error).message}`)
    }
  }

  /**
   * Get processing status for a document
   */
  async getProcessingStatus(processingId: string): Promise<{
    processing_id: string
    stage: string
    progress: number
    message: string
    status: 'processing' | 'completed' | 'error'
    timestamp: string
    result?: any
    error?: string
  }> {
    try {
      return await this.retryWithBackoff(async () => {
        const response = await this.get<{
          processing_id: string
          stage: string
          progress: number
          message: string
          status: 'processing' | 'completed' | 'error'
          timestamp: string
          result?: any
          error?: string
        }>(`/documents/processing/${processingId}`)
        return response.data
      }, 3, 1000)
    } catch (error) {
      logError(error as Error, 'getProcessingStatus')
      console.error('Failed to get processing status:', error)
      throw new Error(`Failed to get processing status: ${(error as Error).message}`)
    }
  }

  /**
   * Upload documents with streaming progress and enhanced error handling
   */
  async *uploadDocumentsStream(files: File[]): AsyncGenerator<BatchProgressEvent, void, unknown> {
    let retryCount = 0
    const maxRetries = 3
    
    while (retryCount <= maxRetries) {
      try {
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
          const errorText = await response.text()
          
          if (retryCount < maxRetries && response.status >= 500) {
            // Retry on server errors
            retryCount++
            const delay = Math.pow(2, retryCount) * 1000
            console.warn(`Upload failed, retrying in ${delay}ms (attempt ${retryCount}/${maxRetries})`)
            await new Promise(resolve => setTimeout(resolve, delay))
            continue
          }
          
          logError(
            new Error(`HTTP ${response.status}: ${response.statusText}`),
            'uploadDocumentsStream'
          )
          console.error('Upload failed:', response.statusText)
          throw new Error(`Upload failed: ${response.statusText}. ${errorText}`)
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
                    logError(
                      new Error(parsed.error),
                      'parseSSEData'
                    )
                    console.error('Streaming upload error:', parsed.error)
                    throw new Error(`Streaming error: ${parsed.error}`)
                  }
                  
                  // Yield progress event
                  yield parsed as BatchProgressEvent
                  
                } catch (parseError) {
                  console.error('Failed to parse SSE data:', data, parseError)
                  logError(parseError as Error, 'parseSSEData')
                  throw new Error(`Failed to parse streaming data: ${(parseError as Error).message}`)
                }
              }
            }
          }
        } finally {
          reader.releaseLock()
        }
        
        // If we get here, the upload was successful
        return
        
      } catch (error) {
        logError(error as Error, 'uploadDocumentsStream')
        
        if (retryCount < maxRetries) {
          retryCount++
          const delay = Math.pow(2, retryCount) * 1000
          console.warn(`Streaming upload failed, retrying in ${delay}ms (attempt ${retryCount}/${maxRetries})`)
          await new Promise(resolve => setTimeout(resolve, delay))
          continue
        }
        
        console.error('Streaming upload failed after all retries:', error)
        throw new Error(`Streaming upload failed: ${(error as Error).message}`)
      }
    }
  }

  /**
   * Delete a document with retry mechanism
   */
  async deleteDocument(documentId: string): Promise<DocumentDeleteResponse> {
    try {
      return await this.retryWithBackoff(async () => {
        const response = await this.delete<DocumentDeleteResponse>(`/documents/${documentId}`)
        return response.data
      }, 3, 1000)
    } catch (error) {
      logError(error as Error, 'deleteDocument')
      console.error('Failed to delete document:', error)
      throw new Error(`Failed to delete document: ${(error as Error).message}`)
    }
  }

  /**
   * Get extracted entities for a document with retry mechanism
   */
  async getDocumentEntities(documentId: string): Promise<DocumentEntitiesResponse> {
    try {
      return await this.retryWithBackoff(async () => {
        const response = await this.get<DocumentEntitiesResponse>(`/documents/${documentId}/entities`)
        return response.data
      }, 3, 1000)
    } catch (error) {
      logError(error as Error, 'getDocumentEntities')
      console.error('Failed to get document entities:', error)
      throw new Error(`Failed to get document entities: ${(error as Error).message}`)
    }
  }

  /**
   * Reset all document storage with retry mechanism
   */
  async resetStorage(): Promise<ResetStorageResponse> {
    try {
      return await this.retryWithBackoff(async () => {
        const response = await this.post<ResetStorageResponse>('/storage/reset?confirm=true')
        return response.data
      }, 3, 1000)
    } catch (error) {
      logError(error as Error, 'resetStorage')
      console.error('Failed to reset storage:', error)
      throw new Error(`Failed to reset storage: ${(error as Error).message}`)
    }
  }

  /**
   * Generate summary for a document (non-streaming)
   * POST /documents/{documentId}/summarize
   */
  async generateSummary(documentId: string): Promise<DocumentSummary> {
    try {
      return await this.retryWithBackoff(async () => {
        const response = await this.post<DocumentSummary>(`/documents/${documentId}/summarize`, {
          document_id: documentId
        })
        return response.data
      }, 3, 2000)
    } catch (error) {
      logError(error as Error, 'generateSummary')
      console.error('Failed to generate summary:', error)
      throw new Error(`Failed to generate summary: ${(error as Error).message}`)
    }
  }

  /**
   * Generate summary with streaming progress updates (SSE)
   * POST /documents/{documentId}/summarize/stream
   */
  async generateSummaryStream(
    documentId: string,
    onProgress: (update: SummaryProgressUpdate) => void
  ): Promise<DocumentSummary> {
    return new Promise(async (resolve, reject) => {
      try {
        const response = await fetch(
          `http://localhost:8000/documents/${documentId}/summarize/stream`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Accept': 'text/event-stream',
            },
            body: JSON.stringify({
              document_id: documentId
            })
          }
        )

        if (!response.ok) {
          const errorText = await response.text()
          const error = new Error(`Failed to start summary generation: ${response.statusText}. ${errorText}`)
          logError(error, 'generateSummaryStream')
          reject(error)
          return
        }

        const reader = response.body?.getReader()
        if (!reader) {
          const error = new Error('No response body available')
          logError(error, 'generateSummaryStream')
          reject(error)
          return
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
                  
                  // Check for completion event
                  if (parsed.type === 'complete' && parsed.summary) {
                    resolve(parsed.summary as DocumentSummary)
                    return
                  }

                  // Check for error event
                  if (parsed.type === 'error') {
                    const error = new Error(parsed.error || 'Summary generation failed')
                    logError(error, 'generateSummaryStream')
                    reject(error)
                    return
                  }

                  // Progress update
                  if (parsed.document_id) {
                    onProgress(parsed as SummaryProgressUpdate)
                  }
                  
                } catch (parseError) {
                  console.error('Failed to parse SSE data:', data, parseError)
                  logError(parseError as Error, 'parseSSEData')
                }
              }
            }
          }
        } finally {
          reader.releaseLock()
        }
        
      } catch (error) {
        logError(error as Error, 'generateSummaryStream')
        reject(error)
      }
    })
  }

  /**
   * Get existing summary for a document
   * GET /documents/{documentId}/summary?language=en
   */
  async getSummary(documentId: string, language?: string): Promise<DocumentSummary> {
    try {
      return await this.retryWithBackoff(async () => {
        const url = language 
          ? `/documents/${documentId}/summary?language=${language}`
          : `/documents/${documentId}/summary`
        const response = await this.get<DocumentSummary>(url)
        return response.data
      }, 3, 1000)
    } catch (error) {
      logError(error as Error, 'getSummary')
      console.error('Failed to get summary:', error)
      throw new Error(`Failed to get summary: ${(error as Error).message}`)
    }
  }

  /**
   * Delete summary and all translations for a document
   * DELETE /documents/{documentId}/summary
   */
  async deleteSummary(documentId: string): Promise<void> {
    try {
      return await this.retryWithBackoff(async () => {
        await this.delete(`/documents/${documentId}/summary`)
      }, 3, 1000)
    } catch (error) {
      logError(error as Error, 'deleteSummary')
      console.error('Failed to delete summary:', error)
      throw new Error(`Failed to delete summary: ${(error as Error).message}`)
    }
  }

  /**
   * Translate existing summary to target language
   * POST /documents/{documentId}/summary/translate
   * Body: { target_language: "English" | "אנגלית" | "Español" | ... }
   */
  async translateSummary(
    documentId: string, 
    targetLanguage: string
  ): Promise<DocumentSummary> {
    try {
      return await this.retryWithBackoff(async () => {
        const request: TranslateSummaryRequest = {
          target_language: targetLanguage
        }
        const response = await this.post<DocumentSummary>(
          `/documents/${documentId}/summary/translate`,
          request
        )
        return response.data
      }, 3, 2000)
    } catch (error) {
      logError(error as Error, 'translateSummary')
      console.error('Failed to translate summary:', error)
      throw new Error(`Failed to translate summary: ${(error as Error).message}`)
    }
  }
}
