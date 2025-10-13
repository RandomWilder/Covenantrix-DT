/**
 * Profile Modal Component
 * Main modal for managing user profile, connected accounts, and API keys
 */

import React, { useState } from 'react';
import { X, User, Cloud, Key } from 'lucide-react';
import { UserInfoTab } from './tabs/UserInfoTab';
import { ConnectedAccountsTab } from './tabs/ConnectedAccountsTab';
import { ProfileApiKeysTab } from './tabs/ApiKeysTab';

interface ProfileModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialTab?: 'user-info' | 'accounts' | 'api-keys';
}

type TabId = 'user-info' | 'accounts' | 'api-keys';

const ProfileModal: React.FC<ProfileModalProps> = ({ 
  isOpen, 
  onClose, 
  initialTab = 'user-info' 
}) => {
  const [activeTab, setActiveTab] = useState<TabId>(initialTab);

  if (!isOpen) return null;

  const tabs = [
    { id: 'user-info' as TabId, label: 'User Info', icon: User },
    { id: 'accounts' as TabId, label: 'Connected Accounts', icon: Cloud },
    { id: 'api-keys' as TabId, label: 'API Keys', icon: Key }
  ];

  const renderTabContent = () => {
    switch (activeTab) {
      case 'user-info':
        return <UserInfoTab />;
      case 'accounts':
        return <ConnectedAccountsTab />;
      case 'api-keys':
        return <ProfileApiKeysTab />;
      default:
        return null;
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] flex flex-col" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            Profile & Settings
          </h2>
          <button
            onClick={onClose}
            className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            title="Close"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="flex border-b border-gray-200 dark:border-gray-700">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 px-6 py-4 font-medium transition-colors ${
                  isActive
                    ? 'text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400'
                    : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700/50'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Tab Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {renderTabContent()}
        </div>
      </div>
    </div>
  );
};

export default ProfileModal;

