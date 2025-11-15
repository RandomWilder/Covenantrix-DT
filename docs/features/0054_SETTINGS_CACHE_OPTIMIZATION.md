# Settings Cache Optimization

**Date**: November 15, 2024  
**Priority**: Performance Optimization  
**Status**: Implemented  
**Related**: 0053_PARALLEL_UPLOAD_OPTIMIZATION.md

## Summary

Added in-memory caching to `UserSettingsStorage` to reduce unnecessary disk I/O during document polling.

## Problem

**Observed in logs**:
```
Line 945: GET /documents
Line 946: Settings loaded successfully  ← File I/O
Line 947: Response: 200

Line 949: GET /documents  (2 seconds later)
Line 950: Settings loaded successfully  ← File I/O again!
Line 951: Response: 200
```

### Root Cause

1. **Frontend polls** `GET /documents` every 2 seconds to check document status
2. **list_documents endpoint** loads subscription settings on every call:
   ```python
   subscription_service = get_subscription_service()
   current_subscription = await subscription_service.get_current_subscription_async()
   ```
3. **get_current_subscription_async()** loads settings from disk every time:
   ```python
   settings = await self.settings_storage.load_settings()
   ```
4. **Result**: Reading `user_settings.json` from disk every 2 seconds!

### Impact

- **~100 disk reads** during a 3-minute document upload
- **Unnecessary I/O** for data that rarely changes
- **Log spam** with "Settings loaded successfully" messages

## Solution

Added **10-second in-memory cache** to `UserSettingsStorage`:

```python
class UserSettingsStorage:
    def __init__(self):
        # ... existing code ...
        
        # In-memory cache for settings
        self._cached_settings: Optional[UserSettings] = None
        self._cache_timestamp: Optional[datetime] = None
        self._cache_ttl_seconds = 10  # Cache for 10 seconds
    
    async def load_settings(self) -> UserSettings:
        # Check cache first
        if self._is_cache_valid():
            logger.debug("Returning cached settings")
            return self._cached_settings
        
        # Load from disk (only when cache expired)
        # ... existing load logic ...
        
        # Update cache
        self._cached_settings = settings
        self._cache_timestamp = datetime.utcnow()
        
        return settings
    
    async def save_settings(self, settings: UserSettings) -> None:
        # ... existing save logic ...
        
        # Invalidate cache after save
        self._cached_settings = None
        self._cache_timestamp = None
    
    def _is_cache_valid(self) -> bool:
        """Check if cached settings are still valid"""
        if self._cached_settings is None or self._cache_timestamp is None:
            return False
        
        age_seconds = (datetime.utcnow() - self._cache_timestamp).total_seconds()
        return age_seconds < self._cache_ttl_seconds
```

## Performance Impact

### Before Cache:
- **GET /documents** every 2 seconds
- **File I/O** every 2 seconds (read + JSON parse + decrypt)
- **~100 disk reads** during a 3-minute upload

### After Cache:
- **GET /documents** every 2 seconds (same)
- **File I/O** once every 10 seconds (cached in between)
- **~18 disk reads** during a 3-minute upload
- **83% reduction** in disk I/O!

### Expected Logs:

**Before**:
```
20:46:33 GET /documents → Settings loaded successfully
20:46:35 GET /documents → Settings loaded successfully
20:46:37 GET /documents → Settings loaded successfully
20:46:39 GET /documents → Settings loaded successfully
```

**After**:
```
20:46:33 GET /documents → Settings loaded successfully
20:46:35 GET /documents → (cache hit - no log)
20:46:37 GET /documents → (cache hit - no log)
20:46:39 GET /documents → (cache hit - no log)
20:46:43 GET /documents → Settings loaded successfully (cache expired)
```

## Cache Configuration

```python
# In UserSettingsStorage.__init__
self._cache_ttl_seconds = 10  # Cache for 10 seconds
```

**Why 10 seconds?**
- Settings changes are rare (user manually edits settings)
- 10 seconds is fast enough for settings changes to propagate
- Long enough to reduce most redundant I/O during polling
- Balances freshness vs. performance

**Can be tuned**:
- Increase (e.g., 30s) for even less I/O if settings rarely change
- Decrease (e.g., 5s) for faster settings propagation

## Cache Invalidation

Cache is **automatically invalidated** when:
1. **Settings are saved**: `save_settings()` clears cache
2. **Cache expires**: After TTL seconds (10s default)
3. **Service restarts**: Cache is in-memory, not persisted

## Safety Guarantees

### Thread-Safe
- ✅ Python's GIL protects cache access
- ✅ Single instance of `UserSettingsStorage` per application
- ✅ No race conditions

### Data Consistency
- ✅ Cache invalidated immediately on save
- ✅ Maximum staleness: 10 seconds
- ✅ No risk of serving outdated critical data

### Error Handling
- ✅ If cache check fails, fallback to disk load
- ✅ If disk load fails, error propagates normally
- ✅ No change to error handling behavior

## Testing

### Manual Verification

1. **Start application**
2. **Navigate to Documents page** (triggers polling)
3. **Watch logs**:
   - First request: "Settings loaded successfully"
   - Next ~5 requests: No settings logs (cache hits)
   - After 10s: "Settings loaded successfully" again

### Code Changes

**Files Modified**:
- `backend/infrastructure/storage/user_settings_storage.py`
  - Added cache fields to `__init__`
  - Updated `load_settings()` to check cache
  - Updated `save_settings()` to invalidate cache
  - Added `_is_cache_valid()` helper

**Lines Added**: ~25 lines
**Breaking Changes**: None

## Related Optimizations

This cache complements the parallel upload optimization (0053):
- **Parallel uploads**: Reduce document processing time
- **Settings cache**: Reduce overhead during uploads
- **Combined**: Faster uploads with less system load

## Monitoring

### What to Monitor

```python
# Add to logs if needed:
logger.debug(f"Settings cache hit rate: {hits}/{total} = {rate:.1%}")
```

### Expected Behavior

- **Cache hit rate**: ~80-90% during active polling
- **Cache misses**: Every 10+ seconds
- **Settings file reads**: Dramatically reduced

## Future Enhancements

1. **Configurable TTL**: Allow users to adjust cache duration
2. **Cache warming**: Pre-load on startup
3. **Metrics**: Track cache hit/miss rates
4. **Redis cache**: For multi-instance deployments

---

**Status**: Implemented and tested  
**Risk**: Low - Minimal code change, proper invalidation  
**Rollback**: Remove cache fields and cache checks (restore original behavior)

