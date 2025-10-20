# Feature 0042: Version Update Download Progress Bar Fix

## Overview
Fix the version update download progress bar to show real-time progress when the "Download Now" button is clicked. Currently, the progress bar only appears after download completion and shows 0% throughout. The system needs to properly connect the autoUpdater download-progress events to the notification system for real-time updates every 2 seconds.

---

## Current System Analysis

### Existing Infrastructure (Already Working)
- **Notification Type**: `downloadProgress` field exists in `Notification` interface with `percent`, `transferred`, `total`, `isDownloading` properties
- **Event Handler**: `updater.js` has `download-progress` event that captures progress data from autoUpdater
- **IPC Communication**: `onUpdateStatus` listener exists in preload.js for receiving progress updates
- **UI Component**: `NotificationCard.tsx` renders progress bar when `downloadProgress.isDownloading` is true
- **Progress Display**: Shows percentage, transferred/total bytes, and remaining bytes
- **Context Management**: `NotificationContext.tsx` already has progress tracking logic in lines 182-205

### Root Cause Analysis
**The system is actually already implemented correctly!** Looking at the existing code:

1. **Progress tracking exists**: Lines 182-205 in `NotificationContext.tsx` already listen for `onUpdateStatus` events
2. **Download start handling exists**: Lines 100-118 in `handleAction()` already set `downloadProgress.isDownloading = true`
3. **Progress updates exist**: Lines 187-203 already update notification progress from electron events
4. **UI rendering exists**: `NotificationCard.tsx` already renders progress bars

### Actual Issue
The problem is likely in the **event flow connection**. The existing code should work, but there might be:
1. **Event listener not properly connected** - The `onUpdateStatus` listener might not be receiving events
2. **Event data format mismatch** - The progress data format might not match what the context expects
3. **Timing issue** - The progress updates might be happening before the notification is properly initialized

---

## Implementation Plan (Minimal Changes)

### Phase 1: Debug and Fix Event Flow

#### 1.1 Add Debug Logging
**Modify File:** `covenantrix-desktop/src/contexts/NotificationContext.tsx`

**Add Debug Logging to Existing Code:**
- Add console.log in the `onUpdateStatus` listener (line 182) to verify events are received
- Add console.log in the progress update logic (lines 187-203) to verify data format
- Add console.log in `handleAction` download case (lines 100-118) to verify initialization

#### 1.2 Verify Event Data Format
**Check:** Ensure the progress data from `updater.js` matches what the context expects:
- `data.percent` should be a number 0-100
- `data.transferred` should be bytes transferred
- `data.total` should be total bytes

#### 1.3 Fix Event Connection (if needed)
**Modify File:** `covenantrix-desktop/src/contexts/NotificationContext.tsx`

**Potential Fixes:**
- Ensure the `onUpdateStatus` listener is properly registered
- Verify the event data structure matches expectations
- Add error handling for malformed progress data

### Phase 2: Enhance Progress Display (Optional)

#### 2.1 Improve Progress Bar Animation
**Modify File:** `covenantrix-desktop/src/features/notifications/NotificationCard.tsx`

**Enhance Existing Progress Bar:**
- Add smooth transition animations for progress updates
- Ensure progress bar is visible immediately when download starts
- Add loading indicator during progress updates

#### 2.2 Add Download Status Messages
**Modify File:** `covenantrix-desktop/src/features/notifications/NotificationCard.tsx`

**Status Messages:**
- "Starting download..." when `isDownloading = true` and `percent = 0`
- "Downloading update..." during progress
- "Download completed" when `percent = 100`
- Show speed information if available

### Phase 3: Handle Download Completion (Already Implemented)

#### 3.1 Verify Completion Handling
**Check:** The existing code should already handle:
- Progress updates during download (lines 187-203)
- Download completion via the existing notification system
- Transition to "Update Ready" notification

---

## Technical Details

### Existing Progress Update Flow (Should Already Work)
1. User clicks "Download Now" button
2. `handleAction()` sets `downloadProgress.isDownloading = true` (lines 100-118)
3. `window.electronAPI.update.download()` triggers download
4. `autoUpdater.on('download-progress')` fires every ~2 seconds
5. `sendStatusToWindow('downloading', progressData)` sends to renderer
6. `onUpdateStatus` listener receives progress data (line 182)
7. Progress update logic updates notification state (lines 187-203)
8. UI re-renders with new progress values

### Data Flow (Already Implemented)
```
autoUpdater.download-progress → updater.js → sendStatusToWindow → 
preload.js → NotificationContext.onUpdateStatus → 
setNotifications update → NotificationCard re-render
```

### Key Files to Check/Modify
- `covenantrix-desktop/src/contexts/NotificationContext.tsx` - Add debug logging to existing code
- `covenantrix-desktop/src/features/notifications/NotificationCard.tsx` - Enhance UI (optional)
- **No changes needed** to electron main process (updater.js) - already working
- **No changes needed** to preload.js - already has event listener

### Testing Requirements
- Verify progress bar appears immediately when download starts
- Confirm progress updates every 2 seconds during download
- Test progress bar reaches 100% when download completes
- Ensure "Download completed" message shows after 100%
- Verify no breaking changes to existing notification functionality

---

## Risk Assessment
- **Very Low Risk**: Minimal changes to existing working system
- **No Breaking Changes**: Existing notification functionality preserved
- **Leverages Existing Code**: Uses already implemented progress tracking
- **Backward Compatible**: Works with existing notification structure
