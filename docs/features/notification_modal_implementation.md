# Notification Modal - Technical Implementation Brief

## Overview
Establish notification infrastructure foundation with empty state functionality. No notifications will be generated yet—this phase creates the system architecture, UI components, and data flow.

---

## Backend Implementation

### 1. Domain Layer - Notification Models
**New File:** `backend/domain/notifications/models.py`

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Literal

@dataclass
class NotificationAction:
    label: str
    action: str  # 'install', 'dismiss', 'open_url', etc.
    url: Optional[str] = None

@dataclass
class Notification:
    id: str
    type: str  # 'version_update', 'document_processed', 'error', etc.
    source: Literal['local', 'cloud']  # Future-ready
    title: str
    summary: str
    content: Optional[str] = None
    actions: List[NotificationAction] = None
    timestamp: datetime = None
    read: bool = False
    dismissed: bool = False
    metadata: Optional[dict] = None
    expires_at: Optional[datetime] = None  # Future: time-limited promos
```

### 2. Domain Layer - Notification Service
**New File:** `backend/domain/notifications/service.py`

**Key Methods:**
- `create_notification()` - Create new notification
- `get_all_notifications()` - Retrieve all notifications (sorted newest first)
- `get_unread_count()` - Count unread AND non-dismissed
- `mark_as_read(notification_id)` - Mark notification as read
- `dismiss_notification(notification_id)` - Dismiss notification
- `cleanup_expired()` - Auto-cleanup after 7 days

**Business Logic:**
- Unread count = notifications where `read=False AND dismissed=False`
- Cleanup: Delete notifications older than 7 days
- Sorting: Newest first by timestamp

### 3. Domain Layer - Notification Exceptions
**New File:** `backend/domain/notifications/exceptions.py`

```python
class NotificationError(Exception): pass
class NotificationNotFoundError(NotificationError): pass
class NotificationStorageError(NotificationError): pass
```

### 4. Infrastructure Layer - Notification Storage
**New File:** `backend/infrastructure/storage/notification_storage.py`

**Implementation:**
- JSON file storage: `~/.covenantrix/rag_storage/notifications.json`
- Follow existing storage patterns (see `chat_storage.py` reference)
- Thread-safe read/write operations
- Atomic file updates

**Storage Schema:**
```json
{
  "notifications": [
    {
      "id": "notif_abc123",
      "type": "version_update",
      "source": "local",
      "title": "...",
      "summary": "...",
      "content": "...",
      "actions": [...],
      "timestamp": "2025-10-14T10:30:00Z",
      "read": false,
      "dismissed": false,
      "metadata": {}
    }
  ]
}
```

### 5. API Layer - Notification Routes
**New File:** `backend/api/routes/notifications.py`

**Endpoints:**
```python
GET    /api/notifications              # List all notifications
GET    /api/notifications/unread-count # Get unread count
PUT    /api/notifications/{id}/read    # Mark as read
DELETE /api/notifications/{id}         # Dismiss notification
POST   /api/notifications/cleanup      # Manual cleanup trigger
```

### 6. API Layer - Notification Schemas
**New File:** `backend/api/schemas/notifications.py`

**Schemas:**
- `NotificationResponse` - API response model
- `NotificationListResponse` - List of notifications
- `UnreadCountResponse` - Unread count response
- `NotificationActionRequest` - Action request body

### 7. Dependency Injection
**Modify File:** `backend/core/dependencies.py`

Add notification service dependency:
```python
def get_notification_service() -> NotificationService:
    storage = NotificationStorage()
    return NotificationService(storage)
```

### 8. Router Registration
**Modify File:** `backend/main.py`

Register notification routes:
```python
from api.routes import notifications
app.include_router(notifications.router, prefix="/api/notifications", tags=["notifications"])
```

---

## Frontend Implementation

### 1. Type Definitions
**New File:** `covenantrix-desktop/src/types/notification.ts`

```typescript
export interface NotificationAction {
  label: string
  action: string
  url?: string
}

export interface Notification {
  id: string
  type: string
  source: 'local' | 'cloud'
  title: string
  summary: string
  content?: string
  actions?: NotificationAction[]
  timestamp: string
  read: boolean
  dismissed: boolean
  metadata?: Record<string, any>
}

export interface NotificationContextValue {
  notifications: Notification[]
  unreadCount: number
  isLoading: boolean
  expandedNotifications: Set<string>
  fetchNotifications: () => Promise<void>
  markAsRead: (id: string) => Promise<void>
  dismissNotification: (id: string) => Promise<void>
  toggleExpanded: (id: string) => void
  handleAction: (notificationId: string, action: string) => void
}
```

### 2. Notification Context
**New File:** `covenantrix-desktop/src/contexts/NotificationContext.tsx`

**Responsibilities:**
- Manage notification state
- Track expanded notifications
- Provide CRUD operations
- Maintain unread count
- Auto-refresh periodically (poll every 60 seconds)

**Key State:**
```typescript
const [notifications, setNotifications] = useState<Notification[]>([])
const [unreadCount, setUnreadCount] = useState<number>(0)
const [expandedNotifications, setExpandedNotifications] = useState<Set<string>>(new Set())
```

### 3. Notification Service (API Layer)
**New File:** `covenantrix-desktop/src/services/api/notificationService.ts`

**Methods:**
```typescript
export const notificationService = {
  getAll: () => Promise<Notification[]>
  getUnreadCount: () => Promise<number>
  markAsRead: (id: string) => Promise<void>
  dismiss: (id: string) => Promise<void>
  cleanup: () => Promise<void>
}
```

Uses `window.electronAPI` for IPC communication with backend.

### 4. Notification Modal Component
**New File:** `covenantrix-desktop/src/features/notifications/NotificationModal.tsx`

**Structure:**
- Modal overlay (similar to SettingsModal pattern)
- Header with title and close button
- Notification list (scrollable)
- Empty state component
- Individual notification cards

**Props:**
```typescript
interface NotificationModalProps {
  isOpen: boolean
  onClose: () => void
}
```

### 5. Notification Card Component
**New File:** `covenantrix-desktop/src/features/notifications/NotificationCard.tsx`

**Features:**
- Collapsed/expanded states
- Click to toggle expansion
- Mark as read when expanded
- Dismiss button (X)
- Action buttons (when expanded)
- Timestamp display (relative)

**Visual States:**
- Unread: Bold title, subtle background highlight
- Read: Normal weight, standard background
- Expanded: Full content + actions visible
- Collapsed: Title + summary only

### 6. Empty State Component
**New File:** `covenantrix-desktop/src/features/notifications/EmptyState.tsx`

Simple component showing:
- Bell icon (muted)
- "No notifications" message
- Friendly explanation text

### 7. Header Integration
**Modify File:** `covenantrix-desktop/src/components/layout/Header.tsx`

**Changes:**
- Add notification modal state
- Bell icon click handler
- Red dot badge conditional render
- Import NotificationContext for unreadCount

```typescript
const { unreadCount } = useNotifications()
const [isNotificationModalOpen, setIsNotificationModalOpen] = useState(false)

// Bell button with badge
<button onClick={() => setIsNotificationModalOpen(true)}>
  <Bell />
  {unreadCount > 0 && <span className="badge">{unreadCount}</span>}
</button>
```

### 8. App Layout Provider
**Modify File:** `covenantrix-desktop/src/App.tsx`

Wrap app with NotificationProvider:
```typescript
<NotificationProvider>
  <SettingsProvider>
    <AppLayout />
  </SettingsProvider>
</NotificationProvider>
```

### 9. IPC Bridge
**Modify File:** `covenantrix-desktop/electron/preload.js`

Add notification IPC methods:
```javascript
notifications: {
  getAll: () => ipcRenderer.invoke('notifications:getAll'),
  getUnreadCount: () => ipcRenderer.invoke('notifications:getUnreadCount'),
  markAsRead: (id) => ipcRenderer.invoke('notifications:markAsRead', id),
  dismiss: (id) => ipcRenderer.invoke('notifications:dismiss', id)
}
```

**Modify File:** `covenantrix-desktop/electron/main.js`

Register IPC handlers:
```javascript
ipcMain.handle('notifications:getAll', async () => {
  // Call backend API
})
// ... other handlers
```

---

## Styling

**New File:** `covenantrix-desktop/src/styles/notifications.css`

**Key Styles:**
- Modal overlay (reuse from SettingsModal pattern)
- Notification card (collapsed/expanded states)
- Unread indicator styling
- Red dot badge on bell icon
- Action button styling
- Smooth expand/collapse transitions

**Follow Existing Patterns:**
- Use Tailwind utility classes
- Match dark/light theme support
- Consistent spacing and typography
- Reuse existing color variables

---

## Dependencies

**No New External Dependencies Required**

All functionality uses existing:
- React (state, hooks, context)
- Tailwind CSS (styling)
- Lucide React (icons - Bell, X, ChevronDown)
- Existing IPC infrastructure
- Existing backend patterns

---

## File Structure Summary

```
backend/
├── domain/
│   └── notifications/
│       ├── __init__.py
│       ├── models.py          # NEW
│       ├── service.py         # NEW
│       └── exceptions.py      # NEW
├── infrastructure/
│   └── storage/
│       └── notification_storage.py  # NEW
├── api/
│   ├── routes/
│   │   └── notifications.py   # NEW
│   └── schemas/
│       └── notifications.py   # NEW
├── core/
│   └── dependencies.py        # MODIFY
└── main.py                    # MODIFY

covenantrix-desktop/
├── src/
│   ├── types/
│   │   └── notification.ts    # NEW
│   ├── contexts/
│   │   └── NotificationContext.tsx  # NEW
│   ├── services/
│   │   └── api/
│   │       └── notificationService.ts  # NEW
│   ├── features/
│   │   └── notifications/
│   │       ├── NotificationModal.tsx   # NEW
│   │       ├── NotificationCard.tsx    # NEW
│   │       └── EmptyState.tsx          # NEW
│   ├── components/
│   │   └── layout/
│   │       └── Header.tsx     # MODIFY
│   ├── styles/
│   │   └── notifications.css  # NEW
│   └── App.tsx                # MODIFY
└── electron/
    ├── preload.js             # MODIFY
    └── main.js                # MODIFY
```

---

## Testing Checklist

After implementation, verify:

- [ ] Bell icon visible in header
- [ ] Bell icon clickable
- [ ] Notification modal opens/closes
- [ ] Empty state displays correctly
- [ ] Modal styling matches app theme
- [ ] Dark/light theme support works
- [ ] No console errors
- [ ] Backend endpoints respond (empty arrays)
- [ ] IPC communication established
- [ ] Context provides default values

---

## Success Criteria

✅ Notification infrastructure fully established  
✅ Empty state functional and styled  
✅ No notifications shown (expected)  
✅ Foundation ready for notification types  
✅ Clean architecture maintained  
✅ Zero disruption to existing features
