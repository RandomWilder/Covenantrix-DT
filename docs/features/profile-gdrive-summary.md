# Profile & Google Drive Integration - Technical Summary

## Core Architecture Decision

**Storage Strategy:** JSON-based for desktop phase. No database/Firebase until SaaS migration needed.

**Storage Location:** `~/.covenantrix/rag_storage/` (existing)

**Integration Approach:** Extends existing `user_settings.json` structure with profile and google_accounts. Reuses encryption infrastructure. Completes placeholder OAuth implementations.

**Philosophy:** Device = user for desktop. No authentication layer. Profile is configuration hub, not auth gateway.

---

## System Components

### **1. Onboarding Flow Enhancement**

**Current:** Welcome → API Keys Setup

**New:** Welcome → **Profile Setup** → API Keys Setup

**Profile Setup Step:**
- Optional name/email entry
- Info message: "Connect Google Drive later from your Profile settings"
- Skip button (like other steps)
- No blockers - fully optional

**Reasoning:** Introduce identity layer early but don't force it. Plant seed for Google Drive without onboarding friction.

---

### **2. Profile System**

**Activation:** Profile icon → Profile modal/page

**Sections:**
1. **User Info** - first name, last name, email (local storage, no auth)
2. **Connected Accounts** - Google account list with add/remove
3. **API Keys** - existing OpenAI/Cohere management (unchanged)

**Storage (Integrates with Existing System):**
```
~/.covenantrix/rag_storage/
├── user_settings.json          # EXTEND existing - add profile + google_accounts
├── documents/                  # Existing RAG data
└── kv_store_*.json            # Existing LightRAG storage
```

**Extended user_settings.json Schema:**
```json
{
  "api_keys": {  /* existing */},
  "profile": {   /* NEW */
    "first_name": "Asaf",
    "last_name": "Cohen", 
    "email": "asaf@example.com"
  },
  "google_accounts": [  /* NEW */
    {
      "account_id": "uuid",
      "email": "work@company.com",
      "credentials": {
        "access_token": "encrypted...",
        "refresh_token": "encrypted...",
        "expiry": "2025-10-14T10:00:00Z"
      }
    }
  ]
}
```

**Reasoning:** Extends existing settings architecture. Single source of truth. Reuses encryption infrastructure. No new storage mechanisms needed.

---

### **3. OAuth Integration**

**Setup Requirements:**
- GCP project "Covenantrix"
- Enable Drive API
- OAuth Client ID (Desktop app type)
- Scope: `https://www.googleapis.com/auth/drive.readonly`

**Credential Management:**
```
Development:  backend/.env
Production:   GitHub Secrets → injected at build time
Runtime:      Loaded from config, never exposed to frontend
```

**Backend Architecture (Complete Existing Placeholders):**
```
backend/
├── domain/integrations/
│   ├── google_oauth.py         # EXISTS - complete TODO implementations
│   └── google_drive.py         # EXISTS - complete TODO implementations  
├── infrastructure/external/
│   └── google_api_client.py    # NEW - HTTP client for Google APIs
├── api/routes/
│   └── google.py               # NEW - REST endpoints
└── core/
    └── config.py               # EXTEND - add OAuth config
```

**Status:** GoogleOAuthService and GoogleDriveService exist with placeholder methods. This plan completes their implementations.

**OAuth Flow:**
1. Frontend requests OAuth URL → Backend generates with Client ID
2. Opens Electron BrowserWindow → Google consent screen
3. User authorizes → callback with auth code
4. Backend exchanges code for tokens (using Client Secret)
5. Tokens encrypted and added to `user_settings.json` google_accounts array
6. Backend manages token refresh automatically using refresh_token

**Token Storage (Within user_settings.json):**
```json
{
  "google_accounts": [
    {
      "account_id": "uuid-v4",
      "email": "user@gmail.com",
      "display_name": "Work Account",
      "credentials": {
        "access_token": "ya29... (encrypted)",
        "refresh_token": "1//... (encrypted)",
        "expiry": "2025-10-14T10:00:00Z",
        "scopes": ["https://www.googleapis.com/auth/drive.readonly"]
      },
      "connected_at": "2025-10-13T12:00:00Z",
      "last_used": "2025-10-13T15:30:00Z"
    }
  ]
}
```

**Best Practice OAuth Principles:**
- **Client Secret Never Exposed:** Backend only, never in frontend code or logs
- **Token Refresh:** Backend handles automatic refresh before expiry
- **Minimal Scope:** Request only `drive.readonly`, not full Drive access
- **Graceful Expiry:** UI prompts re-authorization if refresh fails
- **Revocation Support:** Users can disconnect → tokens deleted + revoked via Google API
- **Rate Limiting:** Respect Google API quotas with exponential backoff
- **Error States:** Handle network failures, expired tokens, quota exhaustion

**Reasoning:** Standard OAuth 2.0 desktop flow. One Client ID serves all users. Each user's tokens isolated. Backend owns secrets. Frontend just triggers flows.

---

### **4. Upload Page Enhancement**

**Current State:** Local files tab works. Google Drive tab is placeholder.

**Google Drive Tab UI (Modern Approach):**

**No Accounts Connected:**
```
┌─────────────────────────────────────────┐
│  No Google Drive Connected              │
│                                         │
│  📁 Connect your Google Drive to        │
│     upload documents directly           │
│                                         │
│  [Connect Google Drive]                 │
└─────────────────────────────────────────┘
```

**With Connected Accounts - Modern File Selector:**
```
┌─────────────────────────────────────────────────────────┐
│ Account: [work@company.com ▼] [+ Add Account] [Remove] │
├─────────────────────────────────────────────────────────┤
│ 🔍 Search in Drive...                    [📁 Grid] [☰]  │
├─────────────────────────────────────────────────────────┤
│ 📂 My Drive > 📁 Documents > 📁 Work                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ [✓] 📄 Contract_2024.pdf         2.3 MB   Oct 10      │
│ [ ] 📄 Report_Q3.docx           1.1 MB   Oct 12      │
│ [✓] 📊 Data_Analysis.xlsx       856 KB   Oct 13      │
│ [ ] 📁 Archive/                   -       Sep 20      │
│ [✓] 🖼️  Diagram.png              234 KB   Oct 11      │
│                                                         │
├─────────────────────────────────────────────────────────┤
│ 3 files selected (3.4 MB)        [Select All] [Clear]  │
│                                   [Upload Selected]     │
└─────────────────────────────────────────────────────────┘
```

**Modern UI Features:**
- **Clean Account Switcher:** Dropdown with email + avatar
- **Breadcrumb Navigation:** Click any folder in path to jump back
- **Smart Search:** Real-time filter as you type
- **Grid/List Toggle:** Thumbnail view for images, compact for files
- **Batch Selection:** Checkboxes with "Select All" / "Clear"
- **Visual File Types:** Icons differentiate PDFs, docs, images
- **Size/Date Context:** Quick metadata at a glance
- **Drag-to-folder:** Future enhancement - drag files into folders
- **Loading Skeleton:** Shimmer effect while fetching from Drive API

**Backend API Endpoints:**
```
GET  /api/google/accounts              # List user's connected accounts
POST /api/google/accounts/connect      # Initiate OAuth flow
DELETE /api/google/accounts/{id}       # Remove account + revoke

GET  /api/google/drive/files           # List files (query: account_id, folder_id, search)
POST /api/google/drive/download        # Download files → upload pipeline
```

**Integration with Upload Pipeline:**
```
Drive API → Download selected files
    ↓
Convert to UploadFile objects
    ↓
Pass to existing DocumentService.upload_document()
    ↓
Same RAG processing as local files
```

**Best Practices Included:**
- **Multi-Account:** Support personal + work Drives
- **Account Removal:** Confirmation dialog + token revocation
- **Token Refresh:** Automatic, transparent to user
- **Folder Navigation:** Breadcrumbs + back button
- **Multi-Select:** Checkbox + "Select All" / "Clear"
- **File Filtering:** Show only supported formats (PDF, DOCX, etc.)
- **Error Handling:** Expired tokens, network failures, quota limits
- **Loading States:** Skeletons during API calls
- **Empty States:** Helpful messages when no files found
- **Quota Warnings:** Notify if approaching Drive API limits

**Reasoning:** OAuth management in Profile (setup). Usage in Upload (consumption). Clean separation. Downloaded Drive files treated identically to local uploads. No pipeline changes needed.

---

## Key Technical Decisions

**Why JSON not Database:** Single-user desktop. Avoid cloud overhead pre-SaaS. Migrate when multi-device/web needed.

**Why You Provide OAuth Client:** Standard practice. Users just click "Allow". No technical setup burden.

**Why Separate Account Storage:** Multiple Drives common (work/personal). Independent tokens. Add/remove without side effects.

**Why Profile Owns Connections:** OAuth is identity layer. Profile is identity hub. Upload is consumption point.

**Why Onboarding Mentions Drive:** Plant seed early. Show value. Don't force setup. Reduce friction.

---

# Detailed High-Level Breakdown

## Part 1: Onboarding Modifications

### **Current Onboarding Flow**
```
Step 1: Welcome Screen
Step 2: API Keys Setup (OpenAI/Cohere)
Step 3: Complete → Main App
```

### **New Onboarding Flow**
```
Step 1: Welcome Screen (unchanged)
Step 2: Profile Setup (NEW)
Step 3: API Keys Setup (unchanged)
Step 4: Complete → Main App
```

---

### **Step 2: Profile Setup - Design**

**Layout:**
```
┌─────────────────────────────────────────┐
│            Set Up Your Profile           │
│     (Optional - can be skipped)          │
├─────────────────────────────────────────┤
│                                          │
│  First Name (optional)                   │
│  [                            ]          │
│                                          │
│  Last Name (optional)                    │
│  [                            ]          │
│                                          │
│  Email (optional)                        │
│  [                            ]          │
│                                          │
├─────────────────────────────────────────┤
│  💡 Connect your Google Drive later      │
│     from Profile settings to upload      │
│     documents directly                   │
├─────────────────────────────────────────┤
│  [Skip]              [Save & Continue]   │
└─────────────────────────────────────────┘
```

**Behavior:**
- All fields optional
- No validation on skip
- "Save & Continue" saves to `user_profile.json` (even if empty)
- Info box hints at Google Drive without requiring action
- Step counter: "Step 2 of 3"
- Can revisit from Profile icon later

**Frontend Files:**
```
covenantrix-desktop/src/
└── features/onboarding/
    ├── steps/
    │   ├── WelcomeStep.tsx         # Existing
    │   ├── ProfileSetupStep.tsx    # NEW
    │   ├── ApiKeysStep.tsx         # Existing
    │   └── CompleteStep.tsx        # Existing
    └── OnboardingScreen.tsx        # Modify step order
```

**Implementation Notes:**
- Add ProfileSetupStep between Welcome and ApiKeys
- Store profile data in existing `user_settings.json` under new `profile` key
- Skip creates empty profile object: `{first_name: null, last_name: null, email: null}`
- Reuses existing settings encryption infrastructure
- No new storage mechanisms or API calls needed

---

## Part 2: Profile Screen

### **Profile Modal/Page Structure**

**Layout Sections:**
```
┌────────────────────────────────────────────────────┐
│  Profile Settings                          [✕]     │
├────────────────────────────────────────────────────┤
│  [User Info] [Connected Accounts] [API Keys]       │
├────────────────────────────────────────────────────┤
│                                                     │
│  USER INFO TAB:                                     │
│  ┌──────────────────────────────────────┐          │
│  │ First Name: [Asaf              ]     │          │
│  │ Last Name:  [Cohen             ]     │          │
│  │ Email:      [asaf@example.com  ]     │          │
│  │                                       │          │
│  │ [Save Changes]                        │          │
│  └──────────────────────────────────────┘          │
│                                                     │
│  CONNECTED ACCOUNTS TAB:                            │
│  ┌──────────────────────────────────────┐          │
│  │ Google Accounts                       │          │
│  │                                       │          │
│  │ 📧 work@company.com                   │          │
│  │    Connected: Oct 13, 2025            │          │
│  │    Last used: 2 hours ago             │          │
│  │    [Remove Account]                   │          │
│  │                                       │          │
│  │ 📧 personal@gmail.com                 │          │
│  │    Connected: Oct 10, 2025            │          │
│  │    Last used: Yesterday               │          │
│  │    [Remove Account]                   │          │
│  │                                       │          │
│  │ [+ Connect Another Google Account]    │          │
│  └──────────────────────────────────────┘          │
│                                                     │
│  API KEYS TAB:                                      │
│  (Existing implementation - unchanged)              │
│                                                     │
└────────────────────────────────────────────────────┘
```

### **Connected Accounts Tab - Detailed Behavior**

**Add Account Flow:**
1. Click "+ Connect Another Google Account"
2. Frontend triggers IPC: `google-oauth-start`
3. Electron calls backend: `GET /api/google/oauth/url` → gets auth URL
4. Electron opens BrowserWindow with auth URL
5. User logs in → Google consent screen → clicks "Allow"
6. Callback intercepted: `http://localhost:8080/oauth/callback?code=xyz`
7. Electron sends IPC: `oauth-callback` with code to frontend
8. Frontend calls backend: `POST /api/google/oauth/callback` with code
9. Backend exchanges code for tokens, saves to `user_settings.json`
10. Close OAuth window, backend returns account data
11. Frontend updates account list

**Remove Account Flow:**
1. Click "Remove Account"
2. Confirmation dialog: "Remove work@company.com? You'll need to reconnect to upload from this Drive."
3. If confirmed: `DELETE /api/google/accounts/{account_id}`
4. Backend revokes token via Google API
5. Backend removes account from `user_settings.json` google_accounts array
6. Frontend updates UI list

**Account Card Details:**
- Email address (primary identifier)
- Connection date
- Last used timestamp (updated on Drive uploads)
- Status indicator (green = active, yellow = token expiring, red = needs re-auth)

### **Frontend Files:**
```
covenantrix-desktop/src/
└── features/profile/
    ├── ProfileScreen.tsx              # Main modal/page
    ├── tabs/
    │   ├── UserInfoTab.tsx           # First/last name, email editing
    │   ├── ConnectedAccountsTab.tsx  # NEW - Google accounts
    │   └── ApiKeysTab.tsx            # Existing
    ├── components/
    │   ├── GoogleAccountCard.tsx     # NEW - Individual account display
    │   └── AddAccountButton.tsx      # NEW - Connect flow trigger
    └── hooks/
        └── useGoogleAccounts.ts      # NEW - Account management logic

electron/
├── oauth-handler.js                  # NEW - OAuth window management
└── ipc-handlers.js                   # Add OAuth IPC handlers
```

### **Backend Files:**
```
backend/
├── api/routes/
│   └── google.py                              # NEW - OAuth & Drive endpoints
├── domain/integrations/
│   ├── google_oauth.py                        # COMPLETE - finish TODOs
│   └── google_drive.py                        # COMPLETE - finish TODOs
├── infrastructure/
│   ├── external/
│   │   └── google_api_client.py              # NEW - HTTP client
│   └── storage/
│       └── user_settings_storage.py          # EXTEND - add profile/google_accounts schema
└── core/
    └── config.py                              # EXTEND - add OAuth config
```

---

## Part 3: OAuth & Google Drive File Selector

### **OAuth Implementation Architecture**

**Backend Layers (Separation of Concerns):**

**1. Infrastructure Layer (`infrastructure/external/google_api_client.py`)**
- Low-level HTTP client
- Handles requests to Google APIs
- Token attachment to headers
- Retry logic with exponential backoff
- Error parsing

```python
class GoogleAPIClient:
    async def request(self, method: str, url: str, token: str, **kwargs):
        headers = {"Authorization": f"Bearer {token}"}
        # HTTP request with retry logic
```

**2. Domain Layer (`domain/integrations/google_oauth.py`)**
- OAuth flow orchestration
- Generate authorization URL
- Exchange code for tokens
- Token refresh logic
- Token storage/retrieval

```python
class GoogleOAuthService:
    def get_authorization_url(self) -> str:
        # Build OAuth URL with client_id, scopes, redirect_uri
    
    async def exchange_code_for_tokens(self, code: str) -> dict:
        # Exchange auth code for access + refresh tokens
    
    async def refresh_access_token(self, refresh_token: str) -> dict:
        # Get new access token using refresh token
```

**Electron OAuth Window Implementation:**

Electron provides `BrowserWindow` for OAuth flows, keeping everything contained within the app:

```javascript
// electron/oauth-handler.js (NEW)
const { BrowserWindow } = require('electron');

function openOAuthWindow(authUrl) {
  const authWindow = new BrowserWindow({
    width: 500,
    height: 600,
    show: false,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true
    }
  });

  authWindow.loadURL(authUrl);
  authWindow.show();

  // Listen for callback redirect
  authWindow.webContents.on('will-redirect', (event, url) => {
    if (url.startsWith('http://localhost:8080/oauth/callback')) {
      const code = new URL(url).searchParams.get('code');
      
      // Send code to main window renderer
      mainWindow.webContents.send('oauth-callback', { code });
      
      // Close OAuth window
      authWindow.close();
    }
  });

  authWindow.on('closed', () => {
    authWindow = null;
  });
}

module.exports = { openOAuthWindow };
```

**IPC Communication Flow:**
```
Frontend                 Electron Main              Backend
   │                          │                        │
   │──google-oauth-start──────>│                        │
   │                          │──GET /oauth/url────────>│
   │                          │<──returns auth_url─────│
   │                          │                        │
   │                      [Opens BrowserWindow]        │
   │                      [User authorizes on Google]  │
   │                          │                        │
   │                      [Callback intercepted]       │
   │<──oauth-callback(code)───│                        │
   │                          │                        │
   │──────POST /oauth/callback(code)───────────────────>│
   │<──────returns account──────────────────────────────│
```

**IPC Handlers (electron/ipc-handlers.js - EXTEND):**
```javascript
ipcMain.handle('google-oauth-start', async () => {
  // Call backend to get OAuth URL
  const response = await fetch('http://localhost:8000/api/google/oauth/url');
  const { url } = await response.json();
  
  // Open OAuth window
  openOAuthWindow(url);
  
  return { success: true };
});
```

**Benefits:**
- ✅ Contained within app (no external browser)
- ✅ Clean UX (modal-like experience)
- ✅ Auto-closes after authorization
- ✅ Standard Electron pattern
- ✅ Direct callback communication via IPC

**3. Domain Layer (`domain/integrations/google_drive.py`)**
- Drive-specific business logic
- List files/folders
- Download files
- Search functionality
- Folder navigation

```python
class GoogleDriveService:
    async def list_files(self, account_id: str, folder_id: str = None, search: str = None):
        # List Drive files with optional filtering
    
    async def download_file(self, account_id: str, file_id: str) -> bytes:
        # Download file content
    
    async def get_file_metadata(self, account_id: str, file_id: str) -> dict:
        # Get file details
```

**4. API Layer (`api/routes/google.py`)**
- REST endpoints
- Request/response schemas
- Dependency injection
- Error handling

```python
@router.post("/accounts/connect")
async def connect_google_account():
    # Return OAuth URL for frontend to open

@router.get("/accounts/callback")
async def oauth_callback(code: str):
    # Exchange code, save tokens, return success

@router.get("/accounts")
async def list_accounts():
    # Return user's connected accounts

@router.delete("/accounts/{account_id}")
async def remove_account(account_id: str):
    # Revoke token, delete storage

@router.get("/drive/files")
async def list_drive_files(account_id: str, folder_id: str = None):
    # Browse Drive files
```

---

### **Google Drive File Selector - Modern UI**

**Component Structure:**
```
covenantrix-desktop/src/features/upload/
└── components/
    ├── GoogleDriveSelector.tsx          # Main container
    ├── DriveAccountSelector.tsx         # Account dropdown
    ├── DriveFileExplorer.tsx            # File browser
    ├── DriveBreadcrumbs.tsx             # Folder navigation
    ├── DriveFileList.tsx                # File grid/list
    ├── DriveFileItem.tsx                # Individual file card
    └── DriveSearchBar.tsx               # Search input
```

**State Management:**
```typescript
// useGoogleDrive.ts hook
{
  selectedAccount: string | null,
  currentFolder: string | null,
  files: DriveFile[],
  selectedFiles: Set<string>,
  breadcrumbs: BreadcrumbItem[],
  viewMode: 'grid' | 'list',
  isLoading: boolean,
  error: string | null
}
```

**Modern UI Features:**

**1. Account Selector:**
```
┌────────────────────────────────────────────┐
│ 📧 work@company.com            ▼           │
│ ─────────────────────────────────────      │
│   📧 work@company.com                      │
│   📧 personal@gmail.com                    │
│   ─────────────────                        │
│   ➕ Add Another Account                   │
└────────────────────────────────────────────┘
```

**2. Search & Filter Bar:**
```
┌────────────────────────────────────────────┐
│ 🔍 [Search in Drive...]   📁 Grid  ☰ List │
│                          [🔽 PDF] [🔽 All] │
└────────────────────────────────────────────┘
```
- Real-time search (debounced API calls)
- File type filter dropdown
- View mode toggle (grid/list)

**3. Breadcrumb Navigation:**
```
┌────────────────────────────────────────────┐
│ 📂 My Drive › 📁 Documents › 📁 Work       │
└────────────────────────────────────────────┘
```
- Click any breadcrumb to navigate back
- Smooth slide transitions between folders

**4. File Grid View:**
```
┌──────────┐ ┌──────────┐ ┌──────────┐
│ [✓]      │ │ [ ]      │ │ [✓]      │
│ 📄       │ │ 📊       │ │ 🖼️       │
│ Contract │ │ Report   │ │ Diagram  │
│ 2.3 MB   │ │ 1.1 MB   │ │ 234 KB   │
└──────────┘ └──────────┘ └──────────┘
```
- Thumbnail preview for images
- File type icons
- Checkbox selection
- Hover effects

**5. File List View:**
```
┌────────────────────────────────────────────┐
│ [✓] 📄 Contract_2024.pdf    2.3 MB  Oct 10│
│ [ ] 📊 Report_Q3.xlsx       1.1 MB  Oct 12│
│ [✓] 🖼️  Diagram.png         234 KB  Oct 11│
└────────────────────────────────────────────┘
```
- Compact row layout
- Sortable columns
- Quick selection

**6. Selection Actions:**
```
┌────────────────────────────────────────────┐
│ 3 files selected (3.4 MB)                  │
│ [Select All] [Clear Selection]             │
│                      [Upload Selected]     │
└────────────────────────────────────────────┘
```

**7. Loading States:**
- Skeleton screens while fetching
- Shimmer effect on file cards
- Progress spinner on file actions

**8. Empty States:**
```
┌────────────────────────────────────────────┐
│            📁                               │
│     No files in this folder                │
│                                            │
│   Upload files to your Google Drive        │
│   to see them here                         │
└────────────────────────────────────────────┘
```

**9. Error States:**
```
┌────────────────────────────────────────────┐
│            ⚠️                              │
│   Failed to load Drive files               │
│                                            │
│   [Reconnect Account] [Try Again]          │
└────────────────────────────────────────────┘
```

---

### **Upload Flow - Drive to Pipeline**

**Step-by-Step:**

1. **User selects files** → `selectedFiles` Set updated
2. **Click "Upload Selected"** → Trigger upload
3. **Frontend calls:** `POST /api/google/drive/download`
   - Body: `{account_id, file_ids: [...]}`
4. **Backend downloads from Drive:**
   - For each file_id: `GET https://www.googleapis.com/drive/v3/files/{id}?alt=media`
   - Uses account's access_token
5. **Convert to UploadFile objects:**
   - Create in-memory file representations
   - Extract filename, mime_type, size
6. **Pass to existing upload pipeline:**
   - Call `DocumentService.upload_document()` for each
   - Same RAG processing as local files
7. **Stream progress to frontend:**
   - SSE or WebSocket updates
   - Show per-file status
8. **Complete:**
   - Show success/failure per file
   - Clear selection
   - Offer to upload more

**No Changes to Existing Pipeline:**
- Drive files → UploadFile → DocumentService
- Same OCR, text extraction, RAG insertion
- Same error handling
- Same progress tracking

---

### **Error Handling & Edge Cases**

**Token Expiration:**
- Backend detects 401 from Drive API
- Automatically refreshes using refresh_token
- Retries original request
- If refresh fails → prompt user to reconnect

**Network Failures:**
- Exponential backoff retry (3 attempts)
- Show error toast
- Offer manual retry

**Quota Limits:**
- Detect quota error from Google API
- Show user-friendly message
- Suggest trying again later

**Large File Handling:**
- Warn if file > 50MB (existing limit)
- Stream download (don't load entire file in memory)
- Show download progress separately from upload progress

**Unsupported File Types:**
- Filter in file list (don't show)
- If user somehow selects → show error message
- List supported types in error

---

### **Security Considerations**

**Token Security:**
- Never log tokens
- Encrypt in storage (electron-store)
- Never send to frontend (backend holds tokens)
- Revoke on account removal

**Scope Minimization:**
- Request only `drive.readonly` scope
- No write/delete permissions
- No access to non-Drive Google services

**HTTPS Enforcement:**
- All Google API calls over HTTPS
- OAuth callback via localhost (secure in desktop context)

**Rate Limiting:**
- Implement request queuing
- Respect Google API quotas
- Exponential backoff on 429 errors

---

This breakdown provides the complete technical foundation for implementation while maintaining clean separation of concerns and modern UX patterns.