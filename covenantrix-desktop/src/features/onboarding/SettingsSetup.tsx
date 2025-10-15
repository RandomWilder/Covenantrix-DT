/**
 * Settings Setup - First Run Onboarding
 * Guides new users through initial settings configuration
 */

import React, { useState } from 'react';
import { CheckCircle, ArrowRight, Settings, Key, Globe, Brain, Palette, User } from 'lucide-react';
import { useSettings } from '../../contexts/SettingsContext';
import { useToast } from '../../hooks/useToast';
import { UserSettings } from '../../types/settings';
import { getDefaultSettings } from '../../utils/settings';
import { ProfileSetupStep } from './ProfileSetupStep';

interface SettingsSetupProps {
  onComplete: () => void;
  onSkip?: () => void;
}

type SetupStep = 'welcome' | 'profile' | 'api-keys' | 'language' | 'rag' | 'appearance' | 'complete';

const SettingsSetup: React.FC<SettingsSetupProps> = ({ onComplete, onSkip }) => {
  const { settings, updateSettings, validateApiKeys } = useSettings();
  const { showToast } = useToast();
  const [currentStep, setCurrentStep] = useState<SetupStep>('welcome');
  const [isValidating, setIsValidating] = useState(false);
  const [localSettings, setLocalSettings] = useState<Partial<UserSettings>>({});
  const defaults = getDefaultSettings();

  const steps = [
    { id: 'welcome', title: 'Welcome', icon: Settings },
    { id: 'profile', title: 'Profile', icon: User },
    { id: 'api-keys', title: 'API Keys', icon: Key },
    { id: 'language', title: 'Language', icon: Globe },
    { id: 'rag', title: 'AI Config', icon: Brain },
    { id: 'appearance', title: 'Appearance', icon: Palette },
    { id: 'complete', title: 'Complete', icon: CheckCircle }
  ];

  const currentStepIndex = steps.findIndex(step => step.id === currentStep);
  const progress = ((currentStepIndex + 1) / steps.length) * 100;

  // Get effective settings (deep merge to prevent data loss)
  const effectiveSettings: UserSettings = {
    ...settings,
    ...localSettings,
    // Explicitly merge nested objects
    api_keys: localSettings.api_keys ? { ...settings?.api_keys, ...localSettings.api_keys } : settings?.api_keys,
    rag: localSettings.rag ? { ...settings?.rag, ...localSettings.rag } : settings?.rag,
    language: localSettings.language ? { ...settings?.language, ...localSettings.language } : settings?.language,
    ui: localSettings.ui ? { ...settings?.ui, ...localSettings.ui } : settings?.ui,
    profile: localSettings.profile ? { ...settings?.profile, ...localSettings.profile } : settings?.profile,
  } as UserSettings;

  const handleNext = async () => {
    if (currentStep === 'api-keys') {
      // Validate API keys before proceeding
      setIsValidating(true);
      try {
        const isValid = await validateApiKeys();
        if (isValid) {
          setCurrentStep('language');
        } else {
          showToast('Please configure valid API keys to continue', 'error');
          return;
        }
      } catch (error) {
        showToast('Failed to validate API keys', 'error');
        return;
      } finally {
        setIsValidating(false);
      }
    } else if (currentStep === 'complete') {
      await handleComplete();
    } else {
      const nextIndex = currentStepIndex + 1;
      if (nextIndex < steps.length) {
        setCurrentStep(steps[nextIndex].id as SetupStep);
      }
    }
  };

  const handleComplete = async () => {
    try {
      // Merge all local state changes and mark onboarding as completed
      const finalSettings = {
        ...localSettings,
        onboarding_completed: true
      };
      await updateSettings(finalSettings);
      onComplete();
    } catch (error) {
      console.error('Error completing onboarding:', error);
      showToast('Failed to save settings', 'error');
    }
  };

  const handleSkip = async () => {
    try {
      // Mark onboarding as completed even when skipped
      // User chose to skip, so don't show onboarding again
      await updateSettings({ onboarding_completed: true });
      if (onSkip) {
        onSkip();
      } else {
        onComplete();
      }
    } catch (error) {
      console.error('Error skipping onboarding:', error);
      // Still call completion handlers even if save failed
      if (onSkip) {
        onSkip();
      } else {
        onComplete();
      }
    }
  };

  const handleBack = () => {
    const prevIndex = currentStepIndex - 1;
    if (prevIndex >= 0) {
      setCurrentStep(steps[prevIndex].id as SetupStep);
    }
  };

  const handleSettingsChange = (updates: Partial<UserSettings>) => {
    // Update local state only (soft save)
    setLocalSettings(prev => ({ ...prev, ...updates }));
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 'welcome':
        return (
          <div className="text-center space-y-6">
            <div className="w-20 h-20 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center mx-auto">
              <Settings className="w-10 h-10 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                Welcome to Covenantrix
              </h2>
              <p className="text-gray-600 dark:text-gray-400 max-w-md mx-auto">
                Let's set up your preferences to get the best experience with our AI-powered document intelligence platform.
              </p>
            </div>
            <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 max-w-md mx-auto">
              <h3 className="font-semibold text-blue-900 dark:text-blue-100 mb-2">What we'll configure:</h3>
              <ul className="text-sm text-blue-800 dark:text-blue-200 space-y-1">
                <li>• Your profile (optional)</li>
                <li>• API keys for AI services</li>
                <li>• Language preferences</li>
                <li>• AI behavior settings</li>
                <li>• Visual appearance</li>
              </ul>
            </div>
          </div>
        );

      case 'profile':
        return (
          <ProfileSetupStep
            initialProfile={effectiveSettings?.profile}
            onSave={(profile) => handleSettingsChange({ profile })}
          />
        );

      case 'api-keys':
        return (
          <div className="space-y-6">
            <div className="text-center">
              <div className="w-16 h-16 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center mx-auto mb-4">
                <Key className="w-8 h-8 text-green-600 dark:text-green-400" />
              </div>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                Configure API Keys
              </h2>
              <p className="text-gray-600 dark:text-gray-400">
                Set up your API keys to enable AI-powered features
              </p>
            </div>

            <div className="space-y-4">
              <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
                <h3 className="font-medium text-gray-900 dark:text-white mb-2">Default Mode (Recommended)</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                  Use our pre-configured API keys for immediate access to all features.
                </p>
                <button
                  onClick={() => handleSettingsChange({ 
                    api_keys: { mode: 'default' } 
                  })}
                  className={`w-full p-3 rounded-lg border-2 transition-colors ${
                    effectiveSettings?.api_keys?.mode === 'default'
                      ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                      : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'
                  }`}
                >
                  <div className="text-left">
                    <div className="font-medium text-gray-900 dark:text-white">Use Default Keys</div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">Quick setup, ready to use</div>
                  </div>
                </button>
              </div>

              <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
                <h3 className="font-medium text-gray-900 dark:text-white mb-2">Custom Mode</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                  Use your own API keys for full control and potentially better performance.
                </p>
                <button
                  onClick={() => handleSettingsChange({ 
                    api_keys: { mode: 'custom' } 
                  })}
                  className={`w-full p-3 rounded-lg border-2 transition-colors ${
                    effectiveSettings?.api_keys?.mode === 'custom'
                      ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                      : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'
                  }`}
                >
                  <div className="text-left">
                    <div className="font-medium text-gray-900 dark:text-white">Use Custom Keys</div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">Configure your own API keys</div>
                  </div>
                </button>
              </div>
            </div>

            {effectiveSettings?.api_keys?.mode === 'custom' && (
              <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
                <div className="flex items-start space-x-3">
                  <div className="text-yellow-600 dark:text-yellow-400">⚠️</div>
                  <div>
                    <h4 className="font-medium text-yellow-800 dark:text-yellow-200">Custom API Keys Required</h4>
                    <p className="text-sm text-yellow-700 dark:text-yellow-300 mt-1">
                      You'll need to configure your API keys in the settings after setup. 
                      You can access settings anytime from the menu.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        );

      case 'language':
        return (
          <div className="space-y-6">
            <div className="text-center">
              <div className="w-16 h-16 bg-purple-100 dark:bg-purple-900 rounded-full flex items-center justify-center mx-auto mb-4">
                <Globe className="w-8 h-8 text-purple-600 dark:text-purple-400" />
              </div>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                Language Preferences
              </h2>
              <p className="text-gray-600 dark:text-gray-400">
                Choose your preferred language for the interface and AI responses
              </p>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Interface Language
                </label>
                <select
                  value={effectiveSettings?.language?.ui_language || 'auto'}
                  onChange={(e) => handleSettingsChange({
                    language: {
                      ...defaults.language,
                      ...effectiveSettings?.language,
                      ui_language: e.target.value as 'auto' | 'en' | 'es'
                    }
                  })}
                  className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                >
                  <option value="auto">Auto (System Default)</option>
                  <option value="en">English</option>
                  <option value="es">Español</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  AI Response Language
                </label>
                <select
                  value={effectiveSettings?.language?.agent_language || 'auto'}
                  onChange={(e) => handleSettingsChange({
                    language: {
                      ...defaults.language,
                      ...effectiveSettings?.language,
                      agent_language: e.target.value as 'auto' | 'en' | 'es' | 'fr' | 'he' | 'de'
                    }
                  })}
                  className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                >
                  <option value="auto">Auto (Match Query Language)</option>
                  <option value="en">English</option>
                  <option value="es">Español</option>
                  <option value="fr">Français</option>
                  <option value="he">עברית</option>
                  <option value="de">Deutsch</option>
                </select>
              </div>
            </div>
          </div>
        );

      case 'rag':
        return (
          <div className="space-y-6">
            <div className="text-center">
              <div className="w-16 h-16 bg-orange-100 dark:bg-orange-900 rounded-full flex items-center justify-center mx-auto mb-4">
                <Brain className="w-8 h-8 text-orange-600 dark:text-orange-400" />
              </div>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                AI Configuration
              </h2>
              <p className="text-gray-600 dark:text-gray-400">
                Configure how the AI processes and responds to your documents
              </p>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Search Mode
                </label>
                <select
                  value={effectiveSettings?.rag?.search_mode || 'hybrid'}
                  onChange={(e) => handleSettingsChange({
                    rag: {
                      ...defaults.rag,
                      ...effectiveSettings?.rag,
                      search_mode: e.target.value as 'naive' | 'local' | 'global' | 'hybrid'
                    }
                  })}
                  className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                >
                  <option value="hybrid">Hybrid (Recommended)</option>
                  <option value="naive">Naive</option>
                  <option value="local">Local</option>
                  <option value="global">Global</option>
                </select>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Hybrid mode provides the best balance of accuracy and performance
                </p>
              </div>

              <div className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  id="enable-ocr"
                  checked={effectiveSettings?.rag?.enable_ocr ?? true}
                  onChange={(e) => handleSettingsChange({
                    rag: {
                      ...defaults.rag,
                      ...effectiveSettings?.rag,
                      enable_ocr: e.target.checked
                    }
                  })}
                  className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
                />
                <label htmlFor="enable-ocr" className="text-sm text-gray-700 dark:text-gray-300">
                  Enable OCR (Optical Character Recognition)
                </label>
              </div>

              <div className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  id="use-reranking"
                  checked={effectiveSettings?.rag?.use_reranking ?? true}
                  onChange={(e) => handleSettingsChange({
                    rag: {
                      ...defaults.rag,
                      ...effectiveSettings?.rag,
                      use_reranking: e.target.checked
                    }
                  })}
                  className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
                />
                <label htmlFor="use-reranking" className="text-sm text-gray-700 dark:text-gray-300">
                  Use Advanced Reranking (Requires Cohere API)
                </label>
              </div>
            </div>
          </div>
        );

      case 'appearance':
        return (
          <div className="space-y-6">
            <div className="text-center">
              <div className="w-16 h-16 bg-pink-100 dark:bg-pink-900 rounded-full flex items-center justify-center mx-auto mb-4">
                <Palette className="w-8 h-8 text-pink-600 dark:text-pink-400" />
              </div>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                Appearance
              </h2>
              <p className="text-gray-600 dark:text-gray-400">
                Customize the look and feel of your application
              </p>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Theme
                </label>
                <div className="grid grid-cols-3 gap-3">
                  {[
                    { value: 'light', label: 'Light', icon: '☀️' },
                    { value: 'dark', label: 'Dark', icon: '🌙' },
                    { value: 'system', label: 'System', icon: '🖥️' }
                  ].map((theme) => (
                    <button
                      key={theme.value}
                      onClick={() => handleSettingsChange({
                        ui: {
                          ...defaults.ui,
                          ...effectiveSettings?.ui,
                          theme: theme.value as 'light' | 'dark' | 'system'
                        }
                      })}
                      className={`p-3 rounded-lg border-2 transition-colors ${
                        effectiveSettings?.ui?.theme === theme.value
                          ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                          : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'
                      }`}
                    >
                      <div className="text-center">
                        <div className="text-2xl mb-1">{theme.icon}</div>
                        <div className="text-sm font-medium text-gray-900 dark:text-white">{theme.label}</div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              <div className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  id="compact-mode"
                  checked={effectiveSettings?.ui?.compact_mode ?? false}
                  onChange={(e) => handleSettingsChange({
                    ui: {
                      ...defaults.ui,
                      ...effectiveSettings?.ui,
                      compact_mode: e.target.checked
                    }
                  })}
                  className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
                />
                <label htmlFor="compact-mode" className="text-sm text-gray-700 dark:text-gray-300">
                  Compact Mode (Smaller interface elements)
                </label>
              </div>
            </div>
          </div>
        );

      case 'complete':
        return (
          <div className="text-center space-y-6">
            <div className="w-20 h-20 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center mx-auto">
              <CheckCircle className="w-10 h-10 text-green-600 dark:text-green-400" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                Setup Complete!
              </h2>
              <p className="text-gray-600 dark:text-gray-400 max-w-md mx-auto">
                Your Covenantrix application is now configured and ready to use. 
                You can always change these settings later from the settings menu.
              </p>
            </div>
            <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4 max-w-md mx-auto">
              <h3 className="font-semibold text-green-900 dark:text-green-100 mb-2">What's next?</h3>
              <ul className="text-sm text-green-800 dark:text-green-200 space-y-1">
                <li>• Upload your first document</li>
                <li>• Start asking questions about your documents</li>
                <li>• Explore AI-powered insights</li>
                <li>• Customize settings as needed</li>
              </ul>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
              Initial Setup
            </h1>
            <button
              onClick={handleSkip}
              className="text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            >
              Skip Setup
            </button>
          </div>
          
          {/* Progress Bar */}
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
          
          {/* Step Indicators */}
          <div className="flex justify-between mt-4">
            {steps.map((step, index) => {
              const Icon = step.icon;
              const isActive = currentStep === step.id;
              const isCompleted = currentStepIndex > index;
              
              return (
                <div key={step.id} className="flex flex-col items-center space-y-1">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center transition-colors ${
                    isActive 
                      ? 'bg-blue-600 text-white' 
                      : isCompleted 
                        ? 'bg-green-600 text-white' 
                        : 'bg-gray-200 dark:bg-gray-600 text-gray-500 dark:text-gray-400'
                  }`}>
                    <Icon className="w-4 h-4" />
                  </div>
                  <span className={`text-xs font-medium ${
                    isActive 
                      ? 'text-blue-600 dark:text-blue-400' 
                      : 'text-gray-500 dark:text-gray-400'
                  }`}>
                    {step.title}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {renderStepContent()}
        </div>

        {/* Footer */}
        <div className="border-t border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center justify-between">
            <button
              onClick={handleBack}
              disabled={currentStepIndex === 0}
              className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Back
            </button>
            
            <div className="flex items-center space-x-3">
              {currentStep === 'complete' ? (
                <button
                  onClick={handleComplete}
                  className="flex items-center space-x-2 px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                >
                  <CheckCircle className="w-4 h-4" />
                  <span>Get Started</span>
                </button>
              ) : (
                <button
                  onClick={handleNext}
                  disabled={isValidating}
                  className="flex items-center space-x-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {isValidating ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      <span>Validating...</span>
                    </>
                  ) : (
                    <>
                      <span>Next</span>
                      <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsSetup;
