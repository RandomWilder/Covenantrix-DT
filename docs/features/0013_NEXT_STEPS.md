# API Key Resolution - Diagnostic & Fix Plan

## Current Status

**Problem**: After saving custom API key via UI and restarting app, system still uses `.env` key (which is malformed as "sks-proj" instead of "sk-proj").

**Root Cause**: Unknown - need diagnostics to identify where key corruption occurs.

## What We Know

### ✅ Working Components:
1. Key is saved to backend storage (`~/.covenantrix/rag_storage/user_settings.json`)
2. Key is encrypted correctly (Fernet encryption)
3. Key appears to load correctly at startup (log shows decrypted key)

### ❌ The Mystery:
- Correct key: `sk-proj-MY7z3...` (shown in log line 920)
- Used key: `sks-proj-...` (error in log line 985)
- **Extra 's'** suggests string manipulation bug or corruption

## Diagnostic Logging Added

I've added detailed logging at every key transformation point:

### 1. Key Resolution (`backend/core/api_key_resolver.py`)
```python
logger.info(f"[DEBUG] Decrypted key length: {len(decrypted_key)}, starts with: {decrypted_key[:15]}")
```

### 2. RAG Engine Init (`backend/infrastructure/ai/rag_engine.py`)
```python
logger.info(f"[DEBUG] RAG Engine received key - length: {len(self.api_key)}, starts with: {self.api_key[:15]}")
logger.info(f"[DEBUG] Set OPENAI_API_KEY env var - length: {len(os.environ['OPENAI_API_KEY'])}, starts with: {os.environ['OPENAI_API_KEY'][:15]}")
```

### 3. Settings Reload (`backend/api/routes/settings.py`)
```python
logger.info(f"[DEBUG] Resolved key for reload - length: {len(resolved_key)}, starts with: {resolved_key[:15]}")
```

## Next Steps

### Step 1: Test with Current Logging

1. **Restart the application** (fresh process)
2. **Check the startup logs** for DEBUG messages showing:
   - What key is loaded
   - What key RAG engine receives
   - What key is set in environment
3. **Try a chat query**
4. **Share the relevant log lines** with DEBUG markers

### Step 2: Based on Log Results

#### Scenario A: Key is Correct Until RAG Engine
**If logs show**: Decrypted key is correct, but RAG engine receives wrong key
**Likely Cause**: Issue in api_key_resolver or RAG engine constructor
**Fix**: Trace the handoff between resolver and RAG engine

#### Scenario B: Key is Correct in RAG Engine, Wrong in API Call
**If logs show**: RAG engine has correct key, but OpenAI API receives wrong key
**Likely Cause**: LightRAG using `os.environ` instead of our client
**Fix**: Ensure LightRAG functions use our provided clients

#### Scenario C: Decryption Returns Corrupted Key
**If logs show**: Decrypted key already has extra 's'
**Likely Cause**: Encryption/decryption mismatch or storage corruption
**Fix**: Re-save key with proper encryption

#### Scenario D: Environment Variable from Startup Persists
**If logs show**: Correct key everywhere, but old env var still exists
**Likely Cause**: Multiple processes or env var not updating properly
**Fix**: Clear env var before setting new one

## Storage Architecture Recommendations

###Current Problems:
1. **Dual Storage**: Electron store + Backend store (not synced properly)
2. **Different Encryption Keys**: Electron uses machineId, Backend uses PBKDF2
3. **Complex Flow**: Settings pass through multiple layers with transformations

### Recommended Fix (After Diagnostics):

**Option 1: Backend as Single Source** (Simpler)
```
User → UI → Electron IPC → Backend API → Backend Storage (encrypted)
                                      ↓
                                   Services Reload
                                      ↓
                                   Success Response
```

**Benefits**:
- Single encryption point
- Clear data flow
- Backend controls service lifecycle
- No sync issues

**Changes**:
1. Remove API key storage from Electron
2. Electron forwards keys directly to backend
3. Backend validates, encrypts, stores, applies
4. UI gets confirmation

**Option 2: OS Keychain** (Industry Standard)
```
User → Keytar/Keyring → OS Credential Manager
                              ↓
                         Both Electron & Backend Read
```

**Benefits**:
- OS-level security
- No custom crypto
- Single source of truth
- Survives app reinstalls

**Libraries**:
- Node: `keytar` (Electron-native)
- Python: `keyring`

## Immediate Testing Instructions

Run these commands in order:

### 1. Clear Current Settings (Fresh Start)
```powershell
# Stop the app first!
Remove-Item "$env:USERPROFILE\.covenantrix\rag_storage\user_settings.json" -Force
Remove-Item "$env:APPDATA\covenantrix-desktop\covenantrix-settings.json" -Force
```

### 2. Start App with Logging
```powershell
# Start the app and watch the terminal for DEBUG logs
# Look for lines starting with [DEBUG]
```

### 3. Set Custom Key via UI
1. Open Settings
2. Switch to Custom mode
3. Enter your OpenAI key
4. Click Save
5. **Check terminal** for DEBUG messages showing key at each step

### 4. Apply Settings
1. After save succeeds, check if "Apply" was called
2. Look for "Reloading RAG engine" message
3. Check DEBUG logs showing reload flow

### 5. Test Chat
1. Send a test query
2. If it fails, capture the exact error with key prefix
3. Compare to DEBUG logs from startup

### 6. Restart App
1. Close app completely
2. Restart
3. **Immediately check startup logs** for DEBUG messages
4. Try chat query again
5. Compare error (if any) to startup logs

## What to Share

When sharing results, please include:

1. **Startup logs** with all `[DEBUG]` lines
2. **Save operation logs** when you click Save in settings
3. **Apply operation logs** (if apply is called)
4. **Error logs** when chat query fails
5. **Key prefix comparison**: What was decrypted vs what was used

Format:
```
=== STARTUP ===
[DEBUG] Decrypted key length: 164, starts with: sk-proj-MY7z3OP
[DEBUG] RAG Engine received key - length: 164, starts with: sk-proj-MY7z3OP
[DEBUG] Set OPENAI_API_KEY env var - length: 164, starts with: sk-proj-MY7z3OP

=== CHAT QUERY ===
ERROR: Incorrect API key provided: sks-proj-...
```

This will immediately show us where the corruption happens!

## Files Modified (For Reference)

1. `backend/core/api_key_resolver.py` - Added decryption output logging
2. `backend/infrastructure/ai/rag_engine.py` - Added RAG init logging
3. `backend/api/routes/settings.py` - Added reload operation logging

All logging uses `[DEBUG]` prefix for easy grepping.

## Expected Timeline

- **30 minutes**: Run diagnostics with new logging
- **1 hour**: Identify root cause based on logs
- **2-4 hours**: Implement proper fix
- **1 day**: Consider architecture simplification if needed

The diagnostic logs will immediately tell us where the key gets corrupted, then we can implement the targeted fix.

