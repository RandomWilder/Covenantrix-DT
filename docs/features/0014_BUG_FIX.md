# Feature 0014: Strict Mode Bug Fix

## Issue Found
**Date:** October 12, 2025  
**Severity:** 🔴 Critical  
**Reporter:** User testing

### Problem Description
When switching from **custom mode** → **default mode** in the Settings UI, the RAG engine continued using the custom API key instead of switching to the system key from `.env`.

**Root Cause:** The `apply_settings` endpoint only reloaded the RAG engine when mode was "custom". In default mode, it just applied settings to the existing engine without reloading with the correct key.

---

## Code Analysis

### Before Fix (Lines 400-427 in `settings.py`)

```python
# If in custom mode, reload RAG engine with fresh settings from storage
if mode == "custom":
    logger.info("Custom mode detected, attempting to reload RAG engine")
    reload_success = await reload_rag_with_settings()  # ✓ Reloads with user key
    # ...
else:
    # Apply settings to existing RAG engine
    rag_engine = get_rag_engine()  # ✗ Gets existing engine (with wrong key!)
    if isinstance(rag_engine, RAGEngine):
        rag_engine.apply_settings(settings_dict)  # ✗ Only applies settings, doesn't reload key
        applied_services.append("rag_engine")
```

**Problem:**
- Custom mode → Reloads engine with new key ✅
- Default mode → Keeps existing engine with old key ❌

### After Fix

```python
# Always reload RAG engine when applying settings
# This ensures strict mode is respected - custom mode uses user keys, default mode uses system keys
logger.info(f"Applying settings in {mode} mode, reloading RAG engine with strict key resolution")
reload_success = await reload_rag_with_settings()

if reload_success:
    applied_services.append("rag_engine_reloaded")
    logger.info(f"RAG engine successfully reloaded with {mode} mode key")
    restart_required = False
else:
    logger.warning("RAG engine reload failed, restart may be required")
    restart_required = True
```

**Solution:**
- **BOTH modes** now reload the engine
- `reload_rag_with_settings()` uses `api_key_resolver` which respects strict mode
- Engine always gets the correct key for the current mode

---

## Why This Fix Works

The `reload_rag_with_settings()` function (lines 330-374) already has the correct logic:

```python
async def reload_rag_with_settings():
    # Load fresh settings from storage
    user_settings = await settings_storage.load_settings()
    settings_dict = user_settings.model_dump()
    
    # Get system settings
    system_settings = get_settings()
    
    # Resolve OpenAI API key using strict mode
    api_key_resolver = get_api_key_resolver()
    resolved_key = api_key_resolver.resolve_openai_key(
        user_settings=settings_dict,
        fallback_key=system_settings.openai.api_key
    )
    
    # Create new RAG engine with resolved key
    rag_engine = RAGEngine(api_key=resolved_key, user_settings=settings_dict)
    await rag_engine.initialize()
    
    # Update global instance
    set_rag_engine(rag_engine)
```

The `api_key_resolver` enforces strict mode:
- **Custom mode** → Returns user key or `None` (never falls back to system)
- **Default mode** → Returns system key or `None` (never falls back to user)

By always calling this function, we ensure the engine uses the correct key.

---

## Testing Instructions

### Test Case 1: Custom → Default Mode Switch

1. **Start with custom mode + custom OpenAI key**
   ```bash
   cd backend
   python main.py
   # Watch logs: "Resolving openai key: mode=custom, source=user"
   ```

2. **Switch to default mode in Settings UI → Save**
   ```bash
   # Watch logs: "Applying settings in default mode, reloading RAG engine with strict key resolution"
   # Should see: "Resolving openai key: mode=default, source=system"
   ```

3. **Verify key changed**
   - If you have a system key in `.env` → Should use that
   - If no system key → RAG engine should be `None`, features disabled

### Test Case 2: Default → Custom Mode Switch

1. **Start with default mode (system key in .env)**
   ```bash
   cd backend
   python main.py
   # Watch logs: "Resolving openai key: mode=default, source=system"
   ```

2. **Switch to custom mode + enter custom key → Save**
   ```bash
   # Watch logs: "Applying settings in custom mode, reloading RAG engine with strict key resolution"
   # Should see: "Resolving openai key: mode=custom, source=user"
   ```

3. **Verify key changed to custom key**

### Expected Log Output

**Custom Mode:**
```
Applying settings in custom mode, reloading RAG engine with strict key resolution
Resolving openai key: mode=custom, source=user
[DEBUG] Resolved key for reload - length: 51, starts with: sk-proj-xxxxx
RAG engine successfully reloaded with custom mode key
```

**Default Mode:**
```
Applying settings in default mode, reloading RAG engine with strict key resolution
Resolving openai key: mode=default, source=system
[DEBUG] Resolved key for reload - length: 51, starts with: sk-xxxxx
RAG engine successfully reloaded with default mode key
```

---

## Impact Assessment

### Before Fix
- ❌ Mode switching didn't actually switch API keys
- ❌ Strict mode was not truly enforced at runtime
- ❌ Users couldn't reliably switch between system and custom keys

### After Fix
- ✅ Mode switching properly reloads engine with correct key
- ✅ Strict mode fully enforced (no fallback between modes)
- ✅ Users can reliably switch between system and custom keys
- ✅ Service status reflects actual key being used

---

## Files Modified

**1 file changed:**
- `backend/api/routes/settings.py` (Lines 393-411)

**Changes:**
- Removed conditional logic that only reloaded for custom mode
- Now always reloads RAG engine when applying settings
- Simplified code (removed unnecessary else block)
- Added clearer logging messages

---

## Verification Checklist

After applying this fix, verify:

- [ ] Switching from custom → default mode reloads engine with system key
- [ ] Switching from default → custom mode reloads engine with user key
- [ ] Logs show correct mode and source for each switch
- [ ] Service status endpoint reflects actual key being used
- [ ] Frontend feature guards respond to mode changes
- [ ] No fallback between modes occurs

---

## Related Files

These files already had correct implementation (no changes needed):
- ✅ `backend/core/api_key_resolver.py` - Strict mode logic was correct
- ✅ `backend/main.py` - Startup initialization correct
- ✅ `backend/core/dependencies.py` - Helper functions correct

---

**Status:** ✅ Fixed  
**Testing:** Ready for verification  
**Severity:** Critical (broke core strict mode functionality)  
**Priority:** High (immediate deployment recommended)

