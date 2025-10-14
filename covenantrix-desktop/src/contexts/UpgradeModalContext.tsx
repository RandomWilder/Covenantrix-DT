/**
 * Upgrade Modal Context
 * Provides global access to upgrade modal
 */

import React, { createContext, useContext, useState, useCallback } from 'react';
import { UpgradeModal } from '../features/subscription/UpgradeModal';

interface UpgradeModalOptions {
  title: string;
  message: string;
  currentTier?: string;
  details?: string;
}

interface UpgradeModalContextValue {
  showUpgradeModal: (options: UpgradeModalOptions) => void;
  hideUpgradeModal: () => void;
}

const UpgradeModalContext = createContext<UpgradeModalContextValue | undefined>(undefined);

export const UpgradeModalProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [modalOptions, setModalOptions] = useState<UpgradeModalOptions>({
    title: '',
    message: ''
  });

  const showUpgradeModal = useCallback((options: UpgradeModalOptions) => {
    setModalOptions(options);
    setIsOpen(true);
  }, []);

  const hideUpgradeModal = useCallback(() => {
    setIsOpen(false);
  }, []);

  const value: UpgradeModalContextValue = {
    showUpgradeModal,
    hideUpgradeModal
  };

  return (
    <UpgradeModalContext.Provider value={value}>
      {children}
      <UpgradeModal
        isOpen={isOpen}
        onClose={hideUpgradeModal}
        title={modalOptions.title}
        message={modalOptions.message}
        currentTier={modalOptions.currentTier}
        details={modalOptions.details}
      />
    </UpgradeModalContext.Provider>
  );
};

export const useUpgradeModal = (): UpgradeModalContextValue => {
  const context = useContext(UpgradeModalContext);
  if (!context) {
    throw new Error('useUpgradeModal must be used within UpgradeModalProvider');
  }
  return context;
};

