/**
 * Appearance Tab
 * Manages UI appearance and display settings
 */

import React, { useEffect } from 'react';
import { Palette, Monitor, Type, Layout, Sun, Moon, ZoomIn, ZoomOut } from 'lucide-react';
import { UISettings, Theme, FontSize } from '../../types/settings';

interface AppearanceTabProps {
  settings: UISettings;
  onChange: (settings: UISettings) => void;
}

const AppearanceTab: React.FC<AppearanceTabProps> = ({ settings, onChange }) => {
  // Apply zoom level when it changes
  useEffect(() => {
    if (window.electronAPI && 'setZoomLevel' in window.electronAPI) {
      (window.electronAPI as any).setZoomLevel(settings.zoom_level);
    }
  }, [settings.zoom_level]);
  const themes: { value: Theme; label: string; description: string; preview: React.ComponentType<any> }[] = [
    { 
      value: 'light', 
      label: 'Light', 
      description: 'Clean and bright interface',
      preview: Sun
    },
    { 
      value: 'dark', 
      label: 'Dark', 
      description: 'Easy on the eyes in low light',
      preview: Moon
    },
    { 
      value: 'system', 
      label: 'System', 
      description: 'Follows your system preference',
      preview: Monitor
    }
  ];

  const fontSizes: { value: FontSize; label: string; description: string }[] = [
    { value: 'small', label: 'Small', description: 'Compact text' },
    { value: 'medium', label: 'Medium', description: 'Standard text size' },
    { value: 'large', label: 'Large', description: 'Larger, easier to read' }
  ];

  const handleThemeChange = (theme: Theme) => {
    onChange({
      ...settings,
      theme
    });
  };

  const handleCompactModeToggle = (compactMode: boolean) => {
    onChange({
      ...settings,
      compact_mode: compactMode
    });
  };

  const handleFontSizeChange = (fontSize: FontSize) => {
    onChange({
      ...settings,
      font_size: fontSize
    });
  };

  const handleZoomLevelChange = (zoomLevel: number) => {
    onChange({
      ...settings,
      zoom_level: zoomLevel
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
          Appearance Settings
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Customize the look and feel of the application interface.
        </p>
      </div>

      {/* Theme Selection */}
      <div className="space-y-4">
        <div className="flex items-center space-x-2">
          <Palette className="w-5 h-5 text-blue-500" />
          <h4 className="text-md font-medium text-gray-900 dark:text-white">
            Theme
          </h4>
        </div>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Choose your preferred color scheme.
        </p>
        <div className="grid grid-cols-3 gap-3">
          {themes.map((theme) => (
            <label
              key={theme.value}
              className={`flex flex-col items-center space-y-2 p-4 border rounded-lg cursor-pointer transition-colors ${
                settings.theme === theme.value
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                  : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'
              }`}
            >
              <input
                type="radio"
                name="theme"
                value={theme.value}
                checked={settings.theme === theme.value}
                onChange={() => handleThemeChange(theme.value)}
                className="w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500"
              />
              <theme.preview className="w-6 h-6 text-gray-600 dark:text-gray-400" />
              <div className="text-center">
                <div className="text-sm font-medium text-gray-900 dark:text-white">
                  {theme.label}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  {theme.description}
                </div>
              </div>
            </label>
          ))}
        </div>
      </div>

      {/* Font Size */}
      <div className="space-y-4">
        <div className="flex items-center space-x-2">
          <Type className="w-5 h-5 text-green-500" />
          <h4 className="text-md font-medium text-gray-900 dark:text-white">
            Font Size
          </h4>
        </div>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Adjust the text size for better readability.
        </p>
        <div className="space-y-2">
          {fontSizes.map((size) => (
            <label
              key={size.value}
              className={`flex items-center space-x-3 p-3 border rounded-lg cursor-pointer transition-colors ${
                settings.font_size === size.value
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                  : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'
              }`}
            >
              <input
                type="radio"
                name="fontSize"
                value={size.value}
                checked={settings.font_size === size.value}
                onChange={() => handleFontSizeChange(size.value)}
                className="w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500"
              />
              <div className="flex-1">
                <div className="text-sm font-medium text-gray-900 dark:text-white">
                  {size.label}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  {size.description}
                </div>
              </div>
            </label>
          ))}
        </div>
      </div>

      {/* Zoom Level */}
      <div className="space-y-4">
        <div className="flex items-center space-x-2">
          <ZoomIn className="w-5 h-5 text-orange-500" />
          <h4 className="text-md font-medium text-gray-900 dark:text-white">
            Zoom Level
          </h4>
        </div>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Adjust the overall size of the application interface. Lower values make everything smaller and fit better on laptop screens.
        </p>
        
        <div className="space-y-4">
          {/* Zoom Slider */}
          <div className="px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-700">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-900 dark:text-white">
                Current Zoom: {(settings.zoom_level * 100).toFixed(0)}%
              </span>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => handleZoomLevelChange(Math.max(0.5, settings.zoom_level - 0.1))}
                  className="p-1 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                  disabled={settings.zoom_level <= 0.5}
                >
                  <ZoomOut className="w-4 h-4" />
                </button>
                <button
                  onClick={() => handleZoomLevelChange(Math.min(2.0, settings.zoom_level + 0.1))}
                  className="p-1 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                  disabled={settings.zoom_level >= 2.0}
                >
                  <ZoomIn className="w-4 h-4" />
                </button>
              </div>
            </div>
            
            <input
              type="range"
              min="0.5"
              max="2.0"
              step="0.1"
              value={settings.zoom_level}
              onChange={(e) => handleZoomLevelChange(parseFloat(e.target.value))}
              className="w-full h-2 bg-gray-200 dark:bg-gray-600 rounded-lg appearance-none cursor-pointer slider"
            />
            
            <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-1">
              <span>50%</span>
              <span>100%</span>
              <span>200%</span>
            </div>
          </div>
          
          {/* Quick Zoom Presets */}
          <div className="grid grid-cols-3 gap-2">
            {[
              { value: 0.8, label: '80%', description: 'Laptop optimized' },
              { value: 1.0, label: '100%', description: 'Standard size' },
              { value: 1.2, label: '120%', description: 'Larger text' }
            ].map((preset) => (
              <button
                key={preset.value}
                onClick={() => handleZoomLevelChange(preset.value)}
                className={`p-3 text-center border rounded-lg transition-colors ${
                  Math.abs(settings.zoom_level - preset.value) < 0.05
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300'
                    : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'
                }`}
              >
                <div className="text-sm font-medium">{preset.label}</div>
                <div className="text-xs text-gray-500 dark:text-gray-400">{preset.description}</div>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Layout Options */}
      <div className="space-y-4">
        <div className="flex items-center space-x-2">
          <Layout className="w-5 h-5 text-purple-500" />
          <h4 className="text-md font-medium text-gray-900 dark:text-white">
            Layout Options
          </h4>
        </div>

        {/* Compact Mode */}
        <div className="flex items-center justify-between p-4 border border-gray-300 dark:border-gray-600 rounded-lg">
          <div className="flex-1">
            <div className="flex items-center space-x-2">
              <span className="text-sm font-medium text-gray-900 dark:text-white">
                Compact Mode
              </span>
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Reduce spacing and padding for a more compact interface
            </p>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={settings.compact_mode}
              onChange={(e) => handleCompactModeToggle(e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
          </label>
        </div>
      </div>

      {/* Preview */}
      <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
        <div className="flex items-center space-x-2 mb-3">
          <Monitor className="w-5 h-5 text-gray-500" />
          <h4 className="text-sm font-medium text-gray-900 dark:text-white">
            Preview
          </h4>
        </div>
        <div className="space-y-2">
          <div className="text-sm text-gray-600 dark:text-gray-400">
            Current settings: {settings.theme} theme, {settings.font_size} font, {settings.compact_mode ? 'compact' : 'normal'} layout, {(settings.zoom_level * 100).toFixed(0)}% zoom
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400">
            Zoom changes are applied immediately, other changes will be applied when you save
          </div>
        </div>
      </div>

      {/* Accessibility Info */}
      <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
        <div className="flex items-start space-x-3">
          <div className="text-blue-500 mt-0.5">♿</div>
          <div>
            <h4 className="text-sm font-medium text-blue-800 dark:text-blue-200">
              Accessibility
            </h4>
            <p className="text-sm text-blue-700 dark:text-blue-300 mt-1">
              Large font size and high contrast themes are available for better accessibility. 
              The system theme option will automatically switch between light and dark based on your OS settings.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AppearanceTab;
