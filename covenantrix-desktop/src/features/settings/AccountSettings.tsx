/**
 * Account Settings Tab
 * User profile information and account management
 */

import React, { useState, useEffect } from 'react';
import { User, Mail, Info } from 'lucide-react';
import { ProfileSettings } from '../../types/settings';

interface AccountSettingsProps {
  settings: ProfileSettings;
  onChange: (settings: ProfileSettings) => void;
}

const AccountSettings: React.FC<AccountSettingsProps> = ({ settings, onChange }) => {
  const [profile, setProfile] = useState<ProfileSettings>({
    first_name: '',
    last_name: '',
    email: ''
  });

  // Sync with incoming props (handles data loading after component mount)
  useEffect(() => {
    setProfile({
      first_name: settings?.first_name || '',
      last_name: settings?.last_name || '',
      email: settings?.email || ''
    });
  }, [settings]);

  const handleChange = (field: keyof ProfileSettings, value: string) => {
    const updatedProfile = {
      ...profile,
      [field]: value || undefined
    };
    setProfile(updatedProfile);
    
    // Soft save - update parent state only
    const cleanedProfile: ProfileSettings = {
      first_name: updatedProfile.first_name?.trim() || undefined,
      last_name: updatedProfile.last_name?.trim() || undefined,
      email: updatedProfile.email?.trim() || undefined
    };
    onChange(cleanedProfile);
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">
          Account Information
        </h3>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Manage your personal profile information
        </p>
      </div>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            First Name
          </label>
          <div className="relative">
            <input
              type="text"
              value={profile.first_name || ''}
              onChange={(e) => handleChange('first_name', e.target.value)}
              placeholder="John"
              className="w-full p-3 pl-10 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent"
            />
            <User className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400 dark:text-gray-500" />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Last Name
          </label>
          <div className="relative">
            <input
              type="text"
              value={profile.last_name || ''}
              onChange={(e) => handleChange('last_name', e.target.value)}
              placeholder="Doe"
              className="w-full p-3 pl-10 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent"
            />
            <User className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400 dark:text-gray-500" />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Email Address
          </label>
          <div className="relative">
            <input
              type="email"
              value={profile.email || ''}
              onChange={(e) => handleChange('email', e.target.value)}
              placeholder="john.doe@example.com"
              className="w-full p-3 pl-10 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent"
            />
            <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400 dark:text-gray-500" />
          </div>
        </div>
      </div>

      {/* Privacy Notice */}
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
        <div className="flex items-start space-x-3">
          <Info className="w-5 h-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
          <div>
            <h4 className="font-medium text-blue-900 dark:text-blue-100 mb-1">Privacy Information</h4>
            <p className="text-sm text-blue-800 dark:text-blue-200">
              All profile information is stored locally on your device and is never transmitted to external servers.
              This information is optional and used only to personalize your experience.
            </p>
          </div>
        </div>
      </div>

      {/* Additional Info Section */}
      <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
        <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Additional Features
        </h4>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Connect your Google Drive account to upload documents directly from your Drive.
          This can be configured in the Google Drive integration section.
        </p>
      </div>
    </div>
  );
};

export default AccountSettings;

