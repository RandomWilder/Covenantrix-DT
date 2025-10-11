# Upload Progress Persistence Fix

## Issue
When users navigate away from the upload tab and return, progress indicators disappear even though the backend is still processing documents.

## Solution

### 1. **Persistent State Storage** (localStorage)
- Upload state (files, progress, status) is automatically saved to localStorage
- State persists across page navigation and even browser refreshes
- Auto-expires after 24 hours to prevent stale data

### 2. **State Restoration on Mount**
- When returning to upload tab, checks localStorage for active uploads
- Restores file list, progress indicators, and processing status
- Only restores if there are active uploads (uploading/processing status)

### 3. **Backend Polling**
- Automatically polls backend every 2 seconds for document status updates
- Maps backend document status to UI progress indicators:
  - `processed` → completed (100%)
  - `processing` → processing with building connections message
  - `failed` → failed status
- Polling stops automatically when all documents complete
- Cleanup on component unmount

### 4. **Document ID Tracking**
- Each uploaded file now tracks its backend document ID
- Enables accurate status polling and updates
- Document IDs are included in progress events from backend

## Files Modified

### Backend
- `backend/api/routes/documents.py` (lines 118-143)
  - Fixed file reading to happen before StreamingResponse
  - Prevents "I/O operation on closed file" errors

### Frontend
- `covenantrix-desktop/src/hooks/useUpload.ts`
  - Added `filename` and `documentId` fields to FileItem interface
  - Implemented localStorage persistence (save/restore)
  - Added backend polling with `startPollingBackend()`
  - Updated `updateFileStatus` to track document IDs

- `covenantrix-desktop/src/features/upload/UploadScreen.tsx`
  - Shows progress UI when files are processing (not just when actively streaming)
  - Hides action buttons when files are being processed

## User Experience

### Before
1. Start upload
2. Navigate to Chat tab
3. Return to Upload tab
4. ❌ Progress lost, no indication of processing

### After
1. Start upload
2. Navigate to Chat tab
3. Return to Upload tab
4. ✅ Progress indicators restored
5. ✅ Backend status updates every 2 seconds
6. ✅ Clear indication when documents complete

## Technical Details

**State Persistence:**
```typescript
interface PersistedUploadState {
  files: Array<{
    id: string
    filename: string
    documentId?: string
    status?: FileItem['status']
    progress?: number
    error?: string
    stage?: DocumentProgressStage
    stageMessage?: string
  }>
  isUploading: boolean
  uploadProgress: UploadProgress
  timestamp: number
}
```

**Polling Mechanism:**
- Interval: 2000ms (2 seconds)
- Stops when: No processing files or component unmounts
- Updates: File status, progress, stage messages
- Error handling: Graceful logging, no user disruption

## Testing Recommendations

1. **Basic Flow:**
   - Upload a file
   - Navigate away immediately
   - Return to upload tab
   - Verify progress is showing

2. **Multiple Files:**
   - Upload 3-5 files
   - Navigate between tabs during processing
   - Verify all progress indicators work

3. **Edge Cases:**
   - Upload large file (takes longer)
   - Close browser tab during upload
   - Reopen and check state restoration
   - Wait 24+ hours and verify state expiry

4. **Error Handling:**
   - Upload invalid file
   - Disconnect network during upload
   - Verify error states persist and restore

## Benefits

- **Better UX:** Users can navigate freely without losing progress
- **Transparency:** Always know what's happening with uploads
- **Reliability:** State survives navigation and browser refreshes
- **Performance:** Efficient polling only when needed
- **Clean:** Auto-cleanup of completed/expired states

