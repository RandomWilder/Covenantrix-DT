# Phase 2 Testing Guide - Profile & Google OAuth

## Prerequisites

### 1. Backend Requirements
- [ ] Backend server running on `http://localhost:8000`
- [ ] Google OAuth credentials configured in `.env`:
  ```
  GOOGLE_CLIENT_ID=your_client_id
  GOOGLE_CLIENT_SECRET=your_client_secret
  GOOGLE_REDIRECT_URI=http://localhost:8000/oauth/callback
  ```

### 2. Google Cloud Console Setup
- [ ] Google Cloud project created/selected
- [ ] OAuth 2.0 Client ID configured (Desktop app)
- [ ] Redirect URI added: `http://localhost:8000/oauth/callback`
- [ ] Drive API enabled
- [ ] OAuth consent screen configured

### 3. Clean State
- [ ] Delete `~/.covenantrix/rag_storage/user_settings.json` for fresh start
- [ ] Alternatively, backup existing settings

---

## Test Plan

### Test 1: Backend Health Check ✅

**Objective:** Verify backend is running and OAuth endpoints are available

**Steps:**
1. Start backend server
2. Test health endpoint
3. Test Google OAuth endpoints exist

**Commands:**
```bash
# From project root
cd backend
python main.py

# In another terminal
curl http://localhost:8000/health
curl http://localhost:8000/api/google/accounts
```

**Expected Results:**
- ✅ Backend starts without errors
- ✅ Health endpoint returns 200
- ✅ `/api/google/accounts` returns `{"success": true, "accounts": []}`

**Pass/Fail:** ____

---

### Test 2: Fresh Onboarding with Profile Step ✅

**Objective:** Verify profile step is integrated into onboarding wizard

**Steps:**
1. Delete `user_settings.json` if exists
2. Start Electron app
3. Verify onboarding wizard appears
4. Count total steps

**Expected Steps:**
1. Welcome
2. **Profile Setup (NEW)** ⭐
3. API Keys
4. Language
5. AI Configuration
6. Appearance
7. Complete

**Profile Step Verification:**
- [ ] Three optional text inputs visible (First Name, Last Name, Email)
- [ ] Info message about Google Drive appears
- [ ] "Skip" and "Save & Continue" buttons visible
- [ ] All fields are optional (can proceed with empty fields)

**Test Cases:**

**2a. Skip Profile (Empty)**
- Leave all fields empty
- Click "Next"
- Profile step completes ✅

**2b. Partial Profile**
- Enter: First Name only
- Click "Next"
- Setting saved with only first_name ✅

**2c. Complete Profile**
- Enter: John | Doe | john.doe@test.com
- Click "Next"
- All fields saved ✅

**Pass/Fail:** ____

**Evidence:** Screenshot of profile step

---

### Test 3: Settings Persistence ✅

**Objective:** Verify profile data is saved to `user_settings.json`

**Steps:**
1. Complete onboarding with profile data
2. Check `~/.covenantrix/rag_storage/user_settings.json`
3. Verify profile section exists

**Expected JSON Structure:**
```json
{
  "profile": {
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@test.com"
  },
  "google_accounts": [],
  "api_keys": { ... },
  "rag": { ... },
  ...
}
```

**Verification:**
- [ ] `profile` section exists
- [ ] Values match what was entered
- [ ] `google_accounts` array exists (empty initially)
- [ ] No plaintext sensitive data

**Pass/Fail:** ____

**Evidence:** JSON content (sanitized)

---

### Test 4: Profile Modal Access ✅

**Objective:** Verify profile modal can be opened from status bar

**Steps:**
1. Complete onboarding
2. Locate status bar (bottom-right)
3. Find user icon button
4. Click user icon

**Expected Results:**
- [ ] User icon visible in status bar
- [ ] Icon has hover effect
- [ ] Clicking opens profile modal
- [ ] Modal appears centered
- [ ] Modal has backdrop overlay
- [ ] Three tabs visible: "User Info", "Connected Accounts", "API Keys"

**Modal Verification:**
- [ ] Close button (X) works
- [ ] Clicking backdrop closes modal
- [ ] Modal is responsive (not too large/small)

**Pass/Fail:** ____

**Evidence:** Screenshot of profile modal

---

### Test 5: User Info Tab ✅

**Objective:** Test profile information editing

**Steps:**
1. Open profile modal
2. Ensure "User Info" tab is active
3. Verify existing data is loaded
4. Edit fields
5. Save changes

**Test Cases:**

**5a. View Existing Data**
- Profile data from onboarding is pre-filled ✅
- Fields are editable ✅

**5b. Update Profile**
- Change First Name to "Jane"
- Click "Save Changes"
- Success toast appears ✅
- Reload app, verify changes persisted ✅

**5c. Clear Profile**
- Clear all fields (empty strings)
- Click "Save Changes"
- Fields saved as undefined ✅

**5d. Validation**
- Enter invalid email format
- Save should work (validation is optional) ✅

**Save Button Behavior:**
- [ ] Disabled when no changes
- [ ] Enabled when fields modified
- [ ] Shows "Saving..." during save
- [ ] Returns to "Save Changes" after

**Pass/Fail:** ____

---

### Test 6: Connected Accounts Tab - Empty State ✅

**Objective:** Test empty state when no accounts connected

**Steps:**
1. Open profile modal
2. Click "Connected Accounts" tab
3. Verify empty state

**Expected Empty State:**
- [ ] Cloud icon displayed
- [ ] "No accounts connected" heading
- [ ] Descriptive text about Google Drive
- [ ] "Connect Google Drive" button visible
- [ ] Info box about connections security

**Pass/Fail:** ____

**Evidence:** Screenshot of empty state

---

### Test 7: Google OAuth Flow - Complete ✅

**Objective:** Test full OAuth authentication flow

**Prerequisites:**
- Google OAuth credentials configured
- Internet connection active

**Steps:**
1. In "Connected Accounts" tab
2. Click "Connect Google Drive"
3. OAuth window opens
4. Complete Google authentication
5. Verify account appears

**Detailed Verification:**

**7a. OAuth Window Opens**
- [ ] Separate window opens (modal, not browser tab)
- [ ] Window title: "Google Authentication"
- [ ] Window shows Google login page
- [ ] Window is 500x600px
- [ ] Parent window remains visible but inactive

**7b. Google Authentication**
- [ ] Can log in to Google account
- [ ] OAuth consent screen appears
- [ ] Requested scopes shown:
  - Drive (read-only)
  - Email
  - Profile
- [ ] Can grant permission

**7c. Callback Handling**
- [ ] After granting permission, window closes automatically ✅
- [ ] Success toast appears: "Connected {email} successfully" ✅
- [ ] Account card appears in list ✅
- [ ] Loading state clears ✅

**7d. Account Card Display**
- [ ] Email address visible
- [ ] Display name shown (if available)
- [ ] Status badge: "Connected" (green)
- [ ] Connected date formatted correctly
- [ ] Last used: "Just now"
- [ ] Scopes displayed as chips
- [ ] Remove button visible

**Pass/Fail:** ____

**Evidence:** Screenshots of OAuth flow

---

### Test 8: Account Card Details ✅

**Objective:** Verify account card shows correct information

**Steps:**
1. With connected account visible
2. Examine account card details

**Verification Checklist:**
- [ ] **Email:** Exact Google account email
- [ ] **Display Name:** Name from Google profile (or empty)
- [ ] **Status:** "Connected" with green indicator
- [ ] **Connected At:** Formatted date (e.g., "Oct 13, 2025")
- [ ] **Last Used:** Relative time (e.g., "Just now", "2 hours ago")
- [ ] **Scopes:** 3 chips visible:
  - `drive.readonly`
  - `userinfo.email`
  - `userinfo.profile`

**Pass/Fail:** ____

---

### Test 9: Multiple Accounts ✅

**Objective:** Test connecting multiple Google accounts

**Steps:**
1. Connect first account (already done)
2. Click "Connect Google Drive" again
3. Authenticate with different Google account
4. Verify both accounts listed

**Expected Results:**
- [ ] Can connect second account
- [ ] Both accounts visible in list
- [ ] Each has unique account_id
- [ ] Both show correct emails
- [ ] Both have "Connected" status
- [ ] Cards stacked vertically with spacing

**Pass/Fail:** ____

---

### Test 10: Account Removal ✅

**Objective:** Test removing connected account

**Steps:**
1. With account(s) connected
2. Click Remove button (trash icon)
3. Confirm removal
4. Verify account removed

**Detailed Steps:**

**10a. Confirmation Dialog**
- [ ] Clicking trash icon shows modal dialog
- [ ] Dialog centered on screen (z-index higher than profile modal)
- [ ] "Remove Account" title
- [ ] Warning message clear
- [ ] "Cancel" and "Remove" buttons

**10b. Cancel Removal**
- [ ] Click "Cancel"
- [ ] Dialog closes
- [ ] Account still in list ✅

**10c. Confirm Removal**
- [ ] Click "Remove"
- [ ] Success toast: "Account removed successfully"
- [ ] Account disappears from list
- [ ] If last account, empty state returns

**10d. Backend Verification**
- [ ] Account removed from `user_settings.json`
- [ ] Token revoked with Google API
- [ ] Settings reloaded properly

**Pass/Fail:** ____

---

### Test 11: Settings Persistence - Accounts ✅

**Objective:** Verify Google accounts persist across app restarts

**Steps:**
1. Connect Google account
2. Close app completely
3. Check `user_settings.json`
4. Reopen app
5. Open Connected Accounts tab

**Verification:**

**11a. Storage Format**
```json
{
  "google_accounts": [
    {
      "account_id": "uuid-here",
      "email": "user@gmail.com",
      "display_name": "User Name",
      "status": "connected",
      "connected_at": "2025-10-13T12:34:56",
      "last_used": "2025-10-13T12:34:56",
      "scopes": ["drive.readonly", "userinfo.email", "userinfo.profile"],
      "access_token": "encrypted-token",
      "refresh_token": "encrypted-token",
      "token_expiry": "2025-10-13T13:34:56"
    }
  ]
}
```

**11b. Encryption Verification**
- [ ] `access_token` is encrypted (base64/gibberish, not plain JWT)
- [ ] `refresh_token` is encrypted
- [ ] No plaintext Google tokens

**11c. Reload Verification**
- [ ] After restart, account appears in list
- [ ] Email, name, status correct
- [ ] Connected/last used dates preserved
- [ ] Can still use account (token decrypted properly)

**Pass/Fail:** ____

---

### Test 12: API Keys Tab Integration ✅

**Objective:** Verify API Keys tab works within profile modal

**Steps:**
1. Open profile modal
2. Click "API Keys" tab
3. Test API key management

**Expected Behavior:**
- [ ] Tab switches to API keys view
- [ ] Existing ApiKeysTab component renders
- [ ] Shows current API key mode (default/custom)
- [ ] Can switch modes
- [ ] Can enter/edit custom keys
- [ ] Save functionality works
- [ ] Changes persist

**Verification:**
- [ ] Same functionality as Settings > API Keys
- [ ] No duplicate state issues
- [ ] Updates reflected in main settings

**Pass/Fail:** ____

---

### Test 13: Error Handling - OAuth Failures ❌

**Objective:** Test error scenarios in OAuth flow

**Test Cases:**

**13a. User Cancels OAuth**
- Click "Connect Google Drive"
- In OAuth window, click "Cancel" or close window
- Expected: Error toast or loading clears ✅

**13b. Network Failure**
- Disconnect internet
- Try to connect account
- Expected: "Failed to start OAuth flow" error ✅

**13c. Backend Down**
- Stop backend server
- Try to connect account
- Expected: Connection error message ✅

**13d. Invalid Credentials**
- Configure invalid OAuth client ID in `.env`
- Restart backend
- Try to connect
- Expected: OAuth error from Google ✅

**Pass/Fail:** ____

---

### Test 14: Memory Leak Tests ✅

**Objective:** Verify fixes for identified memory leaks

**Test Cases:**

**14a. OAuth Callback Listener Cleanup**
- Open/close Connected Accounts tab 10 times
- Connect account once
- Verify only ONE success toast appears ✅
- Check Chrome DevTools > Memory > Take Heap Snapshot
- No accumulation of listeners ✅

**14b. OAuth State Expiration**
- Start OAuth flow
- Don't complete (abandon in browser)
- Wait 11 minutes
- Try to use callback code
- Expected: "Invalid or expired state parameter" error ✅

**14c. Settings Re-render Loop**
- Open Connected Accounts tab
- Watch Network tab in DevTools
- Should see only ONE API call to `/api/google/accounts` on mount ✅
- Changing other settings should NOT trigger reload ✅

**Pass/Fail:** ____

---

### Test 15: UI/UX Verification ✅

**Objective:** Test user experience and visual polish

**Checklist:**

**Loading States:**
- [ ] OAuth "Connecting..." button shows spinner
- [ ] Account list shows spinner while loading
- [ ] Skeleton/shimmer states (if implemented)

**Empty States:**
- [ ] No accounts: Clear call-to-action
- [ ] No errors: Clean UI

**Error States:**
- [ ] Error messages user-friendly
- [ ] Red error banner with icon
- [ ] Retry/dismiss options

**Responsive Design:**
- [ ] Modal adapts to window size
- [ ] Account cards look good at different widths
- [ ] No horizontal scroll

**Dark Mode:**
- [ ] Profile modal works in dark mode
- [ ] All text readable
- [ ] Proper contrast

**Accessibility:**
- [ ] Can navigate with keyboard (Tab key)
- [ ] Focus indicators visible
- [ ] Buttons have hover states

**Pass/Fail:** ____

---

## Backend API Tests

### Test 16: Backend Endpoints ✅

**Objective:** Test backend API endpoints directly

**Endpoints to Test:**

**16a. List Accounts**
```bash
curl http://localhost:8000/api/google/accounts
```
Expected: `{"success": true, "accounts": [...]}`

**16b. Initiate OAuth**
```bash
curl -X POST http://localhost:8000/api/google/accounts/connect
```
Expected: `{"success": true, "auth_url": "https://accounts.google.com/...", "message": "..."}`

**16c. Handle Callback** (with real code from OAuth)
```bash
curl -X POST "http://localhost:8000/api/google/accounts/callback?code=<code>&state=<state>"
```
Expected: Account created and returned

**16d. Remove Account**
```bash
curl -X DELETE http://localhost:8000/api/google/accounts/<account_id>
```
Expected: `{"success": true, "message": "..."}`

**Pass/Fail:** ____

---

## Test Results Summary

### Critical Functionality
- [ ] Onboarding includes profile step
- [ ] Profile modal opens from status bar
- [ ] User info can be edited and saved
- [ ] OAuth flow completes successfully
- [ ] Accounts persist across restarts
- [ ] Accounts can be removed

### Memory Leak Fixes
- [ ] Callback listener cleanup working
- [ ] OAuth state expiration working
- [ ] No re-render loops

### Data Integrity
- [ ] Settings saved correctly
- [ ] Tokens encrypted
- [ ] No data loss on restart

### User Experience
- [ ] Loading states clear
- [ ] Error messages helpful
- [ ] UI is polished

---

## Known Issues / Notes

_Document any issues found during testing:_

1. Issue: _______________
   - Severity: ___
   - Reproducible: Y/N
   - Steps: ___

2. Issue: _______________
   - Severity: ___
   - Reproducible: Y/N
   - Steps: ___

---

## Sign-off

**Tester:** ________________  
**Date:** ________________  
**Overall Result:** PASS / FAIL / CONDITIONAL  

**Notes:**


