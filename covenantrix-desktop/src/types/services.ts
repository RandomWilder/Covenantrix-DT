/**
 * Service Status Types
 * Type definitions for service availability and status checking
 */

/**
 * Service status response from backend
 * Indicates which services are currently available based on API key configuration
 */
export interface ServiceStatus {
  openai_available: boolean;
  cohere_available: boolean;
  google_available: boolean;
  features: {
    chat: boolean;
    upload: boolean;
    reranking: boolean;
    ocr: boolean;
  };
}

/**
 * Feature guard configuration
 * Used to display warnings/banners when features are unavailable
 */
export interface ServiceFeatureGuard {
  available: boolean;
  message: string;
  actionText: string;
  actionRoute: string;
}

/**
 * Service status response wrapper
 * Used for IPC communication
 */
export interface ServiceStatusResponse {
  success: boolean;
  data?: ServiceStatus;
  error?: string;
}

