/**
 * Settings Backup/Restore Component
 * Handles settings export/import functionality
 */

import React, { useState, useRef } from 'react';
import { Download, Upload, FileText, AlertCircle, CheckCircle, X } from 'lucide-react';
import { useSettings } from '../../hooks/useSettings';
import { useToast } from '../../hooks/useToast';
import { 
  downloadSettingsFile, 
  readSettingsFile, 
  validateBackupFile, 
  getBackupMetadata,
  compareSettings 
} from '../../utils/settingsBackup';
import { BackupMetadata } from '../../utils/settingsBackup';

interface SettingsBackupProps {
  onImport?: (settings: any) => void;
}

const SettingsBackup: React.FC<SettingsBackupProps> = ({ onImport }) => {
  const { settings, importSettings } = useSettings();
  const { showToast } = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const [isExporting, setIsExporting] = useState(false);
  const [isImporting, setIsImporting] = useState(false);
  const [importPreview, setImportPreview] = useState<{
    metadata: BackupMetadata;
    changes: { changed: string[]; added: string[]; removed: string[] };
  } | null>(null);
  const [showImportModal, setShowImportModal] = useState(false);

  const handleExport = async () => {
    if (!settings) return;

    try {
      setIsExporting(true);
      downloadSettingsFile(settings);
      showToast('Settings exported successfully', 'success');
    } catch (error) {
      console.error('Export error:', error);
      showToast('Failed to export settings', 'error');
    } finally {
      setIsExporting(false);
    }
  };

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      setIsImporting(true);
      
      // Validate file first
      const validation = await validateBackupFile(file);
      if (!validation.valid) {
        showToast(validation.error || 'Invalid backup file', 'error');
        return;
      }

      // Get metadata and compare with current settings
      const metadata = await getBackupMetadata(file);
      if (!metadata) {
        showToast('Could not read backup metadata', 'error');
        return;
      }

      // Read and preview settings
      const importedSettings = await readSettingsFile(file);
      const changes = settings ? compareSettings(settings, importedSettings) : { changed: [], added: [], removed: [] };
      
      setImportPreview({ metadata, changes });
      setShowImportModal(true);
    } catch (error) {
      console.error('Import error:', error);
      showToast('Failed to read backup file', 'error');
    } finally {
      setIsImporting(false);
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleConfirmImport = async () => {
    if (!importPreview) return;

    try {
      setIsImporting(true);
      
      // Get the file again and import
      const file = fileInputRef.current?.files?.[0];
      if (!file) {
        showToast('No file selected', 'error');
        return;
      }

      const importedSettings = await readSettingsFile(file);
      await importSettings(JSON.stringify(importedSettings));
      
      showToast('Settings imported successfully', 'success');
      setShowImportModal(false);
      setImportPreview(null);
      
      if (onImport) {
        onImport(importedSettings);
      }
    } catch (error) {
      console.error('Import error:', error);
      showToast('Failed to import settings', 'error');
    } finally {
      setIsImporting(false);
    }
  };

  const handleCancelImport = () => {
    setShowImportModal(false);
    setImportPreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <>
      <div className="space-y-4">
        <div className="border border-gray-200 dark:border-gray-600 rounded-lg p-4">
          <h3 className="font-medium text-gray-900 dark:text-white mb-3">Backup & Restore</h3>
          
          <div className="space-y-3">
            {/* Export Section */}
            <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <div className="flex items-center space-x-3">
                <Download className="w-5 h-5 text-blue-600" />
                <div>
                  <div className="font-medium text-gray-900 dark:text-white">Export Settings</div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">
                    Download your current settings as a backup file
                  </div>
                </div>
              </div>
              <button
                onClick={handleExport}
                disabled={isExporting || !settings}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isExporting ? 'Exporting...' : 'Export'}
              </button>
            </div>

            {/* Import Section */}
            <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <div className="flex items-center space-x-3">
                <Upload className="w-5 h-5 text-green-600" />
                <div>
                  <div className="font-medium text-gray-900 dark:text-white">Import Settings</div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">
                    Restore settings from a backup file
                  </div>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".json"
                  onChange={handleFileSelect}
                  className="hidden"
                />
                <button
                  onClick={() => fileInputRef.current?.click()}
                  disabled={isImporting}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {isImporting ? 'Importing...' : 'Import'}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Current Settings Info */}
        {settings && (
          <div className="border border-gray-200 dark:border-gray-600 rounded-lg p-4">
            <h3 className="font-medium text-gray-900 dark:text-white mb-3">Current Settings</h3>
            <div className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
              <div>Version: {settings.version}</div>
              <div>Last Updated: {new Date(settings.last_updated || '').toLocaleString()}</div>
              <div>API Mode: {settings.api_keys.mode}</div>
              <div>Language: {settings.language.preferred}</div>
              <div>Theme: {settings.ui.theme}</div>
            </div>
          </div>
        )}
      </div>

      {/* Import Preview Modal */}
      {showImportModal && importPreview && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-2xl max-h-[80vh] flex flex-col">
            <div className="p-6 border-b border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                  Import Settings
                </h2>
                <button
                  onClick={handleCancelImport}
                  className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-6">
              {/* Backup Info */}
              <div className="mb-6">
                <h3 className="font-medium text-gray-900 dark:text-white mb-3">Backup Information</h3>
                <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 space-y-2">
                  <div className="flex items-center space-x-2">
                    <FileText className="w-4 h-4 text-blue-600" />
                    <span className="text-sm text-gray-600 dark:text-gray-400">
                      Version: {importPreview.metadata.version}
                    </span>
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">
                    Created: {new Date(importPreview.metadata.timestamp).toLocaleString()}
                  </div>
                  {importPreview.metadata.description && (
                    <div className="text-sm text-gray-600 dark:text-gray-400">
                      Description: {importPreview.metadata.description}
                    </div>
                  )}
                </div>
              </div>

              {/* Changes Preview */}
              {importPreview.changes.changed.length > 0 && (
                <div className="mb-6">
                  <h3 className="font-medium text-gray-900 dark:text-white mb-3">Settings Changes</h3>
                  <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
                    <div className="flex items-start space-x-2">
                      <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5" />
                      <div>
                        <div className="font-medium text-yellow-800 dark:text-yellow-200 mb-2">
                          The following settings will be changed:
                        </div>
                        <ul className="text-sm text-yellow-700 dark:text-yellow-300 space-y-1">
                          {importPreview.changes.changed.map((change, index) => (
                            <li key={index}>• {change}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Warning */}
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
                <div className="flex items-start space-x-2">
                  <AlertCircle className="w-5 h-5 text-red-600 mt-0.5" />
                  <div>
                    <div className="font-medium text-red-800 dark:text-red-200 mb-1">
                      Warning
                    </div>
                    <div className="text-sm text-red-700 dark:text-red-300">
                      This will replace your current settings. Make sure to export your current settings first if you want to keep them.
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="border-t border-gray-200 dark:border-gray-700 p-6">
              <div className="flex items-center justify-end space-x-3">
                <button
                  onClick={handleCancelImport}
                  className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleConfirmImport}
                  disabled={isImporting}
                  className="flex items-center space-x-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {isImporting ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      <span>Importing...</span>
                    </>
                  ) : (
                    <>
                      <CheckCircle className="w-4 h-4" />
                      <span>Import Settings</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default SettingsBackup;
