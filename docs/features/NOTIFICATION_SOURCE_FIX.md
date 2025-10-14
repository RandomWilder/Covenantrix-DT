# Notification Source Alignment Fix

**Date:** October 15, 2025  
**Issue:** Update notifications not appearing in production v1.1.13  
**Root Cause:** Notification schema validation error blocking all notification retrieval

---

## Problem Summary

The subscription system (Feature 0020 Phase 3) created notifications with `source='subscription'`, but the notification schema only validated `Literal['local', 'cloud']`. This caused:

1. ✅ Notifications created successfully (POST /api/notifications returned 200)
2. ❌ Notification retrieval failed (GET /api/notifications returned 500)
3. ❌ Validation error: `Input should be 'local' or 'cloud' [input_value='subscription']`
4. ❌ Update notification system blocked (couldn't display any notifications)

---

## Evidence from Production Logs

```
[2025-10-15 00:03:03.954] Notification created successfully: update_available
[2025-10-15 00:03:04.686] Failed to get notifications: 1 validation error for NotificationResponse
source: Input should be 'local' or 'cloud' [input_value='subscription']
```

The update detection worked perfectly, but the frontend couldn't retrieve notifications due to schema mismatch.

---

## Files Modified

### Backend (Python)

1. **`backend/domain/notifications/models.py`** (Line 19)
   - **Before:** `source: Literal['local', 'cloud']`
   - **After:** `source: Literal['local', 'cloud', 'subscription']`

2. **`backend/api/schemas/notifications.py`** (Lines 20, 82)
   - **NotificationResponse.source** (Line 20)
     - **Before:** `source: Literal['local', 'cloud']`
     - **After:** `source: Literal['local', 'cloud', 'subscription']`
   
   - **CreateNotificationRequest.source** (Line 82)
     - **Before:** `source: Literal['local', 'cloud']`
     - **After:** `source: Literal['local', 'cloud', 'subscription']`

### Frontend (TypeScript)

3. **`covenantrix-desktop/src/types/notification.ts`** (Line 10)
   - **Before:** `source: 'local' | 'cloud';`
   - **After:** `source: 'local' | 'cloud' | 'subscription';`

---

## Validation Sources

### Backend Usage
- **'local'**: Update notifications, local system events
- **'cloud'**: Cloud-based notifications (future use)
- **'subscription'**: Subscription lifecycle notifications (trial ended, payment issues, etc.)

### Subscription Notifications Using 'subscription' Source
From `backend/domain/subscription/service.py`:
- Trial ended warning (line 199)
- Payment issue detected (line 215)
- Downgraded to free tier (line 229)
- Subscription restored (line 241)
- Welcome trial notification (line 355)

---

## Impact

### Before Fix
- ❌ ALL notifications fail to load (500 error)
- ❌ Update notifications never display
- ❌ Subscription notifications never display
- ❌ Bell icon doesn't show unread count
- ❌ Frontend continuously polls and fails

### After Fix
- ✅ All notifications load successfully
- ✅ Update notifications display correctly
- ✅ Subscription notifications display correctly
- ✅ Bell icon shows unread count
- ✅ No validation errors

---

## Testing Recommendations

### 1. Backend Validation
```bash
cd backend
python -c "
from api.schemas.notifications import NotificationResponse
from datetime import datetime

# Test subscription source validation
notification = NotificationResponse(
    id='test',
    type='info',
    source='subscription',  # Should now be valid
    title='Test',
    summary='Test',
    timestamp=datetime.now(),
    read=False,
    dismissed=False
)
print('✅ Subscription source validated successfully')
"
```

### 2. Integration Test
1. **Start the app** (development or production build)
2. **Check notification endpoint:**
   - Open DevTools → Network tab
   - Look for GET /api/notifications
   - Should return 200 (not 500)
3. **Verify notifications display:**
   - Click bell icon in header
   - Should see existing update notification for v1.1.15
   - No console errors

### 3. Update Notification Test
1. **Manual trigger:** Help → Check for Updates
2. **Verify logs:** Should see "Notification created successfully"
3. **Verify UI:** Update notification appears in notification modal
4. **Test action:** Click "Download Now" button
5. **Verify download:** Progress should show, then "Update Ready" notification

### 4. Subscription Notification Test
1. Create a subscription event (activate license, etc.)
2. Verify subscription notification appears
3. Should have `source='subscription'` in metadata

---

## Deployment Steps

### Development Testing
```bash
# Backend (terminal 1)
cd backend
python main.py

# Frontend (terminal 2)
cd covenantrix-desktop
npm run dev
```

### Production Build
```bash
# Update version
cd covenantrix-desktop
# Edit package.json: "version": "1.1.16"

# Commit and release
git add .
git commit -m "v1.1.16: fix notification source validation error"
git tag v1.1.16
git push
git push --tags
```

GitHub Actions will build and publish the update.

---

## Rollout Strategy

### Phase 1: Immediate Fix (v1.1.16)
- ✅ Schema changes applied
- ✅ All notification sources now supported
- ✅ No breaking changes to existing functionality
- ✅ Backward compatible (existing notifications still work)

### Phase 2: User Update
- Users on v1.1.13/v1.1.14/v1.1.15 will receive update notification
- Update to v1.1.16 fixes the notification system
- Existing subscription notifications in DB will now load correctly

### Phase 3: Verification
- Monitor error logs for any remaining validation errors
- Verify update notification flow works end-to-end
- Confirm subscription notifications display properly

---

## Why This Happened

1. **Feature 0020 Phase 3** (subscription system) was implemented on October 14, 2025
2. Subscription service created notifications with `source='subscription'`
3. Schema definitions weren't updated to include the new source type
4. System worked in isolation (POST succeeded) but failed on retrieval (GET failed)
5. This blocked the update notification system from working

---

## Prevention Strategy

### For Future Source Types
If adding new notification sources in the future:

1. **Update all Literal types simultaneously:**
   - `backend/domain/notifications/models.py`
   - `backend/api/schemas/notifications.py` (2 locations)
   - `covenantrix-desktop/src/types/notification.ts`

2. **Add integration test** that validates all source types

3. **Document source types** in notification schema docstrings

### Code Review Checklist
- [ ] If adding notification creation with new source value
- [ ] Update Literal type definitions in all 4 locations
- [ ] Add test case for new source type
- [ ] Verify GET /api/notifications doesn't throw validation error

---

## Success Criteria

- ✅ No validation errors in logs
- ✅ GET /api/notifications returns 200
- ✅ Update notifications display in UI
- ✅ Subscription notifications display in UI
- ✅ All three source types ('local', 'cloud', 'subscription') validate correctly
- ✅ No breaking changes to existing functionality
- ✅ TypeScript compilation successful
- ✅ Python linting passes

---

## Related Documentation

- **Update Notification System:** `docs/features/update_notification_implementation.md`
- **Feature 0018:** `docs/features/0018_IMPLEMENTATION_COMPLETE.md`
- **Feature 0020:** `docs/features/0020_PHASE3_COMPLETE.md`
- **Subscription Model:** `docs/features/subscription_model.md`

---

## Conclusion

The fix aligns the notification source validation across the entire stack (backend models, API schemas, and frontend types). This resolves the blocking issue preventing update notifications from displaying and enables the subscription notification system to function correctly.

**Status:** ✅ Complete and ready for testing

