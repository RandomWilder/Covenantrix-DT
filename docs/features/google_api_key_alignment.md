# Google API Key Alignment Plan

## Overview
Align Google API key implementation with the existing OpenAI API key pattern to provide a consistent, user-friendly approach for managing Google Cloud services (Vision API for OCR, future Drive integration, etc.).

## Reasoning
- **Single key architecture**: One Google Cloud API key can access multiple services (Vision, Drive, Translate) - no need for separate keys
- **Consistency**: Users already understand the OpenAI two-mode pattern (default vs custom)
- **Future-proof**: Easy to add more Google services without infrastructure changes
- **Minimal changes**: Leverage existing encryption, storage, and validation infrastructure

---

## Implementation Steps

### Step 1: Rename Backend Configuration Field

**File**: `backend/core/config.py`

**Action**: Rename field to be service-agnostic

```python
# CHANGE FROM:
google_vision_api_key: Optional[str] = Field(None, env="GOOGLE_VISION_API_KEY")

# CHANGE TO:
google_api_key: Optional[str] = Field(None, env="GOOGLE_API_KEY")

# Keep feature toggles separate (no changes needed):
google_vision_enabled: bool = Field(False, env="GOOGLE_VISION_ENABLED")
```

**Rationale**: Reflects that one key serves multiple Google services

---

### Step 2: Update Settings Schema

**File**: `backend/api/schemas/settings.py`

**Action**: Verify `ApiKeySettings` model alignment

```python
class ApiKeySettings(BaseModel):
    """API key configuration"""
    mode: ApiKeyMode = Field(default=ApiKeyMode.DEFAULT, description="API key mode")
    openai: Optional[str] = Field(default=None, description="OpenAI API key (custom mode only)")
    cohere: Optional[str] = Field(default=None, description="Cohere API key (custom mode only)")
    google: Optional[str] = Field(default=None, description="Google Cloud API key (custom mode only)")  # ← VERIFY THIS EXISTS
```

**Check**: If field is named `google_vision`, rename to `google` for consistency

**Rationale**: Schema should mirror config naming (generic, not service-specific)

---

### Step 3: Update Environment Variable Reference

**File**: `backend/.env`

**Action**: Rename environment variable

```bash
# CHANGE FROM:
# GOOGLE_VISION_API_KEY=your_key_here

# CHANGE TO:
GOOGLE_API_KEY=your_key_here

# Keep feature flag:
GOOGLE_VISION_ENABLED=true
```

**Rationale**: Matches new config field name

---

### Step 4: Add Google API Key to UI

**File**: `covenantrix-desktop/src/features/settings/ApiKeyManagement.tsx`

**Action**: Add Google Cloud API key input field following the existing OpenAI/Cohere pattern

**Location**: Inside the "Custom Keys Section" (where OpenAI and Cohere inputs are)

```tsx
{/* Google Cloud Key - ADD THIS BLOCK */}
<div>
  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
    Google Cloud API Key
  </label>
  <div className="relative">
    <input
      type={showKeys.google ? 'text' : 'password'}
      value={settings.google || ''}
      onChange={(e) => handleKeyChange('google', e.target.value)}
      onBlur={(e) => validateKey('google', e.target.value)}
      placeholder="AIzaSy..."
      className="w-full px-3 py-2 pr-20 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:text-white"
    />
    <div className="absolute right-2 top-1/2 transform -translate-y-1/2 flex items-center space-x-1">
      {getValidationIcon(validationStatus.google)}
      <button
        type="button"
        onClick={() => toggleKeyVisibility('google')}
        className="p-1 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
      >
        {showKeys.google ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
      </button>
    </div>
  </div>
  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
    Used for Vision API (OCR), Drive integration, and other Google Cloud services
  </p>
</div>
```

**Additional changes in same file**:
1. Add `google` to `showKeys` state
2. Add `google` to `validationStatus` state  
3. Update `handleKeyChange` to handle 'google' case
4. Update `toggleKeyVisibility` to handle 'google' case

**Rationale**: Follows exact pattern of OpenAI/Cohere inputs for consistency

---

### Step 5: Update TypeScript Types

**File**: `covenantrix-desktop/src/types/settings.ts`

**Action**: Verify interface alignment

```typescript
export interface ApiKeySettings {
  mode: 'default' | 'custom';
  openai?: string;
  cohere?: string;
  google?: string;  // ← VERIFY THIS EXISTS (not google_vision)
}
```

**Check**: If field is named `google_vision`, rename to `google`

**Rationale**: Frontend types must match backend schema

---

### Step 6: Update API Key Validation Hook

**File**: `covenantrix-desktop/src/hooks/useSettings.ts`

**Action**: Add Google API key to validation logic

**In `validateApiKeys` function**, ensure Google key is validated:

```typescript
// Validate Google key
if (context.settings.api_keys.google) {
  results.google = await validateApiKey('google', context.settings.api_keys.google);
}
```

**In validation results type**, ensure `google` field exists:
```typescript
const results: {
  openai: ValidationResult | null;
  cohere: ValidationResult | null;
  google: ValidationResult | null;  // ← ADD THIS
} = {
  openai: null,
  cohere: null,
  google: null
};
```

**Rationale**: Enables real-time validation of Google API keys

---

### Step 7: Update Backend API Key Validation

**File**: `backend/api/routes/settings.py` (or wherever API key validation is handled)

**Action**: Add validation endpoint support for Google API keys

**In the validation logic**, add Google key validation case:

```python
def validate_google_api_key(api_key: str) -> bool:
    """Validate Google Cloud API key"""
    try:
        # Simple validation: make a minimal API call to Vision API
        url = "https://vision.googleapis.com/v1/images:annotate"
        response = requests.get(f"{url}?key={api_key}")
        # Key is valid if we don't get 403/401
        return response.status_code != 403 and response.status_code != 401
    except Exception:
        return False
```

**Note**: If validation endpoint doesn't exist yet, this can be added later. The key will still work without validation, just won't show checkmark/error icon in UI.

---

### Step 8: Update OCR Service to Use New Key

**File**: Any file where Google Vision API is called (likely in document processing)

**Action**: Update references from `google_vision_api_key` to `google_api_key`

```python
# CHANGE FROM:
vision_key = settings.google_vision_api_key

# CHANGE TO:
vision_key = settings.google_api_key
```

**Search for**: `google_vision_api_key` across entire backend codebase and replace with `google_api_key`

**Rationale**: Ensures OCR functionality works with renamed field

---

### Step 9: Update Settings Context (if needed)

**File**: `covenantrix-desktop/src/contexts/SettingsContext.tsx`

**Action**: Verify default settings structure includes Google key

```typescript
const defaultSettings: UserSettings = {
  api_keys: {
    mode: 'default',
    openai: undefined,
    cohere: undefined,
    google: undefined,  // ← VERIFY THIS EXISTS
  },
  // ... rest of settings
};
```

**Rationale**: Ensures proper initialization of Google API key state

---

## Verification Checklist

After implementation, verify:

- [ ] Backend config uses `google_api_key` (not `google_vision_api_key`)
- [ ] Settings schema uses `google` field (not `google_vision`)
- [ ] `.env` uses `GOOGLE_API_KEY` variable
- [ ] UI has Google API key input in ApiKeyManagement component
- [ ] Input follows OpenAI/Cohere pattern exactly
- [ ] TypeScript types align with backend schema
- [ ] Key visibility toggle works for Google key
- [ ] Key validation hook includes Google key
- [ ] OCR service uses new `google_api_key` field
- [ ] No references to old `google_vision_api_key` remain in codebase

---

## Testing Steps

1. **Default Mode**: Start app, ensure OCR works with `.env` key
2. **Custom Mode**: Switch to custom, add Google API key via UI
3. **Validation**: Enter invalid key, verify error icon appears
4. **Persistence**: Restart app, verify custom key persists
5. **OCR**: Upload document, verify OCR works with custom key
6. **Encryption**: Check that key is encrypted in electron-store

---

## Future Extensibility

With this pattern in place, adding new Google services is trivial:

**For Google Drive**:
1. Enable Drive API in user's Google Cloud project
2. Add `google_drive_enabled` feature flag
3. Use existing `google_api_key` field
4. No UI or storage changes needed

**Same for any Google service** (Translate, Maps, etc.)

---

## Summary

**Files to Modify** (8 files):
1. `backend/core/config.py` - rename field
2. `backend/api/schemas/settings.py` - verify field name
3. `backend/.env` - rename env var
4. `covenantrix-desktop/src/features/settings/ApiKeyManagement.tsx` - add UI input
5. `covenantrix-desktop/src/types/settings.ts` - verify interface
6. `covenantrix-desktop/src/hooks/useSettings.ts` - add validation
7. `covenantrix-desktop/src/contexts/SettingsContext.tsx` - verify defaults
8. Backend OCR service files - update references

**Files to Add**: None (leverage existing infrastructure)

**Estimated effort**: 30-45 minutes for a developer familiar with the codebase

**Risk level**: Low (follows established pattern, minimal new code)