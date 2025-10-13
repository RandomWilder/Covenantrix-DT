/**
 * API Keys Tab - Profile Modal
 * Reuses existing ApiKeysTab from settings
 */

import React from 'react';
import { useSettings } from '../../../contexts/SettingsContext';
import ApiKeysTab from '../../settings/ApiKeysTab';

export const ProfileApiKeysTab: React.FC = () => {
  const { settings, updateSettings, error, clearError } = useSettings();

  const handleChange = (apiKeys: any) => {
    updateSettings({ api_keys: apiKeys });
  };

  if (!settings) {
    return <div>Loading...</div>;
  }

  return (
    <ApiKeysTab
      settings={settings.api_keys}
      onChange={handleChange}
      error={error}
      onClearError={clearError}
    />
  );
};

