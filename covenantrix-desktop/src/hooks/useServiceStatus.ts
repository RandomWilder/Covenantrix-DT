/**
 * useServiceStatus Hook
 * Hook to check service availability via global backend state
 * Checks OpenAI, Cohere, and Google services
 */

import { useState, useCallback, useEffect } from 'react';
import type { ServiceStatus } from '../types/services';

export interface UseServiceStatusReturn {
  openaiAvailable: boolean;
  cohereAvailable: boolean;
  googleAvailable: boolean;
  features: {
    chat: boolean;
    upload: boolean;
    reranking: boolean;
    ocr: boolean;
  };
  isLoading: boolean;
  error: string | null;
  refreshStatus: () => Promise<void>;
}

/**
 * Custom hook for checking service availability
 * Checks global service state without re-resolving keys
 * 
 * @returns Service status state and refresh function
 */
export const useServiceStatus = (): UseServiceStatusReturn => {
  const [openaiAvailable, setOpenaiAvailable] = useState<boolean>(false);
  const [cohereAvailable, setCohereAvailable] = useState<boolean>(false);
  const [googleAvailable, setGoogleAvailable] = useState<boolean>(false);
  const [features, setFeatures] = useState({
    chat: false,
    upload: false,
    reranking: false,
    ocr: false,
  });
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchServiceStatus = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await window.electronAPI.getServicesStatus();
      
      if (response.success && response.data) {
        const status: ServiceStatus = response.data;
        setOpenaiAvailable(status.openai_available);
        setCohereAvailable(status.cohere_available);
        setGoogleAvailable(status.google_available);
        setFeatures(status.features);
      } else {
        setError(response.error || 'Failed to check service status');
        // Reset to all unavailable on error
        setOpenaiAvailable(false);
        setCohereAvailable(false);
        setGoogleAvailable(false);
        setFeatures({
          chat: false,
          upload: false,
          reranking: false,
          ocr: false,
        });
      }
    } catch (err) {
      console.error('Failed to check service status:', err);
      setError('Failed to check service status');
      // Reset to all unavailable on error
      setOpenaiAvailable(false);
      setCohereAvailable(false);
      setGoogleAvailable(false);
      setFeatures({
        chat: false,
        upload: false,
        reranking: false,
        ocr: false,
      });
    } finally {
      setIsLoading(false);
    }
  }, []);

  const refreshStatus = useCallback(async () => {
    await fetchServiceStatus();
  }, [fetchServiceStatus]);

  // Check service status on mount
  useEffect(() => {
    fetchServiceStatus();
  }, [fetchServiceStatus]);

  return {
    openaiAvailable,
    cohereAvailable,
    googleAvailable,
    features,
    isLoading,
    error,
    refreshStatus,
  };
};

