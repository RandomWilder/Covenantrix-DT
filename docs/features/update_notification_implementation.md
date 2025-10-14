# Version Update Notification - Implementation

## Overview
Transform the existing version update detection system from immediate dialogs to notification-based workflow, creating the first concrete notification type in the system.

---

## Current Behavior Analysis

**Existing Flow (updateManager.js):**
1. App checks for updates on startup
2. When update available → Shows dialog: "Download Now" / "Later"
3. User downloads → Shows dialog: "Restart Now" / "Later"
4. User forced to make decision immediately

**Current Implementation:**
- `electron/updateManager.js` - Handles auto-updater events
- Shows `dialog.showMessageBox()` popups
- Blocks user workflow until responded

---

## New Behavior Design

**Notification-Based Flow:**
1. App checks for updates on startup
2. When update available → Creates notification (silent)
3. Red dot appears on bell icon
4. User clicks bell when convenient
5. Expands notification → Sees full release notes + action buttons
6. User clicks "Update Now" → Downloads and installs
7. User clicks "Later" → Marks as read, keeps notification visible

**Key Improvements:**
- Non-blocking user workflow
- User controls timing
- Release notes always accessible
- No forced decisions

---

## Backend Implementation

### 1. Notification Creation in Update Manager

**Modify File:** `covenantrix-desktop/electron/updateManager.js`

**Current Code to Replace:**
```javascript
// OLD: Immediate dialog
autoUpdater.on('update-available', (info) => {
  this.promptUserToDownload(info);
});
```

**New Code:**
```javascript
// NEW: Create notification
autoUpdater.on('update-available', async (info) => {
  log.info('Update available:', info);
  updateCheckInProgress = false;
  this.updateInfo = info;
  
  // Create notification instead of dialog
  await this.createUpdateNotification(info);
  
  // Notify frontend to refresh notification list
  this.sendStatusToWindow('update-notification-created');
});
```

### 2. Notification Creation Method

**Add to updateManager.js:**
```javascript
async createUpdateNotification(info) {
  const notificationData = {
    type: 'version_update',
    source: 'local',
    title: `Version ${info.version} Available`,
    summary: `Update to Covenantrix ${info.version}`,
    content: this.formatReleaseNotes(info),
    actions: [
      { label: 'Update Now', action: 'install_update' },
      { label: 'Later', action: 'dismiss' }
    ],
    metadata: {
      version: info.version,
      current_version: app.getVersion(),
      release_date: info.releaseDate,
      download_size: info.files?.[0]?.size
    }
  };

  // Call backend API to create notification
  const response = await fetch('http://localhost:8080/api/notifications', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(notificationData)
  });

  return response.json();
}

formatReleaseNotes(info) {
  // Format release notes for display
  const notes = info.releaseNotes || 'No release notes available';
  
  return `
**Current Version:** ${app.getVersion()}
**New Version:** ${info.version}

**Release Notes:**
${notes}

**Download Size:** ${this.formatBytes(info.files?.[0]?.size)}
  `.trim();
}

formatBytes(bytes) {
  if (!bytes) return 'Unknown';
  const mb = (bytes / 1024 / 1024).toFixed(2);
  return `${mb} MB`;
}
```

### 3. Backend API Endpoint

**Modify File:** `backend/api/routes/notifications.py`

**Add Endpoint:**
```python
@router.post("", response_model=NotificationResponse)
async def create_notification(
    request: CreateNotificationRequest,
    service: NotificationService = Depends(get_notification_service)
) -> NotificationResponse:
    """
    Create a new notification.
    Used by update manager to create version update notifications.
    """
    notification = service.create_notification(
        notification_type=request.type,
        source=request.source,
        title=request.title,
        summary=request.summary,
        content=request.content,
        actions=request.actions,
        metadata=request.metadata
    )
    return NotificationResponse.from_domain(notification)
```

### 4. API Schema for Creation

**Modify File:** `backend/api/schemas/notifications.py`

**Add Schema:**
```python
class NotificationActionSchema(BaseModel):
    label: str
    action: str
    url: Optional[str] = None

class CreateNotificationRequest(BaseModel):
    type: str
    source: Literal['local', 'cloud']
    title: str
    summary: str
    content: Optional[str] = None
    actions: Optional[List[NotificationActionSchema]] = None
    metadata: Optional[Dict[str, Any]] = None
```

### 5. Notification Service Enhancement

**Modify File:** `backend/domain/notifications/service.py`

**Add Method:**
```python
def create_notification(
    self,
    notification_type: str,
    source: str,
    title: str,
    summary: str,
    content: Optional[str] = None,
    actions: Optional[List[Dict]] = None,
    metadata: Optional[Dict] = None
) -> Notification:
    """Create a new notification"""
    
    notification_id = f"notif_{uuid.uuid4().hex[:12]}"
    timestamp = datetime.now()
    
    # Convert action dicts to NotificationAction objects
    action_objects = []
    if actions:
        for action in actions:
            action_objects.append(NotificationAction(
                label=action['label'],
                action=action['action'],
                url=action.get('url')
            ))
    
    notification = Notification(
        id=notification_id,
        type=notification_type,
        source=source,
        title=title,
        summary=summary,
        content=content,
        actions=action_objects,
        timestamp=timestamp,
        read=False,
        dismissed=False,
        metadata=metadata or {}
    )
    
    self.storage.save_notification(notification)
    return notification
```

---

## Frontend Implementation

### 1. Action Handling in Notification Context

**Modify File:** `covenantrix-desktop/src/contexts/NotificationContext.tsx`

**Add Method:**
```typescript
const handleAction = async (notificationId: string, action: string) => {
  const notification = notifications.find(n => n.id === notificationId)
  if (!notification) return

  switch (action) {
    case 'install_update':
      // Trigger update installation
      await window.electronAPI.installUpdate()
      // Dismiss notification after action
      await dismissNotification(notificationId)
      break
      
    case 'dismiss':
      // Mark as read but keep notification
      await markAsRead(notificationId)
      // Collapse the notification
      setExpandedNotifications(prev => {
        const next = new Set(prev)
        next.delete(notificationId)
        return next
      })
      break
      
    default:
      console.warn(`Unknown action: ${action}`)
  }
}
```

### 2. Notification Card Action Rendering

**Modify File:** `covenantrix-desktop/src/features/notifications/NotificationCard.tsx`

**Add Action Buttons Section:**
```typescript
{isExpanded && notification.actions && (
  <div className="mt-4 flex items-center space-x-3">
    {notification.actions.map((action, index) => (
      <button
        key={index}
        onClick={() => handleAction(notification.id, action.action)}
        className={`px-4 py-2 rounded-lg font-medium transition-colors ${
          action.action === 'install_update'
            ? 'bg-blue-600 text-white hover:bg-blue-700'
            : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
        }`}
      >
        {action.label}
      </button>
    ))}
  </div>
)}
```

### 3. Update Installation IPC

**Modify File:** `covenantrix-desktop/electron/preload.js`

**Add Method:**
```javascript
update: {
  install: () => ipcRenderer.invoke('update:install')
}
```

**Modify File:** `covenantrix-desktop/electron/main.js`

**Add Handler:**
```javascript
ipcMain.handle('update:install', async () => {
  // Trigger the update installation
  autoUpdater.quitAndInstall(false, true)
})
```

### 4. Remove Old Dialog Prompts

**Modify File:** `covenantrix-desktop/electron/updateManager.js`

**Remove/Comment Out:**
```javascript
// REMOVE: These dialog-based prompts
// promptUserToDownload(info) { ... }
// promptUserToInstall(info) { ... }
```

**Keep Only:**
- Update checking logic
- Download progress tracking
- Error handling
- Logging

### 5. Notification Polling Trigger

**Modify File:** `covenantrix-desktop/src/contexts/NotificationContext.tsx`

**Add Event Listener:**
```typescript
useEffect(() => {
  // Listen for update notification creation
  const handleUpdateNotification = () => {
    fetchNotifications() // Refresh notification list
  }
  
  window.electronAPI.on('update-notification-created', handleUpdateNotification)
  
  return () => {
    window.electronAPI.off('update-notification-created', handleUpdateNotification)
  }
}, [fetchNotifications])
```

---

## Visual Design Specifications

### Collapsed State
```
🔔 Version 1.2.0 Available                           [2m ago]  [X]
   Update to Covenantrix 1.2.0
   ─────────────────────────────────────────────────────────────
```

### Expanded State
```
🔔 Version 1.2.0 Available                           [2m ago]  [X]
   ▼ Update to Covenantrix 1.2.0
   
   Current Version: 1.1.5
   New Version: 1.2.0
   
   Release Notes:
   • Enhanced OCR accuracy with Google Vision API
   • Fixed document processing memory leak  
   • Improved chat response streaming
   • Added support for Excel file upload
   • UI improvements for dark mode
   
   Download Size: 145.8 MB
   
   [Update Now]  [Later]
   ─────────────────────────────────────────────────────────────
```

### Badge Styling
```css
/* Red dot on bell icon */
.notification-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  width: 8px;
  height: 8px;
  background: #ef4444; /* red-500 */
  border-radius: 50%;
  border: 2px solid white;
}

/* Badge with count (if many notifications) */
.notification-count {
  position: absolute;
  top: -8px;
  right: -8px;
  min-width: 18px;
  height: 18px;
  padding: 0 4px;
  background: #ef4444;
  color: white;
  font-size: 11px;
  font-weight: 600;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
}
```

---

## Testing Scenarios

### Test 1: New Update Available
1. Start app with old version
2. Mock update available event
3. Verify notification created
4. Verify red dot appears on bell
5. Verify notification shows in list

### Test 2: Expand Notification
1. Click notification card
2. Verify full content displays
3. Verify action buttons appear
4. Verify marked as read
5. Verify red dot updates

### Test 3: Update Now Action
1. Expand update notification
2. Click "Update Now" button
3. Verify update installation begins
4. Verify notification dismissed
5. Verify app restarts (if successful)

### Test 4: Later Action
1. Expand update notification
2. Click "Later" button
3. Verify notification marked as read
4. Verify notification collapses
5. Verify notification remains in list
6. Verify buttons still available on re-expand

### Test 5: Dismiss Notification
1. Click X button on notification
2. Verify notification removed from list
3. Verify red dot updates
4. Verify notification not returned on refresh

### Test 6: Persistence
1. Create update notification
2. Mark as read (expand)
3. Restart app
4. Verify notification persists
5. Verify read state persists

### Test 7: Auto-Cleanup
1. Create update notification
2. Modify timestamp to 8 days ago (manual DB edit)
3. Trigger cleanup
4. Verify old notification removed

---

## Migration Notes

**Current System:**
- Users accustomed to immediate update dialogs
- May not notice notification system initially

**Transition Strategy:**
1. Keep current dialog for first-time notification
2. Show one-time tooltip: "Updates now appear in notifications"
3. After first notification interaction, disable tooltips

**Optional Enhancement:**
Add to initial dialog:
```
"Future updates will appear in your notification center 
instead of interrupting your workflow. Click the bell 
icon 🔔 in the header to review notifications."

[Got it, show me] [OK]
```

---

## Success Criteria

✅ Update detection creates notification (not dialog)  
✅ Notification appears in notification list  
✅ Red dot indicates unread update  
✅ Expandable pattern works correctly  
✅ Action buttons appear when expanded  
✅ "Update Now" triggers installation  
✅ "Later" marks as read, keeps notification  
✅ Dismiss removes notification  
✅ Persistence works across app restarts  
✅ No disruption to update installation flow  
✅ Release notes display correctly

---

## Rollback Plan

If issues arise:
1. Re-enable dialog prompts in `updateManager.js`
2. Comment out notification creation
3. System reverts to original behavior
4. Debug notification system separately

Keep both implementations for 1-2 releases before fully removing dialog code.
