/**
 * Language Tab
 * Manages language preferences for UI and AI responses
 */

import React from 'react';
import { Globe, Bot, Monitor, Flag } from 'lucide-react';
import { LanguageSettings, Language } from '../../types/settings';

interface LanguageTabProps {
  settings: LanguageSettings;
  onChange: (settings: LanguageSettings) => void;
}

const LanguageTab: React.FC<LanguageTabProps> = ({ settings, onChange }) => {
  const languages: { value: Language; label: string; flag: React.ComponentType<any> }[] = [
    { value: 'en', label: 'English', flag: Flag },
    { value: 'es', label: 'Español', flag: Flag },
    { value: 'fr', label: 'Français', flag: Flag },
    { value: 'he', label: 'עברית', flag: Flag },
    { value: 'de', label: 'Deutsch', flag: Flag }
  ];

  const uiLanguages = [
    { value: 'auto', label: 'Auto-detect', flag: Globe },
    { value: 'en', label: 'English', flag: Flag },
    { value: 'es', label: 'Español', flag: Flag }
  ];

  const handlePreferredLanguageChange = (language: Language) => {
    onChange({
      ...settings,
      preferred: language
    });
  };

  const handleAgentLanguageChange = (language: 'auto' | Language) => {
    onChange({
      ...settings,
      agent_language: language
    });
  };

  const handleUILanguageChange = (language: 'auto' | 'en' | 'es') => {
    onChange({
      ...settings,
      ui_language: language
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
          Language Preferences
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Configure language settings for the interface and AI responses.
        </p>
      </div>

      {/* Preferred Language */}
      <div className="space-y-4">
        <div className="flex items-center space-x-2">
          <Globe className="w-5 h-5 text-blue-500" />
          <h4 className="text-md font-medium text-gray-900 dark:text-white">
            Preferred Language
          </h4>
        </div>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Your primary language for AI responses and document processing.
        </p>
        <div className="grid grid-cols-2 gap-3">
          {languages.map((lang) => (
            <label
              key={lang.value}
              className={`flex items-center space-x-3 p-3 border rounded-lg cursor-pointer transition-colors ${
                settings.preferred === lang.value
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                  : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'
              }`}
            >
              <input
                type="radio"
                name="preferredLanguage"
                value={lang.value}
                checked={settings.preferred === lang.value}
                onChange={() => handlePreferredLanguageChange(lang.value)}
                className="w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500"
              />
              <lang.flag className="w-5 h-5 text-gray-600 dark:text-gray-400" />
              <span className="text-sm font-medium text-gray-900 dark:text-white">
                {lang.label}
              </span>
            </label>
          ))}
        </div>
      </div>

      {/* Agent Language */}
      <div className="space-y-4">
        <div className="flex items-center space-x-2">
          <Bot className="w-5 h-5 text-green-500" />
          <h4 className="text-md font-medium text-gray-900 dark:text-white">
            AI Agent Language
          </h4>
        </div>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Language for AI agent responses. Auto-detect uses your preferred language.
        </p>
        <div className="space-y-2">
          <label className="flex items-center space-x-3 p-3 border rounded-lg cursor-pointer transition-colors">
            <input
              type="radio"
              name="agentLanguage"
              value="auto"
              checked={settings.agent_language === 'auto'}
              onChange={() => handleAgentLanguageChange('auto')}
              className="w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500"
            />
            <span className="text-2xl">🌐</span>
            <div>
              <div className="text-sm font-medium text-gray-900 dark:text-white">
                Auto-detect
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400">
                Use preferred language
              </div>
            </div>
          </label>
          
          {languages.map((lang) => (
            <label
              key={lang.value}
              className="flex items-center space-x-3 p-3 border rounded-lg cursor-pointer transition-colors"
            >
              <input
                type="radio"
                name="agentLanguage"
                value={lang.value}
                checked={settings.agent_language === lang.value}
                onChange={() => handleAgentLanguageChange(lang.value)}
                className="w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500"
              />
              <lang.flag className="w-5 h-5 text-gray-600 dark:text-gray-400" />
              <span className="text-sm font-medium text-gray-900 dark:text-white">
                {lang.label}
              </span>
            </label>
          ))}
        </div>
      </div>

      {/* UI Language */}
      <div className="space-y-4">
        <div className="flex items-center space-x-2">
          <Monitor className="w-5 h-5 text-purple-500" />
          <h4 className="text-md font-medium text-gray-900 dark:text-white">
            Interface Language
          </h4>
        </div>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Language for the application interface. Currently supports English and Spanish.
        </p>
        <div className="space-y-2">
          {uiLanguages.map((lang) => (
            <label
              key={lang.value}
              className={`flex items-center space-x-3 p-3 border rounded-lg cursor-pointer transition-colors ${
                settings.ui_language === lang.value
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                  : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'
              }`}
            >
              <input
                type="radio"
                name="uiLanguage"
                value={lang.value}
                checked={settings.ui_language === lang.value}
                onChange={() => handleUILanguageChange(lang.value as 'auto' | 'en' | 'es')}
                className="w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500"
              />
              <lang.flag className="w-5 h-5 text-gray-600 dark:text-gray-400" />
              <span className="text-sm font-medium text-gray-900 dark:text-white">
                {lang.label}
              </span>
            </label>
          ))}
        </div>
      </div>

      {/* Language Info */}
      <div className="p-4 bg-amber-50 dark:bg-amber-900/20 rounded-lg">
        <div className="flex items-start space-x-3">
          <div className="text-amber-500 mt-0.5">ℹ️</div>
          <div>
            <h4 className="text-sm font-medium text-amber-800 dark:text-amber-200">
              Language Support
            </h4>
            <p className="text-sm text-amber-700 dark:text-amber-300 mt-1">
              The AI will respond in your preferred language. For best results, ensure your documents are in the same language as your preference. Interface language changes will take effect after restarting the application.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LanguageTab;
