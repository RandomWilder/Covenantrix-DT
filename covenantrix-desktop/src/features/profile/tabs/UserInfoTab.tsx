/**
 * User Info Tab - Profile Modal
 * Manage user profile information
 */

import React, { useState, useEffect } from 'react';
import { Save, User } from 'lucide-react';
import { useSettings } from '../../../contexts/SettingsContext';
import { useToast } from '../../../hooks/useToast';
import { ProfileSettings } from '../../../types/settings';

export const UserInfoTab: React.FC = () => {
  const { settings, updateSettings } = useSettings();
  const { showToast } = useToast();
  const [profile, setProfile] = useState<ProfileSettings>({
    first_name: '',
    last_name: '',
    email: ''
  });
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (settings?.profile) {
      setProfile({
        first_name: settings.profile.first_name || '',
        last_name: settings.profile.last_name || '',
        email: settings.profile.email || ''
      });
    }
  }, [settings?.profile]);

  const handleChange = (field: keyof ProfileSettings, value: string) => {
    setProfile(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      // Clean up empty strings to undefined
      const cleanedProfile: ProfileSettings = {
        first_name: profile.first_name?.trim() || undefined,
        last_name: profile.last_name?.trim() || undefined,
        email: profile.email?.trim() || undefined
      };

      await updateSettings({ profile: cleanedProfile });
      showToast('Profile updated successfully', 'success');
    } catch (error) {
      console.error('Error saving profile:', error);
      showToast('Failed to update profile', 'error');
    } finally {
      setIsSaving(false);
    }
  };

  const hasChanges = 
    profile.first_name !== (settings?.profile?.first_name || '') ||
    profile.last_name !== (settings?.profile?.last_name || '') ||
    profile.email !== (settings?.profile?.email || '');

  return (
    <div className="space-y-6">
      <div className="flex items-center space-x-3">
        <div className="w-12 h-12 bg-indigo-100 dark:bg-indigo-900 rounded-full flex items-center justify-center">
          <User className="w-6 h-6 text-indigo-600 dark:text-indigo-400" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            User Information
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Manage your profile information
          </p>
        </div>
      </div>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            First Name
          </label>
          <input
            type="text"
            value={profile.first_name || ''}
            onChange={(e) => handleChange('first_name', e.target.value)}
            placeholder="John"
            className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Last Name
          </label>
          <input
            type="text"
            value={profile.last_name || ''}
            onChange={(e) => handleChange('last_name', e.target.value)}
            placeholder="Doe"
            className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Email
          </label>
          <input
            type="email"
            value={profile.email || ''}
            onChange={(e) => handleChange('email', e.target.value)}
            placeholder="john.doe@example.com"
            className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent"
          />
        </div>
      </div>

      <div className="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-700">
        <p className="text-xs text-gray-500 dark:text-gray-400">
          All information is stored locally on your device
        </p>
        <button
          onClick={handleSave}
          disabled={!hasChanges || isSaving}
          className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isSaving ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              <span>Saving...</span>
            </>
          ) : (
            <>
              <Save className="w-4 h-4" />
              <span>Save Changes</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
};

