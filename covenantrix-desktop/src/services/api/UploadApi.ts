import { ApiService } from './ApiService'

export interface BatchUploadResponse {
  success: boolean
  total_files: number
  successful_uploads: number
  failed_uploads: number
  results: Array<{
    filename: string
    document_id?: string
    success: boolean
    error?: string
    file_size?: number
  }>
  message: string
}

export interface GoogleDriveFileInfo {
  file_id: string
  name: string
  mime_type: string
  size?: number
  modified_time?: string
  web_view_link?: string
}

export interface GoogleDriveListResponse {
  success: boolean
  files: GoogleDriveFileInfo[]
  next_page_token?: string
}

export class UploadApiService extends ApiService {
  /**
   * Upload multiple files in batch
   */
  async uploadBatch(files: File[]): Promise<BatchUploadResponse> {
    const formData = new FormData()
    files.forEach(file => {
      formData.append('files', file)
    })

    const response = await this.post('/documents/upload/batch', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })

    return response.data as BatchUploadResponse
  }

  /**
   * Upload files from Google Drive
   */
  async uploadFromGoogleDrive(fileIds: string[]): Promise<BatchUploadResponse> {
    const response = await this.post('/documents/upload/drive', {
      file_ids: fileIds
    })

    return response.data as BatchUploadResponse
  }

  /**
   * List files from Google Drive
   */
  async listGoogleDriveFiles(folderId?: string, pageToken?: string): Promise<GoogleDriveListResponse> {
    const params = new URLSearchParams()
    if (folderId) params.append('folder_id', folderId)
    if (pageToken) params.append('page_token', pageToken)

    const response = await this.get(`/documents/drive/files?${params.toString()}`)
    return response.data as GoogleDriveListResponse
  }

  /**
   * Check Google authentication status
   */
  async checkGoogleAuth(): Promise<{ authenticated: boolean; account?: any }> {
    try {
      const response = await this.get('/auth/google/status')
      return {
        authenticated: true,
        account: response.data
      }
    } catch (error) {
      return {
        authenticated: false
      }
    }
  }

  /**
   * Initiate Google OAuth flow
   */
  async initiateGoogleAuth(): Promise<{ authUrl: string }> {
    const response = await this.post('/auth/google/authorize')
    return response.data as { authUrl: string }
  }
}

export const uploadApi = new UploadApiService()
