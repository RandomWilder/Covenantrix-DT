/**
 * Navigation Type Definitions
 * Types for screen navigation and routing
 */

/**
 * Available screens in the application
 */
export type Screen = 
  | 'dashboard'
  | 'documents'
  | 'chat'
  | 'graph'
  | 'analytics'
  | 'upload'
  | 'library'
  | 'history';

/**
 * Navigation item structure
 */
export interface NavigationItem {
  icon: any; // Lucide React icon component
  label: string;
  screen: Screen;
}

