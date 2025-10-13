/**
 * Google API Service
 * Handles Google OAuth and Drive operations
 */

const API_BASE_URL = 'http://127.0.0.1:8000';

export interface GoogleAccountResponse {
  account_id: string;
  email: string;
  display_name?: string;
  status: string;
  connected_at: string;
  last_used: string;
  scopes?: string[];
}

export interface GoogleAccountsListResponse {
  success: boolean;
  accounts: GoogleAccountResponse[];
}

export interface AuthUrlResponse {
  auth_url: string;
  state: string;
}

export interface DriveFileResponse {
  id: string;
  name: string;
  mimeType?: string;  // Backend sends camelCase
  size?: number;
  modifiedTime?: string;  // Backend sends camelCase
  webViewLink?: string;  // Backend sends camelCase
  iconLink?: string;  // Backend sends camelCase
}

export interface DriveFilesListResponse {
  success: boolean;
  files: DriveFileResponse[];
  account_id: string;
}

export interface DriveDownloadRequest {
  account_id: string;
  file_ids: string[];
}

export interface BatchProgressEvent {
  total_files: number;
  current_file_index: number;
  file_progress: {
    filename: string;
    document_id?: string;
    stage: string;
    message: string;
    progress_percent: number;
    timestamp: string;
    error?: string;
  };
  overall_progress_percent: number;
}

export const googleService = {
  /**
   * List all connected Google accounts
   */
  async listAccounts(): Promise<GoogleAccountsListResponse> {
    const response = await fetch(`${API_BASE_URL}/api/google/accounts`);
    
    if (!response.ok) {
      throw new Error('Failed to fetch Google accounts');
    }
    
    return response.json();
  },

  /**
   * Initiate OAuth flow (triggers Electron OAuth window)
   */
  async connectAccount(): Promise<void> {
    // Trigger IPC to Electron to open OAuth window
    if (window.electronAPI?.startGoogleOAuth) {
      await window.electronAPI.startGoogleOAuth();
    } else {
      throw new Error('Electron API not available');
    }
  },

  /**
   * Handle OAuth callback after authorization
   */
  async handleOAuthCallback(code: string, state: string): Promise<GoogleAccountResponse> {
    const params = new URLSearchParams({ code, state });
    const response = await fetch(
      `${API_BASE_URL}/api/google/accounts/callback?${params}`,
      { method: 'POST' }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to connect Google account');
    }

    return response.json();
  },

  /**
   * Remove a Google account
   */
  async removeAccount(accountId: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/google/accounts/${accountId}`, {
      method: 'DELETE'
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to remove Google account');
    }
  },

  /**
   * List files from Google Drive
   */
  async listDriveFiles(accountId: string, folderId?: string): Promise<DriveFilesListResponse> {
    const params = new URLSearchParams({ account_id: accountId });
    if (folderId) {
      params.append('folder_id', folderId);
    }

    const response = await fetch(`${API_BASE_URL}/api/google/drive/files?${params}`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to fetch Drive files');
    }

    return response.json();
  },

  /**
   * Download files from Google Drive and process through upload pipeline
   */
  async downloadDriveFiles(request: DriveDownloadRequest): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/google/drive/download`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(request)
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to download Drive files');
    }

    return response.json();
  },

  /**
   * Download files from Google Drive with streaming progress updates
   * Similar to DocumentsApi.uploadDocumentsStream but for Drive files
   */
  async *downloadDriveFilesStream(accountId: string, fileIds: string[]): AsyncGenerator<BatchProgressEvent, void, unknown> {
    const response = await fetch(`${API_BASE_URL}/api/google/drive/download/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        account_id: accountId,
        file_ids: fileIds
      })
    });

    if (!response.ok) {
      throw new Error(`Drive download failed: ${response.statusText}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('No response body');
    }

    const decoder = new TextDecoder();
    let buffer = '';

    try {
      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        
        // Process complete SSE messages (ending with \n\n)
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || ''; // Keep incomplete message in buffer

        for (const line of lines) {
          if (line.trim().startsWith('data: ')) {
            const data = line.trim().substring(6); // Remove 'data: ' prefix
            try {
              const parsed = JSON.parse(data);
              
              // Check for error event
              if (parsed.error) {
                throw new Error(parsed.error);
              }
              
              // Yield progress event
              yield parsed as BatchProgressEvent;
              
            } catch (e) {
              console.error('Failed to parse SSE data:', data, e);
              throw e;
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  }
};

