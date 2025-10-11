/**
 * Authentication Type Definitions
 * Structure for future cloud auth, stub implementation for MVP
 */

import { SubscriptionTier } from './subscription';

export interface User {
  id: string;
  email?: string;  // Optional for local users
  name: string;
  tier: SubscriptionTier;
  createdAt: Date;
  preferences: UserPreferences;
}

export interface UserPreferences {
  theme?: 'light' | 'dark' | 'system';
  compactMode?: boolean;
  notifications?: boolean;
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

export interface AuthContextValue {
  authState: AuthState;
  login: (credentials: any) => Promise<void>;
  logout: () => Promise<void>;
  updateProfile: (updates: Partial<User>) => Promise<void>;
}