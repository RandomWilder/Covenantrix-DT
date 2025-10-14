# Browser-Electron Compatibility Guide

**Status:** ✅ Implemented  
**Date:** October 14, 2025

---

## Overview

This document describes the systematic approach to handling environment differences between **Browser (Vite dev server)** and **Electron** contexts. The solution ensures the app works gracefully in both environments without errors.

---

## Problem Statement

When running the React app in a browser at `http://localhost:5173` (Vite dev server), the `window.electronAPI` object doesn't exist because there's no Electron context. This caused errors in:

- **SettingsContext**: Trying to call `window.electronAPI.getSettings()`
- **NotificationContext**: Trying to call `window.electronAPI.notifications.getAll()` and register event listeners
- **Services**: Trying to access Electron APIs directly

---

## Solution Architecture

### 1. **Environment Detection Utility** (`src/utils/environment.ts`)

Created a centralized utility module for environment detection:

```typescript
/**
 * Check if running in Electron environment
 */
export const isElectron = (): boolean => {
  return typeof window !== 'undefined' && 
         window.electronAPI !== undefined;
};

/**
 * Check if running in browser (Vite dev server)
 */
export const isBrowser = (): boolean => {
  return !isElectron();
};

/**
 * Log with environment context
 */
export const envLog = (message: string, ...args: any[]) => {
  const env = getEnvironmentName();
  console.log(`[${env}] ${message}`, ...args);
};

/**
 * Warn with environment context
 */
export const envWarn = (message: string, ...args: any[]) => {
  const env = getEnvironmentName();
  console.warn(`[${env}] ${message}`, ...args);
};
```

---

### 2. **Service Layer Guards** (`notificationService.ts`)

All service methods check environment before calling Electron APIs:

```typescript
import { isElectron, envWarn } from '../../utils/environment';

export const notificationService = {
  async getAll(): Promise<Notification[]> {
    if (!isElectron()) {
      envWarn('notificationService.getAll: Not in Electron environment, returning empty array');
      return [];
    }
    const result = await window.electronAPI.notifications.getAll();
    return result.notifications || [];
  },
  // ... other methods with same pattern
};
```

---

### 3. **Context Guards** (SettingsContext, NotificationContext)

All contexts check environment in useEffect hooks and API calls:

**SettingsContext Pattern:**
```typescript
import { isElectron, envLog, envWarn } from '../utils/environment';

useEffect(() => {
  if (!isElectron()) {
    envLog('SettingsContext: Running in browser mode, using default settings');
    const defaultSettings = getDefaultSettings();
    setSettings(defaultSettings);
    setIsLoading(false);
    return;
  }
  loadSettings();
}, []);
```

**NotificationContext Pattern:**
```typescript
useEffect(() => {
  if (!isElectron()) {
    envLog('NotificationContext: Skipping Electron event listeners in browser mode');
    return;
  }

  // Register Electron event listeners only when in Electron
  const cleanup = window.electronAPI.onUpdateNotificationCreated(() => {
    fetchNotifications();
  });

  return cleanup;
}, []);
```

---

## Files Modified

### ✅ Created
- `src/utils/environment.ts` - Environment detection utilities

### ✅ Updated
- `src/services/api/notificationService.ts` - Added guards to all methods
- `src/contexts/NotificationContext.tsx` - Added guards to useEffect hooks and handleAction
- `src/contexts/SettingsContext.tsx` - Added guards to all methods and useEffect hooks

---

## Implementation Patterns

### Pattern 1: Service Methods

```typescript
async methodName(...args) {
  if (!isElectron()) {
    envWarn('methodName: Not in Electron, returning fallback');
    return fallbackValue;
  }
  
  return await window.electronAPI.someMethod(...args);
}
```

### Pattern 2: useEffect Hooks

```typescript
useEffect(() => {
  if (!isElectron()) {
    envLog('Component: Skipping in browser mode');
    return;
  }
  
  // Electron-specific logic
  const cleanup = setupElectronListeners();
  return cleanup;
}, []);
```

### Pattern 3: Event Handlers

```typescript
const handleSomeAction = useCallback(async () => {
  if (!isElectron()) {
    envWarn('handleSomeAction: Not in Electron, skipping');
    return;
  }
  
  await window.electronAPI.doSomething();
}, []);
```

---

## Systematic Checklist

### ✅ For All New Contexts

When creating a new context that uses Electron APIs:

1. **Import environment utilities:**
   ```typescript
   import { isElectron, envLog, envWarn } from '../utils/environment';
   ```

2. **Guard all useEffect hooks** that use Electron APIs:
   ```typescript
   useEffect(() => {
     if (!isElectron()) return;
     // Electron logic here
   }, []);
   ```

3. **Guard all methods** that call Electron APIs:
   ```typescript
   const method = useCallback(async () => {
     if (!isElectron()) return fallback;
     return await window.electronAPI.method();
   }, []);
   ```

4. **Provide sensible fallbacks** for browser mode (defaults, empty arrays, etc.)

---

### ✅ For All New Services

When creating a new service that uses Electron APIs:

1. **Import environment utilities**
2. **Add guard to every method**
3. **Return appropriate fallback values**
4. **Log warnings for debugging**

```typescript
import { isElectron, envWarn } from '../../utils/environment';

export const myService = {
  async getData() {
    if (!isElectron()) {
      envWarn('myService.getData: Not in Electron, returning empty array');
      return [];
    }
    return await window.electronAPI.getData();
  }
};
```

---

### ✅ For All New Event Listeners

When registering Electron event listeners:

1. **Always check environment first**
2. **Return early if not Electron**
3. **Return cleanup function**

```typescript
useEffect(() => {
  if (!isElectron()) {
    envLog('Component: Skipping event listeners in browser mode');
    return;
  }
  
  const cleanup = window.electronAPI.onEvent(() => {
    // Handle event
  });
  
  return cleanup;
}, []);
```

---

## Testing Strategy

### Browser Mode (Vite Dev Server)
```bash
cd covenantrix-desktop
npm run dev:vite
```

**Expected behavior:**
- App loads without errors
- Console shows `[Browser]` prefixed messages
- Default settings loaded
- No notifications (empty state)
- All services marked as unavailable
- UI functional but without Electron features

### Electron Mode
```bash
cd covenantrix-desktop
npm run dev
```

**Expected behavior:**
- App loads in Electron window
- Console shows `[Electron]` prefixed messages
- Real settings from secure storage
- Notification system active
- All services status from backend
- Full functionality

---

## Environment Differences

| Feature | Browser Mode | Electron Mode |
|---------|-------------|---------------|
| `window.electronAPI` | ❌ Undefined | ✅ Available |
| Settings | ✅ Defaults only | ✅ From secure storage |
| Notifications | ❌ Empty array | ✅ Real notifications |
| File operations | ❌ Not available | ✅ Full access |
| IPC communication | ❌ Not available | ✅ Full access |
| Service status | ❌ All unavailable | ✅ From backend |
| Update system | ❌ Not available | ✅ Full functionality |

---

## Benefits

### 1. **No More Errors**
- Browser mode doesn't crash when Electron APIs are missing
- Clean, informative console warnings instead of errors

### 2. **Development Flexibility**
- Can develop UI in fast Vite dev server
- Can test full functionality in Electron
- Clear environment indicators in logs

### 3. **Better Error Tracking**
- Environment-prefixed logs (`[Browser]`, `[Electron]`)
- Clear warnings when features unavailable
- Easy debugging

### 4. **Maintainability**
- Single source of truth (`environment.ts`)
- Consistent pattern across codebase
- Easy to add new contexts/services

---

## Code Review Checklist

When reviewing PRs, check that:

- [ ] All new contexts that use Electron APIs import `isElectron`
- [ ] All useEffect hooks with Electron APIs have guards
- [ ] All service methods have environment checks
- [ ] All event listeners check environment
- [ ] Appropriate fallback values provided
- [ ] Console logging uses `envLog`/`envWarn`
- [ ] No direct `window.electronAPI` calls without guards

---

## Anti-Patterns to Avoid

### ❌ BAD: Direct Electron API Call
```typescript
const data = await window.electronAPI.getData();
```

### ✅ GOOD: Guarded Call
```typescript
if (!isElectron()) return fallback;
const data = await window.electronAPI.getData();
```

---

### ❌ BAD: Event Listener Without Guard
```typescript
useEffect(() => {
  const cleanup = window.electronAPI.onEvent(() => {});
  return cleanup;
}, []);
```

### ✅ GOOD: Guarded Event Listener
```typescript
useEffect(() => {
  if (!isElectron()) return;
  const cleanup = window.electronAPI.onEvent(() => {});
  return cleanup;
}, []);
```

---

### ❌ BAD: Silent Failures
```typescript
try {
  await window.electronAPI.method();
} catch (error) {
  // Silently fail
}
```

### ✅ GOOD: Explicit Environment Check
```typescript
if (!isElectron()) {
  envWarn('method: Not in Electron, skipping');
  return fallback;
}
await window.electronAPI.method();
```

---

## Future Enhancements

### Optional: Mock Electron API for Browser Testing

Could create a mock Electron API for browser mode to enable more testing:

```typescript
// src/utils/mockElectronAPI.ts
if (isBrowser()) {
  window.electronAPI = {
    // Mock implementations
    getSettings: async () => ({ success: true, settings: defaults }),
    // ... other mocks
  };
}
```

**Benefits:**
- Test more functionality in browser
- Faster development iterations

**Tradeoffs:**
- More code to maintain
- Could mask real Electron issues

**Decision:** Not implemented yet - current approach preferred for now

---

## Conclusion

The systematic approach using `environment.ts` and consistent guard patterns ensures the app works in both Browser and Electron contexts without errors. All new code should follow these patterns to maintain compatibility.

**Key Principle:** Always check `isElectron()` before calling `window.electronAPI`.

---

## Quick Reference

### Import Statement
```typescript
import { isElectron, envLog, envWarn } from '../utils/environment';
```

### Basic Guard Pattern
```typescript
if (!isElectron()) {
  envWarn('Feature unavailable in browser mode');
  return fallback;
}
// Electron-specific code
```

### useEffect Pattern
```typescript
useEffect(() => {
  if (!isElectron()) return;
  // Electron setup
  return cleanup;
}, []);
```

---

**Status: Implementation Complete ✅**  
**Browser Compatibility: Verified ✅**  
**Electron Compatibility: Maintained ✅**

