/**
 * useTheme Hook
 * Manages theme application and system theme detection
 */

import { useEffect, useState } from 'react';
import { useSettings } from './useSettings';
import { Theme } from '../types/settings';

export const useTheme = () => {
  const { settings } = useSettings();
  const [systemTheme, setSystemTheme] = useState<'light' | 'dark'>('light');

  // Detect system theme preference
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    
    const handleChange = (e: MediaQueryListEvent) => {
      setSystemTheme(e.matches ? 'dark' : 'light');
    };

    // Set initial value
    setSystemTheme(mediaQuery.matches ? 'dark' : 'light');

    // Listen for changes
    mediaQuery.addEventListener('change', handleChange);

    return () => {
      mediaQuery.removeEventListener('change', handleChange);
    };
  }, []);

  // Apply theme to HTML element
  useEffect(() => {
    if (!settings?.ui?.theme) return;

    const htmlElement = document.documentElement;
    
    // Remove existing theme classes
    htmlElement.classList.remove('light', 'dark');
    
    let effectiveTheme: 'light' | 'dark';
    
    if (settings.ui.theme === 'system') {
      effectiveTheme = systemTheme;
    } else {
      effectiveTheme = settings.ui.theme as 'light' | 'dark';
    }
    
    // Apply the effective theme
    htmlElement.classList.add(effectiveTheme);
    
    // Also set a data attribute for CSS targeting
    htmlElement.setAttribute('data-theme', effectiveTheme);
    
  }, [settings?.ui?.theme, systemTheme]);

  // Get the current effective theme
  const getEffectiveTheme = (): 'light' | 'dark' => {
    if (!settings?.ui?.theme) return 'light';
    
    if (settings.ui.theme === 'system') {
      return systemTheme;
    }
    
    return settings.ui.theme as 'light' | 'dark';
  };

  return {
    currentTheme: settings?.ui?.theme || 'system',
    effectiveTheme: getEffectiveTheme(),
    systemTheme,
    isDark: getEffectiveTheme() === 'dark',
    isLight: getEffectiveTheme() === 'light'
  };
};
