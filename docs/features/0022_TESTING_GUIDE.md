# Feature 0022: Testing Guide

## Quick Testing Checklist

### Test 1: Fresh Install - Trial Initialization
**Goal:** Verify trial dates populate immediately on first launch

**Steps:**
1. Delete `~/.covenantrix/rag_storage/user_settings.json`
2. Start backend
3. Check `user_settings.json`

**Expected:**
- `subscription.trial_started_at` has ISO datetime (not null)
- `subscription.trial_expires_at` is 7 days later (not null)
- `subscription.features.use_default_keys` is `true`
- `ui.zoom_level` is `0.8`

---

### Test 2: Zoom Level Persistence
**Goal:** Verify zoom level survives app restart

**Steps:**
1. Open app → Settings → Appearance
2. Change zoom to 120%
3. Save settings
4. Restart app
5. Check Settings → Appearance

**Expected:**
- Zoom level still shows 120%
- App UI actually zoomed to 120%

---

### Test 3: Migration - Missing Trial Dates
**Goal:** Verify existing settings get trial dates added

**Steps:**
1. Manually edit `user_settings.json`:
   - Set `subscription.trial_started_at` to `null`
   - Set `subscription.trial_expires_at` to `null`
2. Start backend
3. Check `user_settings.json`

**Expected:**
- Trial dates now populated
- Backend logs show "Fixing existing trial subscription with missing dates"

---

### Test 4: Migration - Missing Zoom Level
**Goal:** Verify existing UI settings get zoom_level added

**Steps:**
1. Manually edit `user_settings.json`:
   - Remove `"zoom_level"` from `ui` section
2. Start backend
3. Check `user_settings.json`

**Expected:**
- `ui.zoom_level` now exists with value `0.8`
- Backend logs show "Adding zoom_level to existing UI settings"

---

### Test 5: Feature Flag Consistency
**Goal:** Verify feature flags sync with tier config

**Steps:**
1. Check `user_settings.json` on fresh install
2. Compare `subscription.features.use_default_keys` 

**Expected:**
- Trial tier: `use_default_keys` is `true`
- Backend logs show feature flags synced if needed

---

## Quick Validation Commands

**Check settings file:**
```bash
cat ~/.covenantrix/rag_storage/user_settings.json | jq '.subscription'
cat ~/.covenantrix/rag_storage/user_settings.json | jq '.ui.zoom_level'
cat ~/.covenantrix/rag_storage/user_settings.json | jq '.subscription.features.use_default_keys'
```

**Watch backend logs for migration messages:**
```bash
# Look for these log messages:
# "Trial period initialized during migration"
# "Adding zoom_level to existing UI settings"
# "Fixing existing trial subscription with missing dates"
```

---

## Pass Criteria

✅ **All 5 tests pass**  
✅ **No null values in trial dates**  
✅ **Zoom level persists across restarts**  
✅ **Migration logs appear when fixing existing settings**  
✅ **Feature flags match tier configuration**

