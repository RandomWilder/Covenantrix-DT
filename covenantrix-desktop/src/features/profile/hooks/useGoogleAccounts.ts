/**
 * Google Accounts Hook
 * Custom hook for managing Google account operations
 */

import { useState, useCallback } from 'react';
import { googleService, GoogleAccountResponse } from '../../../services/googleService';

export const useGoogleAccounts = () => {
  const [accounts, setAccounts] = useState<GoogleAccountResponse[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Load all Google accounts
   */
  const loadAccounts = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await googleService.listAccounts();
      setAccounts(response.accounts);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load accounts';
      setError(message);
      console.error('Error loading Google accounts:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Initiate OAuth connection flow
   */
  const connectAccount = useCallback(async () => {
    setError(null);

    try {
      await googleService.connectAccount();
      // OAuth window will open via Electron IPC
      // Callback will be handled separately
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to start OAuth flow';
      setError(message);
      console.error('Error connecting Google account:', err);
      throw err;
    }
  }, []);

  /**
   * Remove a Google account
   */
  const removeAccount = useCallback(async (accountId: string) => {
    setIsLoading(true);
    setError(null);

    try {
      await googleService.removeAccount(accountId);
      // Reload accounts after removal
      await loadAccounts();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to remove account';
      setError(message);
      console.error('Error removing Google account:', err);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [loadAccounts]);

  /**
   * Clear error state
   */
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    accounts,
    isLoading,
    error,
    loadAccounts,
    connectAccount,
    removeAccount,
    clearError
  };
};

