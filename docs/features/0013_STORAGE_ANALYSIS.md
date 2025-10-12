# Storage & Encryption Analysis - Critical Issues Found

## Executive Summary

**The custom API key system has fundamental architecture problems that prevent it from working correctly.**

### Key Findings:

1. ✅ **Storage Strategy**: Dual storage (Electron + Backend) with encryption is acceptable
2. ❌ **Encryption Mismatch**: Electron and Backend use DIFFERENT encryption keys
3. ❌ **Startup Key Persistence**: RAG engine initialized at startup with .env key persists
4. ❌ **No Reload on Restart**: Restarting app doesn't trigger RAG reload flow
5. ❌ **Environment Variable Pollution**: `os.environ["OPENAI_API_KEY"]` set at startup never updates

## Current Storage Architecture

### Two Separate Storage Systems:

**1. Electron Store** (Frontend-side)
- **Location**: `C:\Users\Asaf\AppData\Roaming\covenantrix-desktop\covenantrix-settings.json`
- **Encryption**: electron-store with AES encryption
- **Key Derivation**: `SHA256(machineId + 'covenantrix-settings')`
- **Purpose**: UI state persistence

**2. Backend Storage** (Python-side)
- **Location**: `C:\Users\Asaf\.covenantrix\rag_storage\user_settings.json`
- **Encryption**: Fernet (AES-128 in CBC mode) via cryptography library
- **Key Derivation**: `PBKDF2(COMPUTERNAME-USERPROFILE, 100k iterations)`
- **Purpose**: Service configuration

### Found User Settings:
```json
{
  "api_keys": {
    "mode": "custom",
    "openai": "Z0FBQUFBQm82N2U2...==",  // Encrypted by backend
    "cohere": null,
    "google": null
  }
}
```

## Critical Problems

### Problem 1: Encryption Key Mismatch

**Electron (JavaScript)**:
```javascript
const machineIdValue = machineId()
const encryptionKey = crypto.createHash('sha256')
  .update(machineIdValue + 'covenantrix-settings')
  .digest('hex')
```

**Backend (Python)**:
```python
def _get_machine_id(self) -> str:
    computer_name = os.environ.get("COMPUTERNAME", "unknown")
    user_profile = os.environ.get("USERPROFILE", "unknown")
    return f"{computer_name}-{user_profile}"

# Then PBKDF2 with 100k iterations
```

**Result**: Different encryption keys mean:
- ❌ Electron-encrypted data cannot be decrypted by backend
- ❌ Backend-encrypted data cannot be decrypted by Electron
- ✅ Currently "works" because both store separately and don't cross-decrypt

**Why it hasn't failed yet**: The backend receives **plain-text** keys from Electron POST request, then encrypts them with its own key for storage.

### Problem 2: RAG Engine Lifecycle Issue

**At Startup** (`main.py` lifespan):
```python
# Line 50-75
user_settings = await user_settings_storage.load_settings()
resolved_openai_key = api_key_resolver.resolve_openai_key(...)
rag_engine = RAGEngine(api_key=resolved_openai_key, ...)
await rag_engine.initialize()
set_rag_engine(rag_engine)  # Global singleton
```

**Sets environment variable**:
```python
# rag_engine.py line 62
os.environ["OPENAI_API_KEY"] = self.api_key
```

**On Settings Save**:
```python
# settings.py apply endpoint
if mode == "custom":
    reload_success = await reload_rag_with_settings()
    # Creates NEW RAG engine instance
    # Sets NEW global singleton
```

**After App Restart**:
- App restarts → `lifespan()` runs → Loads from `user_settings.json` (encrypted backend storage)
- ✅ Custom key IS loaded and decrypted
- ✅ RAG engine IS created with custom key
- ❓ **Why is it using wrong key then?**

### Problem 3: The "sks-proj" Mystery

From your log:
```
'Incorrect API key provided: sks-proj...'  // Extra 's'!
```

vs the correct key you entered:
```
openai: 'sk-proj-MY7z3...'  // Line 920 in log
```

**This indicates**:
1. Key is being loaded correctly (line 920 shows plain decrypted key)
2. But somewhere between load and use, it gets corrupted
3. The 's' prefix suggests string concatenation error or encoding issue

### Potential Root Cause:

Looking at `RAGEngine.__init__()`:
```python
# Line 55
self.api_key = api_key or settings.openai.api_key
```

If `api_key` parameter is falsy (empty string, None), it falls back to `.env` key!

**Hypothesis**: The decrypted key from storage might be:
- Empty string
- Corrupted during decryption
- Not properly passed to RAG engine constructor

## Storage Best Practices Review

### Current Approach:
- ❌ Dual storage with different encryption (complexity, sync issues)
- ❌ Keys encrypted twice (once by Electron, once by backend)
- ❌ No single source of truth
- ❌ Restart doesn't preserve runtime state properly

### Industry Best Practice:
1. **Single Source of Truth**: Backend should be authoritative
2. **Encryption**: Encrypt once at rest, decrypt on load, use plain in memory
3. **Key Storage**: OS-level keychain/credential manager for sensitive data
   - Windows: DPAPI (Data Protection API)
   - macOS: Keychain
   - Linux: Secret Service API (libsecret)
4. **No Double Encryption**: Encrypt at storage layer only
5. **Clear Lifecycle**: 
   - Load once at startup
   - Store once on change
   - Reload services explicitly

## Recommended Architecture

### Option A: Backend as Single Source (Recommended)

**Flow**:
1. User enters key in UI
2. UI sends to Electron IPC
3. Electron forwards to backend API (plain text over localhost)
4. Backend encrypts and stores in `user_settings.json`
5. Backend reloads services immediately
6. Electron UI updated with success
7. On restart: Backend loads from storage, services initialize

**Benefits**:
- Single encryption layer (backend only)
- Single storage location
- Clear data flow
- Backend controls service lifecycle

**Changes Needed**:
1. Remove Electron encryption/storage for API keys
2. Electron only stores UI preferences locally
3. Backend handles all sensitive data
4. Clear separation of concerns

### Option B: OS Keychain Integration (Industry Standard)

**Libraries**:
- Node: `keytar` (Electron-native)
- Python: `keyring` library

**Flow**:
1. Store keys in OS-native credential manager
2. Both Electron and backend read from same keychain
3. No custom encryption needed
4. Platform handles security

**Benefits**:
- OS-level security
- Single source of truth
- No custom crypto
- Works across reboots

## Immediate Diagnostic Steps

To find the exact issue causing "sks-proj" corruption:

### 1. Check Decryption Output
```python
# In api_key_resolver.py line 115
decrypted_key = self.api_key_manager.decrypt_key(user_key)
logger.info(f"DECRYPTED KEY LENGTH: {len(decrypted_key)}")
logger.info(f"DECRYPTED KEY STARTS WITH: {decrypted_key[:10]}")
```

### 2. Check RAG Engine Receives Correct Key
```python
# In rag_engine.py line 55
self.api_key = api_key or settings.openai.api_key
logger.info(f"RAG ENGINE RECEIVED KEY LENGTH: {len(self.api_key)}")
logger.info(f"RAG ENGINE KEY STARTS WITH: {self.api_key[:10]}")
```

### 3. Check Environment Variable
```python
# In rag_engine.py line 62
os.environ["OPENAI_API_KEY"] = self.api_key
logger.info(f"SET ENV VAR LENGTH: {len(os.environ['OPENAI_API_KEY'])}")
```

### 4. Check What OpenAI Client Gets
```python
# In rag_engine.py line 78
client = AsyncOpenAI(api_key=self.api_key)
logger.info(f"OPENAI CLIENT CREATED WITH KEY LENGTH: {len(self.api_key)}")
```

## Chat Endpoint Review

**File**: `backend/api/routes/chat.py`

The chat endpoint uses RAG engine from dependency injection:
```python
rag_engine: RAGEngine = Depends(get_rag_engine)
```

This returns the **global singleton** set by `set_rag_engine()`.

**Potential Issue**: If the singleton wasn't updated after settings change, it still has the old key.

### Verify Singleton Update:
```python
# backend/core/dependencies.py
def set_rag_engine(engine: RAGEngine) -> None:
    global _rag_engine
    _rag_engine = engine
    logger.info(f"RAG ENGINE GLOBAL UPDATED - KEY LENGTH: {len(engine.api_key)}")
```

## Embedding Model Confirmation

From `rag_engine.py` line 80-86:
```python
async def embedding_func(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for texts using text-embedding-3-large"""
    response = await client.embeddings.create(
        model="text-embedding-3-large",
        input=texts
    )
    return [item.embedding for item in response.data]
```

✅ **Correct**: Using `text-embedding-3-large` with 3072 dimensions
✅ **Client**: Created with `AsyncOpenAI(api_key=self.api_key)`

**The embedding function DOES get the API key** - it's passed via the client created in line 78.

## Root Cause Hypothesis

Based on the "sks-proj" error (extra 's'), I suspect:

1. **Decryption might be failing** and returning corrupted data
2. **Or**: An old environment variable is being used somewhere
3. **Or**: LightRAG is reading from `os.environ` instead of using the client we provide

### Check LightRAG Internal Behavior:

LightRAG might be creating its own OpenAI client and reading from environment:
```python
# Somewhere in LightRAG internals
client = OpenAI()  # No api_key param = reads from env
```

**Solution**: Ensure LightRAG uses our provided functions, not its own clients.

## Action Plan

### Immediate Fix (Today):
1. Add detailed logging at every key transformation point
2. Verify decryption is working correctly
3. Check if LightRAG is using environment variable instead of our client
4. Verify singleton update happens when settings change

### Short-term Fix (This Week):
1. Simplify storage: Backend-only for API keys
2. Remove Electron encryption for sensitive data
3. Ensure RAG engine reloads properly on settings change
4. Add startup log showing which key source is active

### Long-term Fix (Next Sprint):
1. Migrate to OS keychain for secure storage
2. Implement proper key rotation support
3. Add settings sync status indicator in UI
4. Comprehensive integration tests for key lifecycle

## Files Requiring Changes

### Immediate Diagnostic Logging:
1. `backend/core/api_key_resolver.py` - Log decrypted key length/prefix
2. `backend/infrastructure/ai/rag_engine.py` - Log received key
3. `backend/core/dependencies.py` - Log singleton updates
4. `backend/api/routes/settings.py` - Log reload operations

### Architecture Simplification:
1. `covenantrix-desktop/electron/ipc-handlers.js` - Remove API key storage
2. `backend/infrastructure/storage/user_settings_storage.py` - Single encryption point
3. `backend/main.py` - Enhanced startup logging
4. `backend/core/config.py` - Document storage strategy


