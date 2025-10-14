# Phase 1 Implementation Complete ✓

## Feature 0020: JWT-Based Subscription & Tier Management System
**Phase 1: Core Infrastructure & Data Layer**

### Implementation Date
October 14, 2025

### Status
✅ **COMPLETE** - All Phase 1 components implemented and ready for testing

---

## What Was Implemented

### 1. Backend Schema Extensions ✓
**File:** `backend/api/schemas/settings.py`

Added three new Pydantic models:
- `FeatureFlags` - Tier-based feature limits (documents, queries, file sizes, API key mode)
- `SubscriptionSettings` - Complete subscription state management
- Updated `UserSettings` to include subscription field

### 2. Tier Configuration ✓
**File:** `backend/domain/subscription/tier_config.py`

Created tier configuration system with 4 tiers:
- **TRIAL**: 7 days, 3 docs, 10MB/doc, unlimited queries, default keys
- **FREE**: Indefinite, 3 docs, 10MB/doc, 50 queries/month + 20/day, custom keys only
- **PAID**: Unlimited docs/queries, 100MB/doc, default keys available
- **PAID_LIMITED**: Grace period (7 days), first 3 docs only, FREE limits, custom keys only

### 3. Usage Tracking Storage ✓
**File:** `backend/infrastructure/storage/usage_tracker.py`

Implemented comprehensive usage tracking:
- Query counters (monthly/daily) with auto-reset
- Document upload tracking
- Limit enforcement checks
- Persistent storage in `~/.covenantrix/rag_storage/usage_tracking.json`

### 4. JWT License Validator ✓
**File:** `backend/domain/subscription/license_validator.py`

Created JWT validation system:
- RS256 signature verification (with dev fallback)
- Expiry checking
- Payload extraction to SubscriptionSettings
- Test token generation utility

### 5. Subscription Service ✓
**File:** `backend/domain/subscription/service.py`

Core business logic orchestrator:
- Trial initialization on first launch
- License activation (JWT validation + tier upgrade)
- Tier expiry checking (trial → free, paid_limited → free)
- Tier transitions with notifications
- Upload/query limit enforcement
- Document deletion on downgrade
- Usage statistics aggregation

### 6. Subscription API Routes ✓
**File:** `backend/api/routes/subscription.py`

RESTful API endpoints:
- `GET /api/subscription/status` - Current tier, features, usage stats
- `POST /api/subscription/activate` - Activate license key (JWT)
- `GET /api/subscription/usage` - Remaining quotas
- `POST /api/subscription/validate-license` - Validate JWT without activating

### 7. Dependency Injection Setup ✓
**File:** `backend/core/dependencies.py`

Added global subscription service management:
- `set_subscription_service()` - Register singleton
- `get_subscription_service()` - DI for route handlers

### 8. Settings Storage Migration ✓
**File:** `backend/infrastructure/storage/user_settings_storage.py`

Added automatic migration:
- Detects missing `subscription` field in user_settings.json
- Auto-adds trial tier defaults on first load
- Preserves existing settings

### 9. Backend Startup Integration ✓
**File:** `backend/main.py`

Integrated into application lifecycle:
- Initialize subscription service on startup
- Auto-check trial/grace period expiry
- Global singleton registration
- Error handling with graceful degradation
- Subscription router registration

### 10. Dependencies Updated ✓
**File:** `backend/requirements.txt`

Added required packages:
- `PyJWT>=2.8.0` - JWT token validation
- `cryptography>=41.0.0` - Already present (used by JWT)

---

## Files Created (11 new files)

```
backend/domain/subscription/
  ├── __init__.py
  ├── tier_config.py
  ├── license_validator.py
  └── service.py

backend/infrastructure/storage/
  └── usage_tracker.py

backend/api/routes/
  └── subscription.py

docs/features/
  └── 0020_PHASE1_COMPLETE.md (this file)
```

## Files Modified (5 files)

```
backend/api/schemas/settings.py
backend/core/dependencies.py
backend/infrastructure/storage/user_settings_storage.py
backend/main.py
backend/requirements.txt
```

---

## Testing Instructions

### Prerequisites
1. Install new dependencies:
   ```bash
   cd backend
   pip install PyJWT>=2.8.0
   ```

2. Start the backend:
   ```bash
   python main.py
   ```

### Test 1: Trial Auto-Activation
**Objective:** Verify trial tier initializes on first launch

1. Delete `~/.covenantrix/rag_storage/user_settings.json` (if exists)
2. Start backend
3. Check logs for: `[OK] Subscription service initialized`
4. Call API:
   ```bash
   curl http://localhost:8000/api/subscription/status
   ```
5. **Expected Result:**
   ```json
   {
     "tier": "trial",
     "features": {
       "max_documents": 3,
       "max_doc_size_mb": 10,
       "max_queries_monthly": -1,
       "max_queries_daily": -1,
       "use_default_keys": true
     },
     "trial_started_at": "2025-10-14T...",
     "trial_expires_at": "2025-10-21T...",
     "usage": {...}
   }
   ```

### Test 2: Usage Tracking File Creation
**Objective:** Verify usage_tracking.json is created

1. Check file exists: `~/.covenantrix/rag_storage/usage_tracking.json`
2. **Expected Content:**
   ```json
   {
     "version": "1.0",
     "usage": {
       "queries": {
         "monthly": {"count": 0, "reset_date": "...", "history": []},
         "daily": {"count": 0, "reset_date": "...", "history": []}
       },
       "documents": {
         "total_count": 0,
         "current_visible": 0,
         "upload_history": []
       }
     }
   }
   ```

### Test 3: JWT License Validation (Development Token)
**Objective:** Test JWT validation with test token

1. Generate test token (from backend directory):
   ```bash
   cd backend
   python -c "from domain.subscription.license_validator import LicenseValidator; v = LicenseValidator(); print(v.generate_test_token('paid', 365))"
   ```

2. Validate via API (use the generated token):
   ```bash
   curl -X POST http://localhost:8000/api/subscription/validate-license \
     -H "Content-Type: application/json" \
     -d '{"license_key": "YOUR_TOKEN_HERE"}'
   ```

3. **Expected Result:**
   ```json
   {
     "valid": true,
     "tier": "paid",
     "expiry": "2026-10-14T...",
     "features": {
       "max_documents": -1,
       "max_queries_monthly": -1,
       "use_default_keys": true
     }
   }
   ```

**Note:** Validator supports both HS256 (test tokens) and RS256 (production tokens) with **full signature verification enabled** for both. Test tokens are verified using the shared secret "test-secret", production tokens use the embedded public key.

### Test 4: License Activation
**Objective:** Upgrade from trial to paid

1. Use token from Test 3
2. Activate license:
   ```bash
   curl -X POST http://localhost:8000/api/subscription/activate \
     -H "Content-Type: application/json" \
     -d '{"license_key": "YOUR_TOKEN_HERE"}'
   ```

3. **Expected Result:**
   ```json
   {
     "success": true,
     "new_tier": "paid",
     "message": "License activated successfully. Welcome to paid tier!",
     "features": {...}
   }
   ```

4. Verify in user_settings.json - tier should be "paid"

### Test 5: Settings Migration
**Objective:** Verify existing settings get subscription field

1. Use existing user_settings.json (without subscription field)
2. Restart backend
3. Check user_settings.json - should have `subscription` section added
4. Check logs: `"Adding subscription section to settings"`

### Test 6: Trial Expiry (Manual Test)
**Objective:** Test automatic downgrade from trial to free

1. Edit user_settings.json:
   ```json
   "subscription": {
     "tier": "trial",
     "trial_expires_at": "2025-01-01T00:00:00"  // Past date
   }
   ```
2. Restart backend
3. Check logs: `"Trial period expired, transitioning to FREE tier"`
4. Verify notification created with title "Trial Ended"
5. Call `/api/subscription/status` - tier should be "free"

### Test 7: API Endpoints
**Objective:** Verify all endpoints work

1. **Status:** `GET /api/subscription/status`
2. **Usage:** `GET /api/subscription/usage`
3. **Activate:** `POST /api/subscription/activate`
4. **Validate:** `POST /api/subscription/validate-license`

All should return 200 OK with proper JSON responses.

---

## API Reference

### GET /api/subscription/status
Returns current subscription tier, features, and usage statistics.

**Response:**
```typescript
{
  tier: "trial" | "free" | "paid" | "paid_limited"
  features: FeatureFlags
  trial_started_at?: string
  trial_expires_at?: string
  grace_period_started_at?: string
  grace_period_expires_at?: string
  usage: UsageStats
  last_tier_change?: string
}
```

### POST /api/subscription/activate
Activates a JWT license key.

**Request:**
```json
{
  "license_key": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:**
```json
{
  "success": true,
  "new_tier": "paid",
  "message": "License activated successfully. Welcome to paid tier!",
  "features": {...}
}
```

**Error Codes:**
- `400` - Invalid license token
- `500` - Server error

### GET /api/subscription/usage
Returns usage statistics and remaining quotas.

**Response:**
```json
{
  "tier": "trial",
  "documents_uploaded": 2,
  "queries_this_month": 15,
  "queries_today": 5,
  "monthly_remaining": 35,
  "daily_remaining": 15,
  "monthly_reset_date": "2025-11-14T...",
  "daily_reset_date": "2025-10-15T..."
}
```

### POST /api/subscription/validate-license
Validates a license without activating it (for testing).

**Request:**
```json
{
  "license_key": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:**
```json
{
  "valid": true,
  "tier": "paid",
  "expiry": "2026-10-14T...",
  "features": {...}
}
```

---

## Storage Files Created

### 1. user_settings.json
Location: `~/.covenantrix/rag_storage/user_settings.json`

New section added:
```json
{
  "subscription": {
    "tier": "trial",
    "license_key": null,
    "trial_started_at": "2025-10-14T12:00:00",
    "trial_expires_at": "2025-10-21T12:00:00",
    "grace_period_started_at": null,
    "grace_period_expires_at": null,
    "features": {
      "max_documents": 3,
      "max_doc_size_mb": 10,
      "max_total_storage_mb": 30,
      "max_queries_monthly": -1,
      "max_queries_daily": -1,
      "use_default_keys": true
    },
    "last_tier_change": "2025-10-14T12:00:00"
  }
}
```

### 2. usage_tracking.json (NEW)
Location: `~/.covenantrix/rag_storage/usage_tracking.json`

Tracks usage for limit enforcement:
```json
{
  "version": "1.0",
  "usage": {
    "queries": {
      "monthly": {
        "count": 0,
        "reset_date": "2025-11-14T12:00:00",
        "history": []
      },
      "daily": {
        "count": 0,
        "reset_date": "2025-10-15T12:00:00",
        "history": []
      }
    },
    "documents": {
      "total_count": 0,
      "current_visible": 0,
      "upload_history": []
    }
  }
}
```

---

## Next Steps: Phase 2

Once Phase 1 testing is complete, proceed to **Phase 2: Enforcement & Usage Tracking**

Phase 2 will add:
1. Document upload limit enforcement in `/api/documents/upload`
2. File size validation against tier limits
3. Query limit enforcement in `/api/queries` and `/api/chat`
4. Document visibility filtering (paid_limited tier shows first 3 only)
5. API key mode validation (FREE/paid_limited require custom keys)
6. Tier transition handlers with document hiding/deletion
7. Grace period auto-downgrade on startup

---

## Notes

- **Backward Compatibility:** Existing user_settings.json files are automatically migrated
- **Trial Duration:** 7 days from first launch
- **Default State:** All new installs start in TRIAL tier
- **JWT Validation:** Uses RS256 with fallback to HS256 for development
- **Error Handling:** Graceful degradation if subscription service fails to initialize
- **Storage Location:** All data in `~/.covenantrix/rag_storage/`

---

## Troubleshooting

### Issue: "Subscription service not initialized"
**Solution:** Check backend logs for initialization errors. Subscription service initializes after notification service in `main.py`.

### Issue: Trial not starting automatically
**Solution:** Delete user_settings.json and restart backend. Check logs for "Trial period initialized".

### Issue: JWT validation fails with "alg value is not allowed"
**Solution:** Fixed - validator now supports both HS256 (test tokens) and RS256 (production tokens). Signature verification is **ALWAYS ENABLED** for security - test tokens are verified with shared secret, production tokens with public key.

### Issue: Settings migration not working
**Solution:** Check file permissions on `~/.covenantrix/rag_storage/`. Ensure write access.

---

**Phase 1 Complete ✅**

Ready for testing and Phase 2 implementation.

