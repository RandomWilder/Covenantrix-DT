/**
 * Profile Setup Step - Onboarding
 * Optional profile information collection during onboarding
 */

import React, { useState } from 'react';
import { User, Mail } from 'lucide-react';
import { ProfileSettings } from '../../types/settings';

interface ProfileSetupStepProps {
  initialProfile?: ProfileSettings;
  onSave: (profile: ProfileSettings) => void;
}

export const ProfileSetupStep: React.FC<ProfileSetupStepProps> = ({ 
  initialProfile, 
  onSave 
}) => {
  const [profile, setProfile] = useState<ProfileSettings>(initialProfile || {
    first_name: '',
    last_name: '',
    email: ''
  });

  const handleChange = (field: keyof ProfileSettings, value: string) => {
    const updatedProfile = {
      ...profile,
      [field]: value || undefined
    };
    setProfile(updatedProfile);
    
    // Auto-save on change - clean up empty strings to undefined
    const cleanedProfile: ProfileSettings = {
      first_name: updatedProfile.first_name?.trim() || undefined,
      last_name: updatedProfile.last_name?.trim() || undefined,
      email: updatedProfile.email?.trim() || undefined
    };
    onSave(cleanedProfile);
  };

  return (
    <div className="space-y-6">
      <div className="text-center">
        <div className="w-16 h-16 bg-indigo-100 dark:bg-indigo-900 rounded-full flex items-center justify-center mx-auto mb-4">
          <User className="w-8 h-8 text-indigo-600 dark:text-indigo-400" />
        </div>
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
          Profile Information
        </h2>
        <p className="text-gray-600 dark:text-gray-400">
          Tell us a bit about yourself (optional)
        </p>
      </div>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            First Name (Optional)
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
            Last Name (Optional)
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
            Email (Optional)
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

      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
        <div className="flex items-start space-x-3">
          <div className="text-blue-600 dark:text-blue-400">ℹ️</div>
          <div>
            <h4 className="font-medium text-blue-800 dark:text-blue-200">Google Drive Integration</h4>
            <p className="text-sm text-blue-700 dark:text-blue-300 mt-1">
              You can connect your Google Drive later from Profile settings to upload documents directly from your Drive.
            </p>
          </div>
        </div>
      </div>

      <div className="text-center text-xs text-gray-500 dark:text-gray-400">
        All fields are optional. This information is stored locally on your device.
      </div>
    </div>
  );
};

