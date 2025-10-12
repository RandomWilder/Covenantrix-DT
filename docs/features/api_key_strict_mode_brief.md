# API Key Strict Mode - Technical Implementation Brief

## Core Principle
**One mode, one key source, no fallback.** User's choice of mode (default/custom) is absolute. Services initialize with available keys or remain disabled with clear messaging.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        APPLICATION STARTUP                   │
├─────────────────────────────────────────────────────────────┤
│ 1. Load .env (system keys)                                  │
│ 2. Load user_settings.json (user keys + mode)               │
│ 3. Resolve keys (strict mode - no fallback)                 │
│ 4. Initialize services (handle None gracefully)             │
│    - OpenAI key present → RAG + Chat enabled                │
│    - Cohere key present → Reranking enabled                 │
│    - Google key present → OCR enabled                       │
│    - Missing keys → Services disabled, clear messaging      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    SETTINGS CHANGE FLOW                      │
├─────────────────────────────────────────────────────────────┤
│ 1. User enters keys in settings UI                          │
│ 2. Validation on blur (per key type)                        │
│ 3. User clicks save                                          │
│ 4. Backend validates ALL provided keys                      │
│ 5. Backend saves to user_settings.json (encrypted)          │
│ 6. Backend reinitializes services with new keys             │
│ 7. Frontend receives success → updates UI state             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                     KEY RESOLUTION LOGIC                     │
├─────────────────────────────────────────────────────────────┤
│ IF mode == "custom":                                         │
│   → Check user_settings.json for key                        │
│   → Return key if exists, else None                         │
│   → NEVER check .env                                        │
│                                                              │
│ IF mode == "default":                                        │
│   → Check .env for key                                      │
│   → Return key if exists, else None                         │
│   → NEVER check user_settings.json                          │
└─────────────────────────────────────────────────────────────┘
```

---

## File Changes

### BACKEND - Core Logic

#### `backend/core/api_key_resolver.py` - MODIFY
**Changes:**
- Remove fallback logic in `_resolve_key()` method
- Strict mode: custom mode → only user key, default mode → only system key
- Return `None` when selected mode has no key (don't cross modes)
- Add detailed logging for debugging

**Key Method Update:**
```python
def _resolve_key(self, key_type: str, user_settings: Dict, fallback_key: str) -> Optional[str]:
    mode = user_settings.get("api_keys", {}).get("mode", "default")
    
    if mode == "custom":
        user_key = user_settings.get("api_keys", {}).get(key_type)
        return user_key if user_key else None  # No fallback
    
    # Default mode: only check system key
    return fallback_key if fallback_key else None  # No fallback
```

---

#### `backend/api/routes/settings.py` - MODIFY
**Changes:**
- Extract validation logic to shared function `validate_api_key(key: str, key_type: str) -> bool`
- Add validation for ALL key types (OpenAI, Cohere, Google) on save
- Validation rules:
  - **Default mode:** Always allow save (even without keys)
  - **Custom mode:** Validate only provided keys (allow partial keys, show warnings)
  - **Invalid keys:** Block save with specific error per key type

**New Endpoint:**
```python
@router.post("/validate-key")
async def validate_single_key(key: str, key_type: str):
    """Validate a single API key by making actual API call"""
    # Make real API call to verify key works
    # Return {valid: bool, error: Optional[str]}
```

---

#### `backend/main.py` - MODIFY
**Changes:**
- Update `lifespan()` to handle `None` keys gracefully
- Don't fail startup if keys missing
- Log which services initialized vs disabled

```python
# If OpenAI key is None → RAG engine = None (disabled)
# If Cohere key is None → Reranker = None (disabled)
# If Google key is None → OCR = None (disabled)
```

---

#### `backend/api/routes/chat.py` - MODIFY
**Changes:**
- Add pre-operation check for valid OpenAI key
- If no key → return 400 with clear message

```python
@router.post("/chat")
async def chat(request: ChatRequest):
    if not rag_engine_available():
        raise HTTPException(400, "OpenAI key not configured. Go to Settings → API Keys")
    # ... proceed with chat
```

---

#### `backend/api/routes/documents.py` - MODIFY
**Changes:**
- Add pre-operation check for valid OpenAI key
- If no key → return 400 with clear message

```python
@router.post("/upload")
async def upload(file: UploadFile):
    if not rag_engine_available():
        raise HTTPException(400, "OpenAI key not configured. Go to Settings → API Keys")
    # ... proceed with upload
```

---

### BACKEND - New Files

#### `backend/api/routes/services.py` - NEW
**Purpose:** Status endpoint for frontend to check service availability

```python
@router.get("/status")
async def get_services_status():
    return {
        "openai_available": rag_engine_available(),
        "cohere_available": reranker_available(),
        "google_available": ocr_available(),
        "features": {
            "chat": rag_engine_available(),
            "upload": rag_engine_available(),
            "reranking": reranker_available(),
            "ocr": ocr_available()
        }
    }
```

---

### FRONTEND - Core Components

#### `covenantrix-desktop/src/contexts/SettingsContext.tsx` - MODIFY
**Changes:**
- Add service status state
- Fetch status after settings save succeeds
- Provide status to all child components

---

#### `covenantrix-desktop/src/features/settings/ApiKeysTab.tsx` - MODIFY
**Changes:**
- Add validation for all key types (OpenAI, Cohere, Google)
- Show warnings for missing optional keys (don't block save)
- Clear messaging per service about what features are disabled
- Validation on blur (already implemented, verify for all keys)

---

#### `covenantrix-desktop/src/features/chat/ChatScreen.tsx` - MODIFY
**Changes:**
- Check service status on mount
- If OpenAI unavailable → show banner: "Chat disabled. Configure OpenAI key in Settings"
- Disable input field
- Provide direct link to settings

---

#### `covenantrix-desktop/src/features/upload/UploadScreen.tsx` - MODIFY
**Changes:**
- Check service status on mount
- If OpenAI unavailable → show banner: "Upload disabled. Configure OpenAI key in Settings"
- Disable upload button
- Provide direct link to settings

---

### FRONTEND - New Files

#### `covenantrix-desktop/src/hooks/useServiceStatus.ts` - NEW
**Purpose:** Reusable hook for checking service availability

```typescript
export function useServiceStatus() {
  const [status, setStatus] = useState<ServiceStatus | null>(null);
  
  useEffect(() => {
    fetchServiceStatus().then(setStatus);
  }, []);
  
  return {
    openaiAvailable: status?.openai_available ?? false,
    cohereAvailable: status?.cohere_available ?? false,
    googleAvailable: status?.google_available ?? false,
    features: status?.features
  };
}
```

---

#### `covenantrix-desktop/src/types/services.ts` - NEW
**Purpose:** TypeScript types for service status

```typescript
export interface ServiceStatus {
  openai_available: boolean;
  cohere_available: boolean;
  google_available: boolean;
  features: {
    chat: boolean;
    upload: boolean;
    reranking: boolean;
    ocr: boolean;
  };
}
```

---

### CONFIGURATION

#### `backend/core/config.py` - MODIFY (Documentation Only)
**Changes:**
- Add comments explaining key resolution behavior
- Document that this provides system fallback keys only
- Clarify resolution happens in `api_key_resolver.py`

---

## Key Architectural Decisions

### 1. Strict Mode Enforcement
- **Location:** `backend/core/api_key_resolver.py`
- **Logic:** One mode → one source → no fallback
- **Rationale:** User's explicit choice must be respected

### 2. Service Graceful Degradation
- **Location:** `backend/main.py` lifespan
- **Logic:** Missing key → service = None → features disabled
- **Rationale:** App remains usable even with partial configuration

### 3. Validation Strategy
- **Location:** `backend/api/routes/settings.py`
- **Logic:** Validate provided keys only, allow partial configs
- **Rationale:** Don't force users to configure everything at once

### 4. Frontend Guard Pattern
- **Location:** Chat/Upload screens
- **Logic:** Check status → show banner → disable features
- **Rationale:** Clear user guidance instead of silent failures

### 5. Status as Source of Truth
- **Location:** `backend/api/routes/services.py`
- **Logic:** Single endpoint, queried on demand
- **Rationale:** Avoid state sync issues, frontend polls when needed

---

## Validation Rules

### Default Mode
- Save **always succeeds** (even with no keys)
- No validation required
- Show info messages about disabled features

### Custom Mode
- Validate **only provided keys**
- Block save if **any provided key is invalid**
- Allow partial configs (e.g., only OpenAI, no Cohere/Google)
- Show warnings for missing optional keys

### Per-Key Validation
- **OpenAI:** Format check + actual API call
- **Cohere:** Format check + actual API call
- **Google:** Format check + actual API call

---

## Error Messaging Examples

### No OpenAI Key
```
⚠️ Chat and Upload Disabled
OpenAI API key not configured. 
→ Go to Settings → API Keys to configure.
```

### No Cohere Key
```
ℹ️ Response Reranking Disabled
Cohere API key not configured. Responses will not be reranked for relevance.
→ Configure Cohere key in Settings for better results.
```

### No Google Key
```
ℹ️ OCR Disabled
Google Vision API key not configured. Image documents cannot be processed.
→ Configure Google key in Settings to enable OCR.
```

### Invalid Custom Key
```
❌ Invalid OpenAI API Key
The provided key is not valid. Please check and try again.
→ Ensure key starts with 'sk-' and is properly copied.
```

---

## Files Summary

### Modified Files (11)
1. `backend/core/api_key_resolver.py` - Remove fallback
2. `backend/api/routes/settings.py` - Add validation
3. `backend/main.py` - Graceful degradation
4. `backend/api/routes/chat.py` - Add guards
5. `backend/api/routes/documents.py` - Add guards
6. `backend/core/config.py` - Documentation
7. `covenantrix-desktop/src/contexts/SettingsContext.tsx` - Status state
8. `covenantrix-desktop/src/features/settings/ApiKeysTab.tsx` - Validation
9. `covenantrix-desktop/src/features/chat/ChatScreen.tsx` - Guards
10. `covenantrix-desktop/src/features/upload/UploadScreen.tsx` - Guards

### New Files (3)
1. `backend/api/routes/services.py` - Status endpoint
2. `covenantrix-desktop/src/hooks/useServiceStatus.ts` - Status hook
3. `covenantrix-desktop/src/types/services.ts` - Types

### Deleted Files (0)
None - we're enhancing existing architecture

---

## Implementation Order

1. **Backend Core** - Fix key resolution (no fallback)
2. **Backend Services** - Graceful degradation on None keys
3. **Backend Validation** - Add validation for all key types
4. **Backend Status** - Add status endpoint
5. **Frontend Hooks** - Add service status hook
6. **Frontend Guards** - Add feature guards to chat/upload
7. **Frontend Settings** - Enhance validation UI
8. **Testing** - Verify all scenarios work correctly