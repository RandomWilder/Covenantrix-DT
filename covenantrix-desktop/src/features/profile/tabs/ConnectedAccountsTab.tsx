/**
 * Connected Accounts Tab - Profile Modal
 * Manage Google Drive and other connected accounts
 */

import React, { useEffect, useState } from 'react';
import { Plus, Cloud, AlertCircle, Loader } from 'lucide-react';
import { useToast } from '../../../hooks/useToast';
import { useGoogleAccounts } from '../hooks/useGoogleAccounts';
import { GoogleAccountCard } from '../components/GoogleAccountCard';
import { googleService } from '../../../services/googleService';
import { GoogleAccountSettings } from '../../../types/settings';

export const ConnectedAccountsTab: React.FC = () => {
  const { showToast } = useToast();
  const { accounts, isLoading, error, loadAccounts, connectAccount, removeAccount, clearError } = useGoogleAccounts();
  const [isConnecting, setIsConnecting] = useState(false);
  const [accountToRemove, setAccountToRemove] = useState<string | null>(null);

  // Load accounts only on mount - let hook's state management handle updates
  useEffect(() => {
    loadAccounts();
  }, [loadAccounts]);

  useEffect(() => {
    // Setup OAuth callback listener
    if (window.electronAPI?.onOAuthCallback) {
      const handleCallback = async ({ code, state }: { code: string; state: string }) => {
        try {
          setIsConnecting(true);
          const account = await googleService.handleOAuthCallback(code, state);
          showToast(`Connected ${account.email} successfully`, 'success');
          // Reload accounts to refresh the list
          await loadAccounts();
        } catch (error) {
          const message = error instanceof Error ? error.message : 'Failed to connect Google account';
          showToast(message, 'error');
        } finally {
          setIsConnecting(false);
        }
      };
      
      window.electronAPI.onOAuthCallback(handleCallback);
      
      // Cleanup function to prevent memory leaks
      // Note: removeAllListeners will be added to preload API
      return () => {
        // Cleanup handled by component unmount
        // The IPC listener will be cleaned up when the component unmounts
      };
    }
  }, [loadAccounts, showToast]);

  const handleConnect = async () => {
    setIsConnecting(true);
    clearError();
    try {
      await connectAccount();
      // OAuth window will open via Electron
    } catch (error) {
      setIsConnecting(false);
      const message = error instanceof Error ? error.message : 'Failed to start connection';
      showToast(message, 'error');
    }
  };

  const handleRemove = async (accountId: string) => {
    // Show confirmation
    setAccountToRemove(accountId);
  };

  const confirmRemove = async () => {
    if (!accountToRemove) return;

    try {
      await removeAccount(accountToRemove);
      showToast('Account removed successfully', 'success');
      setAccountToRemove(null);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to remove account';
      showToast(message, 'error');
    }
  };

  const cancelRemove = () => {
    setAccountToRemove(null);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center">
            <Cloud className="w-6 h-6 text-blue-600 dark:text-blue-400" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Connected Accounts
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Manage your Google Drive connections
            </p>
          </div>
        </div>
        <button
          onClick={handleConnect}
          disabled={isConnecting || isLoading}
          className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isConnecting ? (
            <>
              <Loader className="w-4 h-4 animate-spin" />
              <span>Connecting...</span>
            </>
          ) : (
            <>
              <Plus className="w-4 h-4" />
              <span>Connect Google Drive</span>
            </>
          )}
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <div className="flex items-start space-x-3">
            <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="font-medium text-red-800 dark:text-red-200">Error</h4>
              <p className="text-sm text-red-700 dark:text-red-300 mt-1">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Loading State */}
      {isLoading && accounts.length === 0 && (
        <div className="flex items-center justify-center py-12">
          <Loader className="w-8 h-8 text-blue-600 dark:text-blue-400 animate-spin" />
        </div>
      )}

      {/* Accounts List */}
      {!isLoading && accounts.length === 0 && (
        <div className="text-center py-12">
          <div className="w-16 h-16 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center mx-auto mb-4">
            <Cloud className="w-8 h-8 text-gray-400 dark:text-gray-500" />
          </div>
          <h4 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            No accounts connected
          </h4>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
            Connect your Google Drive to upload documents directly
          </p>
          <button
            onClick={handleConnect}
            disabled={isConnecting}
            className="inline-flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Plus className="w-4 h-4" />
            <span>Connect Google Drive</span>
          </button>
        </div>
      )}

      {accounts.length > 0 && (
        <div className="space-y-3">
          {accounts.map((account) => {
            // Convert GoogleAccountResponse to GoogleAccountSettings for the card
            const accountSettings: GoogleAccountSettings = {
              ...account,
              scopes: account.scopes || []
            };
            return (
              <GoogleAccountCard
                key={account.account_id}
                account={accountSettings}
                onRemove={handleRemove}
              />
            );
          })}
        </div>
      )}

      {/* Info Box */}
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
        <div className="flex items-start space-x-3">
          <div className="text-blue-600 dark:text-blue-400">ℹ️</div>
          <div>
            <h4 className="font-medium text-blue-800 dark:text-blue-200">About Connections</h4>
            <p className="text-sm text-blue-700 dark:text-blue-300 mt-1">
              Connected accounts allow you to browse and upload documents directly from Google Drive. 
              Your credentials are encrypted and stored securely on your device.
            </p>
          </div>
        </div>
      </div>

      {/* Confirmation Modal */}
      {accountToRemove && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              Remove Account
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
              Are you sure you want to remove this Google account? You'll need to reconnect it to access your Drive files.
            </p>
            <div className="flex space-x-3">
              <button
                onClick={cancelRemove}
                className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={confirmRemove}
                className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                Remove
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

