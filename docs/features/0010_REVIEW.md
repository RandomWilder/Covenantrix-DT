# Feature 0010: Real-Time Document Upload Progress - Code Review

## Review Date
October 11, 2025

## Overall Assessment
⚠️ **ISSUES FOUND** - The implementation has the right structure and follows the plan well, but contains several critical bugs that will prevent the feature from working as intended.

---

## Critical Issues

### 1. ❌ Missing Progress Callback Connection (CRITICAL BUG)
**File:** `backend/api/routes/documents.py` (lines 181-188)

**Issue:** The SSE streaming endpoint does NOT emit intermediate progress stages from `service.process_document()`. The service method has a `progress_callback` parameter but it's never passed when called from the streaming endpoint.

**Current Code:**
```python
# Process document (progress updates are handled internally)
# The service will emit its own progress updates to registry
await service.process_document(
    document_id=document.id,
    extracted_content=extracted_text,
    processing_time=time.time() - start_time,
    ocr_applied=False
)
```

**Impact:** Users will only see three stages:
1. Initializing (10%)
2. Reading (25%)
3. Completed (100%)

They will NOT see:
- Understanding (50%)
- Building connections (75%)
- Finalizing (90%)

**Fix Required:** Pass a progress callback that emits SSE events:
```python
async def progress_callback(stage: str, percent: int):
    event = DocumentProgressEvent(
        filename=filename,
        document_id=document.id,
        stage=DocumentProgressStage(stage),
        message=service.STAGE_MESSAGES[stage],
        progress_percent=percent,
        timestamp=datetime.utcnow().isoformat()
    )
    batch_event.file_progress = event
    yield f"data: {batch_event.model_dump_json()}\n\n"

await service.process_document(
    document_id=document.id,
    extracted_content=extracted_text,
    processing_time=time.time() - start_time,
    ocr_applied=False,
    progress_callback=progress_callback
)
```

**However**, there's a deeper issue: The callback needs to yield to the outer generator, which isn't straightforward in Python. The proper solution would be to use a queue or to refactor the service to be a generator itself.

---

### 2. ❌ Progress Count Duplication Bug (CRITICAL BUG)
**File:** `covenantrix-desktop/src/hooks/useUpload.ts` (lines 193-201)

**Issue:** The `completed++` and `failed++` counters are incremented on EVERY progress event, not just when the file completes. Since multiple progress events are emitted per file (initializing, reading, understanding, etc.), the counts will be grossly inflated.

**Current Code:**
```typescript
// Map status from stage
let status: FileItem['status'] = 'processing'
if (file_progress.stage === 'completed') {
  status = 'completed'
  progress.completed++  // ❌ INCREMENTS EVERY TIME!
} else if (file_progress.stage === 'failed') {
  status = 'failed'
  progress.failed++     // ❌ INCREMENTS EVERY TIME!
}
```

**Impact:** If a file emits 6 events before completion, the completed count will be incremented 6 times for a single file.

**Fix Required:** Track which files have been counted:
```typescript
const completedFiles = new Set<string>()
const failedFiles = new Set<string>()

// Inside the loop:
if (file_progress.stage === 'completed' && !completedFiles.has(fileItem.id)) {
  status = 'completed'
  progress.completed++
  completedFiles.add(fileItem.id)
} else if (file_progress.stage === 'failed' && !failedFiles.has(fileItem.id)) {
  status = 'failed'
  progress.failed++
  failedFiles.add(fileItem.id)
}
```

---

### 3. ❌ Outdated Function Signature (BUG)
**File:** `covenantrix-desktop/src/hooks/useUpload.ts` (line 243)

**Issue:** The `uploadGoogleDriveFiles` function signature doesn't match the new parameters that include stage information.

**Current Signature:**
```typescript
const uploadGoogleDriveFiles = async (
  files: FileItem[],
  progress: UploadProgress,
  updateFileStatus: (id: string, status: FileItem['status'], progress?: number, error?: string) => void,
  setUploadProgress: (progress: UploadProgress) => void
)
```

**Expected Signature:**
```typescript
const uploadGoogleDriveFiles = async (
  files: FileItem[],
  progress: UploadProgress,
  updateFileStatus: (
    id: string, 
    status: FileItem['status'], 
    progress?: number, 
    error?: string,
    stage?: DocumentProgressStage,
    stageMessage?: string
  ) => void,
  setUploadProgress: (progress: UploadProgress) => void
)
```

**Impact:** TypeScript compilation will fail or calls to `updateFileStatus` from this function will have incorrect parameters.

---

## Major Issues

### 4. ⚠️ Generator Yield Problem (ARCHITECTURAL ISSUE)
**File:** `backend/api/routes/documents.py`

**Issue:** The original plan specified using a progress callback, but Python async generators cannot yield from within a nested function. The callback pattern won't work as designed.

**Current Architecture:**
```python
async def generate_progress_stream():
    # ... 
    async def progress_callback(stage: str, percent: int):
        yield "data: ..."  # ❌ Cannot yield from nested function
    
    await service.process_document(progress_callback=progress_callback)
```

**Solutions:**
1. **Use an async queue**: Callback adds events to queue, outer generator reads from queue
2. **Refactor service**: Make `process_document` itself a generator
3. **Skip internal stages**: Only emit stages at the route level (current implementation)

The current implementation has chosen option 3 (skipping internal stages), which works but doesn't fulfill the plan's promise of showing all 7 stages.

---

## Minor Issues

### 5. ⚠️ Missing Router Assignment
**File:** `backend/api/routes/documents.py` (line 27)

**Issue:** The `router` variable is used throughout but isn't shown in the imports. Need to verify it's defined:

**Should have:**
```python
router = APIRouter(prefix="/documents", tags=["documents"])
```

(This is actually present in the full file - verified from earlier view)

---

### 6. ⚠️ Inconsistent Overall Progress Calculation
**File:** `backend/api/routes/documents.py` (lines 146, 200, 222)

**Issue:** Overall progress calculation is inconsistent:
- Line 146: `int((file_index / total_files) * 100)` - Progress at START of file
- Line 200: `int(((file_index + 1) / total_files) * 100)` - Progress at END of file
- Line 222: `int(((file_index + 1) / total_files) * 100)` - Progress on failure

This is actually logical (0% when starting first file, 33% when first file completes, etc.) but the initial event at index 0 shows 0% which seems odd. Consider showing overall progress including the current file's progress:

```python
overall_progress = int(((file_index + (file_progress.progress_percent / 100)) / total_files) * 100)
```

---

### 7. ⚠️ OCR Detection Missing
**File:** `backend/api/routes/documents.py` (line 187)

**Issue:** `ocr_applied` is hardcoded to `False`, but the DocumentProcessor may have actually used OCR.

**Fix:** Track if OCR was used:
```python
ocr_used = hasattr(processor, 'ocr_applied') and processor.ocr_applied
await service.process_document(
    document_id=document.id,
    extracted_content=extracted_text,
    processing_time=time.time() - start_time,
    ocr_applied=ocr_used
)
```

---

### 8. ⚠️ Progress State Mutation Issue
**File:** `covenantrix-desktop/src/hooks/useUpload.ts` (lines 195-200)

**Issue:** The progress counts are being mutated directly in the loop:
```typescript
progress.completed++
```

But the progress object is not being recreated, leading to potential stale state issues in React.

**Recommendation:** Track counts separately and update progress atomically:
```typescript
let completedCount = progress.completed
let failedCount = progress.failed

// In loop...
if (stage === 'completed') completedCount++
if (stage === 'failed') failedCount++

// After loop
setUploadProgress({ ...progress, completed: completedCount, failed: failedCount })
```

---

## Data Alignment Review ✅

### Backend to Frontend Data Flow
**Status:** ✅ CORRECT

The backend uses snake_case in Python but Pydantic's `model_dump_json()` automatically converts to camelCase:

**Backend (Python):**
```python
class BatchProgressEvent(BaseModel):
    total_files: int
    current_file_index: int
    file_progress: DocumentProgressEvent
    overall_progress_percent: int
```

**Frontend (TypeScript):**
```typescript
interface BatchProgressEvent {
  total_files: number
  current_file_index: number
  file_progress: DocumentProgressEvent
  overall_progress_percent: number
}
```

Actually, checking Pydantic default behavior - it uses snake_case by default! The TypeScript types should actually be camelCase:

```typescript
interface BatchProgressEvent {
  totalFiles: number        // ❌ Should match backend
  currentFileIndex: number  // ❌ Should match backend
  fileProgress: DocumentProgressEvent
  overallProgressPercent: number
}
```

**Wait** - Let me check if the code is using camelCase or snake_case in the frontend...

Looking at line 188 in useUpload.ts:
```typescript
const { file_progress, current_file_index } = event
```

So the frontend IS expecting snake_case! This is correct then. But it's inconsistent with typical TypeScript conventions.

**Recommendation:** Configure Pydantic to use camelCase for JSON serialization:
```python
class BatchProgressEvent(BaseModel):
    total_files: int
    current_file_index: int
    file_progress: DocumentProgressEvent
    overall_progress_percent: int
    
    class Config:
        alias_generator = lambda x: ''.join(word.capitalize() if i else word for i, word in enumerate(x.split('_')))
        populate_by_name = True
```

Or keep snake_case throughout (current approach) - just document this decision.

---

## Style and Consistency Review

### ✅ Follows Existing Patterns
- SSE implementation matches `chat.py` streaming pattern
- Error handling follows existing conventions
- Uses existing service layer properly

### ✅ No Over-Engineering
- Simple, focused implementation
- Reuses existing infrastructure
- No unnecessary abstractions

### ⚠️ File Size
- `documents.py` is now 607 lines - getting large but still manageable
- Consider splitting if more features are added
- Current size is acceptable

---

## Test Coverage Gaps

The plan mentions testing considerations but no tests were implemented:
1. Single file upload with progress
2. Batch upload with progress  
3. Network interruption during stream
4. Navigation away and back during upload
5. Stage progress for each phase
6. Hebrew/RTL text in messages

---

## Summary

| Category | Status | Count |
|----------|--------|-------|
| Critical Bugs | ❌ | 3 |
| Major Issues | ⚠️ | 1 |
| Minor Issues | ⚠️ | 5 |
| Passed Checks | ✅ | 3 |

## Recommendations Priority

**Must Fix Before Merge:**
1. Fix progress count duplication bug (#2)
2. Update `uploadGoogleDriveFiles` signature (#3)

**Should Fix:**
3. Implement proper progress callback or acknowledge limitation (#1, #4)
4. Fix progress state mutation (#8)

**Nice to Have:**
5. Improve overall progress calculation (#6)
6. Add OCR detection (#7)
7. Standardize camelCase vs snake_case
8. Add tests

## Conclusion

The implementation follows the architectural plan well and demonstrates good code organization. However, there are **3 critical bugs** that will prevent the feature from working correctly:

1. Progress callback not connected (stages won't stream)
2. Progress counts will be wrong (duplicated increments)
3. Type signature mismatch (Google Drive uploads will break)

These must be fixed before the feature can be considered functional. The architectural issue with yielding from callbacks also needs to be addressed or documented as a known limitation.

