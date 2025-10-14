# Feature 0020 Phase 2: Enforcement & Usage Tracking - COMPLETE

## Implementation Summary

Phase 2 focused on implementing limit enforcement, usage tracking, and tier-based feature restrictions throughout the application. All components have been successfully implemented and are ready for testing.

---

## What Was Implemented

### 2.1 Document Upload Limit Enforcement ✅

**Files Modified:**
- `backend/api/routes/documents.py`

**Changes:**
1. **Single Upload Endpoint (`/upload`):**
   - Added subscription service dependency
   - Check document count limit before upload
   - Check file size against tier limit (max_doc_size_mb)
   - Return HTTP 402 (Payment Required) if document limit reached
   - Return HTTP 413 (Payload Too Large) if file exceeds size limit
   - Record document upload after successful processing

2. **Stream Upload Endpoint (`/upload/stream`):**
   - Added file size validation for each file in batch
   - Check document count limit per file during streaming
   - Return limit errors in SSE format
   - Record each successful upload

**Error Responses:**
```json
// Document limit reached (HTTP 402)
{
  "error": "upload_limit_reached",
  "message": "Document limit of 3 reached for trial tier",
  "current_tier": "trial",
  "upgrade_required": true
}

// File too large (HTTP 413)
{
  "error": "file_too_large",
  "file_size_mb": 15.5,
  "max_size_mb": 10,
  "current_tier": "trial"
}
```

---

### 2.2 Query Limit Enforcement ✅

**Files Modified:**
- `backend/api/routes/queries.py`
- `backend/api/routes/chat.py`

**Changes:**
1. **Query Endpoint (`POST /queries`):**
   - Check query limits before processing
   - Return HTTP 429 (Too Many Requests) if limit exceeded
   - Record query after successful execution
   - Return remaining quotas in error response

2. **Chat Endpoints (`POST /chat/message` and `POST /chat/message/stream`):**
   - Added query limit checks before message processing
   - Record query usage after successful response
   - For streaming endpoint, record after stream completes

**Error Response:**
```json
// Query limit reached (HTTP 429)
{
  "error": "query_limit_reached",
  "message": "Daily query limit of 20 reached for free tier",
  "remaining_monthly": 15,
  "remaining_daily": 0,
  "reset_dates": {
    "daily": "2025-10-15T00:00:00",
    "monthly": "2025-11-01T00:00:00"
  }
}
```

---

### 2.3 Document Visibility Filtering ✅

**Files Modified:**
- `backend/domain/documents/service.py`
- `backend/api/routes/documents.py`

**Changes:**
1. **Document Service:**
   - Updated `list_documents()` to accept `subscription_tier` parameter
   - Apply tier-based filtering:
     - **paid_limited**: Show only first 3 documents by creation date
     - **trial/free**: Apply max_documents limit from tier config
     - **paid**: Show all documents (no limit)

2. **Documents API:**
   - Updated `GET /documents` endpoint to pass current tier to service
   - Filtering happens transparently on backend

**Filtering Logic:**
```python
if subscription_tier == "paid_limited":
    documents = sorted(documents, key=lambda d: d.created_at)[:3]
else:
    max_docs = tier_config["max_documents"]
    if max_docs != -1:
        documents = sorted(documents, key=lambda d: d.created_at)[:max_docs]
```

---

### 2.4 API Key Mode Validation ✅

**Files Modified:**
- `backend/api/routes/settings.py`

**Changes:**
- Added validation when user tries to set API key mode to "default"
- Check if current subscription tier allows default keys
- Return HTTP 403 (Forbidden) if tier doesn't support default keys
- Applies to FREE and PAID_LIMITED tiers (custom keys only)

**Error Response:**
```json
// Default keys not allowed (HTTP 403)
{
  "error": "default_keys_not_allowed",
  "message": "Your free tier requires custom API keys",
  "current_tier": "free",
  "allowed_mode": "custom"
}
```

---

### 2.5 Tier Transition Logic ✅

**Files Modified:**
- `backend/domain/subscription/service.py` (already implemented in Phase 1)

**Implementation:**
The `transition_tier()` method handles all tier transitions with proper cleanup:

**Transition Scenarios:**

1. **TRIAL → FREE:**
   - Force custom API key mode
   - Send warning notification
   - Keep existing documents

2. **PAID → PAID_LIMITED:**
   - Start 7-day grace period
   - Set grace period expiry timestamp
   - Force custom API key mode
   - Send error notification
   - Hide documents beyond first 3 (still in storage)

3. **PAID_LIMITED → FREE:**
   - End grace period
   - **Permanently delete** documents beyond first 3
   - Force custom API key mode
   - Send info notification

4. **PAID_LIMITED → PAID:**
   - Restore full access
   - Clear grace period timestamps
   - Send success notification
   - All documents become visible again

5. **FREE/TRIAL → FREE:**
   - Force custom mode
   - No document deletion

**Document Deletion:**
The `_delete_hidden_documents()` method:
- Sorts all documents by creation date
- Deletes documents at position 4+ (zero-indexed [3:])
- Uses hard delete (permanent removal)
- Updates usage tracker
- Logs each deletion

---

### 2.6 Grace Period Check on Startup ✅

**Files Modified:**
- `backend/main.py` (already implemented in Phase 1)
- `backend/domain/subscription/service.py` (already implemented in Phase 1)

**Implementation:**
The `check_tier_expiry()` method runs on backend startup:

```python
# In main.py lifespan()
await subscription_service.check_tier_expiry()
```

**Checks Performed:**
1. **Trial Initialization:** If trial never started, initialize with 7-day expiry
2. **Trial Expiry:** If trial expired, auto-downgrade to FREE
3. **Grace Period Expiry:** If grace period expired, auto-downgrade to FREE (triggers document deletion)

**Auto-Transitions:**
- TRIAL (expired) → FREE
- PAID_LIMITED (grace period expired) → FREE

---

## Integration Points

### Subscription Service Methods Used

```python
# Limit checking
can_upload, reason = await subscription_service.check_upload_allowed()
can_query, reason = await subscription_service.check_query_allowed()

# Usage recording
await subscription_service.record_document_upload(doc_id, size_mb)
await subscription_service.record_query()

# Get limits
tier_limits = subscription_service.get_current_limits()
remaining = await subscription_service.get_remaining_queries()

# Get current tier
current_subscription = subscription_service.get_current_subscription()
```

---

## Testing Guide

### 2.1 Test Document Upload Limits

```bash
# Upload documents until limit reached (3 for trial tier)
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@test.pdf"

# Expected: First 3 succeed, 4th returns 402
# Response:
# {
#   "error": "upload_limit_reached",
#   "message": "Document limit of 3 reached for trial tier",
#   "current_tier": "trial",
#   "upgrade_required": true
# }
```

### 2.2 Test File Size Limits

```bash
# Try uploading a 15MB file (trial limit is 10MB)
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@large_file.pdf"

# Expected: 413 error
# {
#   "error": "file_too_large",
#   "file_size_mb": 15.2,
#   "max_size_mb": 10,
#   "current_tier": "trial"
# }
```

### 2.3 Test Query Limits (FREE Tier)

```bash
# First, transition to FREE tier (50 queries/month, 20/day)
# Then make queries until limit reached

curl -X POST http://localhost:8000/api/queries \
  -H "Content-Type: application/json" \
  -d '{"query": "Test query", "mode": "hybrid"}'

# After 20 queries in a day:
# {
#   "error": "query_limit_reached",
#   "message": "Daily query limit of 20 reached for free tier",
#   "remaining_monthly": 30,
#   "remaining_daily": 0
# }
```

### 2.4 Test Document Visibility (PAID_LIMITED)

```bash
# 1. Upload 5 documents
# 2. Transition to PAID_LIMITED tier (manually in code or via license expiry)
# 3. List documents

curl -X GET http://localhost:8000/api/documents

# Expected: Only first 3 documents returned (by creation date)
```

### 2.5 Test API Key Mode Validation (FREE Tier)

```bash
# Try to set mode to "default" while in FREE tier
curl -X POST http://localhost:8000/api/settings \
  -H "Content-Type: application/json" \
  -d '{
    "settings": {
      "api_keys": {"mode": "default"}
    }
  }'

# Expected: 403 error
# {
#   "error": "default_keys_not_allowed",
#   "message": "Your free tier requires custom API keys",
#   "current_tier": "free"
# }
```

### 2.6 Test Tier Transitions

**Trial Expiry:**
```bash
# 1. Start backend with trial tier
# 2. Manually set trial_expires_at to past date in user_settings.json
# 3. Restart backend
# Expected: Auto-transition to FREE, notification created
```

**Grace Period Expiry:**
```bash
# 1. Transition to PAID_LIMITED (via subscription service)
# 2. Upload 5 documents
# 3. Set grace_period_expires_at to past date
# 4. Restart backend
# Expected: 
#   - Auto-transition to FREE
#   - Documents 4-5 permanently deleted
#   - Notification created
```

### 2.7 Test Document Deletion on Grace Period End

```bash
# 1. Start with PAID tier, upload 5 documents
# 2. Transition to PAID_LIMITED
curl -X POST http://localhost:8000/api/subscription/activate \
  -H "Content-Type: application/json" \
  -d '{"license_key": "<expired_paid_license>"}'

# 3. List documents - should show only 3
curl -X GET http://localhost:8000/api/documents

# 4. Wait or manually expire grace period
# 5. Restart backend
# 6. List documents again - should still show only 3 (others deleted)

# 7. Check logs for deletion messages:
# "Deleted hidden document: <doc_id> (<filename>)"
# "Deleted 2 hidden documents"
```

---

## Error Handling

### HTTP Status Codes Used

| Code | Meaning | When Used |
|------|---------|-----------|
| 402  | Payment Required | Document upload limit reached |
| 403  | Forbidden | API key mode not allowed for tier |
| 413  | Payload Too Large | File exceeds tier size limit |
| 429  | Too Many Requests | Query limit exceeded |

### Error Response Format

All limit-related errors follow consistent structure:
```json
{
  "error": "error_code",
  "message": "Human-readable message",
  "current_tier": "trial",
  // Additional context fields...
}
```

---

## Database Changes

### Usage Tracking File (`usage_tracking.json`)

**Document Records:**
```json
{
  "documents": {
    "total_count": 3,
    "current_visible": 3,
    "upload_history": [
      {
        "doc_id": "uuid",
        "filename": "contract.pdf",
        "size_mb": 2.5,
        "uploaded_at": "2025-10-14T12:00:00"
      }
    ]
  }
}
```

**Query Records:**
```json
{
  "queries": {
    "monthly": {
      "count": 25,
      "reset_date": "2025-11-01T00:00:00",
      "history": [...]
    },
    "daily": {
      "count": 8,
      "reset_date": "2025-10-15T00:00:00",
      "history": [...]
    }
  }
}
```

---

## Key Algorithms

### Document Count Check
```python
1. Get max_documents from tier config
2. If max_documents == -1: return allowed
3. Query usage_tracker.get_document_count()
4. Compare: count >= max ? reject : allow
5. After upload: record_document_upload()
```

### Query Limit Check
```python
1. Get max_queries_monthly and max_queries_daily from tier
2. If both == -1: return allowed
3. Query usage_tracker for current counts
4. Check monthly: remaining_monthly > 0?
5. Check daily: remaining_daily > 0?
6. If either exceeded: reject with 429
7. After query: record_query()
```

### Document Visibility Filter
```python
1. Get all documents from registry
2. If tier == "paid_limited":
   - Sort by created_at ascending
   - Return first 3 only
3. Else if max_documents != -1:
   - Sort by created_at ascending
   - Return first max_documents
4. Else: return all
```

---

## Files Modified Summary

| File | Changes | Lines Added |
|------|---------|-------------|
| `backend/api/routes/documents.py` | Upload limits, size checks | ~60 |
| `backend/api/routes/queries.py` | Query limit checks | ~20 |
| `backend/api/routes/chat.py` | Query limit checks (2 endpoints) | ~40 |
| `backend/api/routes/settings.py` | API key mode validation | ~15 |
| `backend/domain/documents/service.py` | Tier-based filtering | ~15 |

**Total:** 5 files modified, ~150 lines added

---

## Dependencies

Phase 2 relies on Phase 1 components:
- `SubscriptionService` (core orchestration)
- `UsageTracker` (storage layer)
- `LicenseValidator` (JWT validation)
- `TIER_LIMITS` configuration
- Subscription settings in `user_settings.json`

---

## Next Steps: Phase 3

Phase 2 is complete and ready for testing. After validation, proceed to Phase 3:
- Frontend integration (SubscriptionContext)
- UI components (trial banner, grace period warning)
- Feature gates in React components
- License activation UI
- Usage stats display

---

## Status: ✅ COMPLETE & READY FOR TESTING

All Phase 2 requirements have been implemented:
1. ✅ Document upload limit enforcement
2. ✅ Query limit enforcement
3. ✅ Document visibility filtering
4. ✅ API key mode validation
5. ✅ Tier transition with document deletion
6. ✅ Grace period check on startup

**No linter errors detected.**

Run the testing guide above to verify all functionality before proceeding to Phase 3.

