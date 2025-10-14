# Phase 2 Hotfix: Event Loop Error

## Issue Identified

When testing Phase 2 via the UI, an event loop error was detected in the backend logs:

```
2025-10-14 21:36:30 - domain.subscription.service - ERROR - Failed to load subscription: This event loop is already running
RuntimeWarning: coroutine 'UserSettingsStorage.load_settings' was never awaited
```

**Root Cause:** The route handlers (which are async functions) were calling the **synchronous** `get_current_subscription()` method, which internally tries to use `loop.run_until_complete()`. This fails because the async route handler already has an event loop running.

---

## Fix Applied

Changed all calls from `get_current_subscription()` to `await get_current_subscription_async()` in async route handlers.

### Files Modified

**1. `backend/api/routes/documents.py` (4 occurrences):**

```python
# BEFORE (sync call in async context - WRONG)
current_subscription = subscription_service.get_current_subscription()

# AFTER (async call in async context - CORRECT)
current_subscription = await subscription_service.get_current_subscription_async()
```

**Changed locations:**
- Line 63: Upload limit error response
- Line 86: File size limit check
- Line 176: Stream upload initialization
- Line 429: List documents tier filtering

**2. `backend/api/routes/settings.py` (1 occurrence):**

```python
# Line 198: API key mode validation
current_subscription = await subscription_service.get_current_subscription_async()
```

---

## Why This Happened

The `SubscriptionService` has two methods:

1. **`get_current_subscription()`** - Synchronous version
   - Uses `loop.run_until_complete()` to run async code
   - **Can only be called from synchronous contexts**
   - Used for dependency injection in `get_current_limits()` and similar

2. **`get_current_subscription_async()`** - Async version
   - Proper async/await implementation
   - **Must be used in async route handlers**

We mistakenly used the sync version in async contexts.

---

## Testing

After this fix, the error should no longer appear when:
- Uploading documents
- Listing documents
- Sending chat queries
- Updating settings

### Verification

Restart the backend and check logs - you should **NOT** see:
```
ERROR - Failed to load subscription: This event loop is already running
RuntimeWarning: coroutine 'UserSettingsStorage.load_settings' was never awaited
```

---

## Note on OpenAI API Key Error

The logs also showed:
```
Error code: 401 - Incorrect API key provided
```

**This is unrelated to the subscription system.** This indicates the OpenAI API key in settings is invalid/encrypted incorrectly. This is a separate issue with the API key configuration.

---

## Status

✅ **Fixed** - All async route handlers now use `get_current_subscription_async()`
✅ **No linter errors**
✅ **Ready for re-testing**

The chat query should now work without the event loop error. If there are still issues, they would be related to API key configuration, not the subscription system.

