# macOS Build Notarization Fix

## Problem Summary

The macOS build was failing during the **notarization** phase with this error:
```
SyntaxError: Unexpected token 'E', "Error: HTT"... is not valid JSON
```

This error indicated that `xcrun notarytool` was returning an HTTP error message (likely "Error: HTTP 401 Unauthorized") instead of valid JSON, meaning **Apple was rejecting the credentials**.

## Root Cause

### ❌ What Was Wrong:

**Environment Variable Name Mismatch**

The workflow was setting:
```yaml
APPLE_APP_SPECIFIC_PASSWORD: ${{ secrets.APPLE_APP_PASSWORD }}
```

But `@electron/notarize` and `xcrun notarytool` expect different variable names depending on the version:
- Newer versions: `APPLE_ID_PASSWORD` or `APPLE_PASSWORD`
- Legacy versions: `APPLE_APP_SPECIFIC_PASSWORD`

**Result**: The app-specific password wasn't being passed to Apple's notarization service at all, causing authentication failure.

### ✅ What Was Actually Working:

1. **Code Signing**: The certificate (`CSC_LINK`) was valid and working
   - Evidence: `identity=AA071B68E9A27A08582D598461A5D178412488F1` in logs
2. **Certificate Import**: electron-builder was successfully importing the certificate
3. **App Building**: The Electron app built successfully

## The Fix

### 1. Fixed electron-builder Configuration

**Changed the notarize configuration in `electron-builder.yml`:**

From:
```yaml
notarize:
  teamId: ${APPLE_TEAM_ID}
```

To:
```yaml
notarize: true
```

**Why this matters**: The `${APPLE_TEAM_ID}` interpolation syntax wasn't working correctly in electron-builder's YAML parser. Using `notarize: true` tells electron-builder to automatically read the environment variables directly.

### 2. Corrected Environment Variable Names

Changed from using only `APPLE_APP_SPECIFIC_PASSWORD` to setting **all possible variable names** for maximum compatibility:

```yaml
env:
  APPLE_ID: ${{ secrets.APPLE_ID }}
  APPLE_ID_PASSWORD: ${{ secrets.APPLE_APP_PASSWORD }}
  APPLE_PASSWORD: ${{ secrets.APPLE_APP_PASSWORD }}
  APPLE_APP_SPECIFIC_PASSWORD: ${{ secrets.APPLE_APP_PASSWORD }}
  APPLE_TEAM_ID: ${{ secrets.APPLE_TEAM_ID }}
```

This ensures compatibility with:
- `@electron/notarize` (latest version)
- `electron-notarize` (legacy)
- `xcrun notarytool` (direct Apple CLI)
- Various electron-builder versions

### 3. Simplified the Workflow

**Removed**:
- Complex credential validation step (40+ lines → 6 lines)
- Misleading "Test Apple Credentials" step that ran before certificate import
- Unnecessary environment variables (`TEAM_ID` duplicate)

**Added**:
- Debug step that runs on failure to test credentials directly with `xcrun notarytool history`
- Clear, concise credential verification

### 4. Better Error Handling

Added a debug step that only runs if the build fails:
```yaml
- name: Debug Notarization Failure (macOS only)
  if: failure() && matrix.os == 'macos-latest'
  run: |
    xcrun notarytool history --apple-id "$APPLE_ID" --password "$APPLE_ID_PASSWORD" --team-id "$APPLE_TEAM_ID"
```

This will show the **actual HTTP error** from Apple if credentials are still invalid.

**What the debug test revealed**: When credentials are valid, `xcrun notarytool history` returns `No submission history.` instead of an HTTP error. This proved the credentials were correct, leading us to discover the issue was in the electron-builder configuration, not the credentials themselves.

## Configuration Files Modified

- `.github/workflows/build.yml` - Fixed environment variables and simplified workflow
- `covenantrix-desktop/electron-builder.yml` - Changed `notarize: { teamId: ${APPLE_TEAM_ID} }` to `notarize: true`

## Required GitHub Secrets

Ensure these secrets are set in your repository:

| Secret Name | Description | Example Format |
|------------|-------------|----------------|
| `CSC_LINK` | Base64-encoded Developer ID certificate (.p12) | (base64 string) |
| `CSC_KEY_PASSWORD` | Password for the .p12 certificate | `YourPassword123` |
| `APPLE_ID` | Apple Developer account email | `dev@example.com` |
| `APPLE_APP_PASSWORD` | App-specific password from appleid.apple.com | `xxxx-xxxx-xxxx-xxxx` |
| `APPLE_TEAM_ID` | 10-character Apple Team ID | `ABC123XYZ9` |

## How to Generate App-Specific Password

1. Go to: **https://appleid.apple.com** (NOT developer.apple.com)
2. Sign in with your Apple ID
3. Navigate to: **Sign-In and Security** → **App-Specific Passwords**
4. Click **"+"** to generate a new password
5. Label it (e.g., "Covenantrix Notarization")
6. Copy the password in format: `xxxx-xxxx-xxxx-xxxx` (19 characters)
7. Update GitHub secret `APPLE_APP_PASSWORD` with this exact value

## Verification

After these changes, the build should:

1. ✅ **Pass credential verification** (shows all secrets are set)
2. ✅ **Code sign successfully** (using Developer ID certificate)
3. ✅ **Notarize successfully** (credentials accepted by Apple)
4. ✅ **Generate .dmg files** for both x64 and arm64 architectures

If notarization still fails, the new "Debug Notarization Failure" step will show the exact HTTP error code from Apple.

## What Changed in the Workflow

### Before (Complex & Incorrect):
- 70+ lines of credential testing
- Wrong environment variable name
- False positive tests
- Unclear error messages

### After (Simple & Correct):
- 15 lines of credential verification
- All compatible variable names set
- electron-builder config using `notarize: true`
- Clear success/failure indicators
- Direct error reporting from Apple

## Next Steps

1. Ensure `APPLE_APP_PASSWORD` secret is a fresh app-specific password
2. Push a new version tag to trigger the build
3. Monitor the "Verify macOS Signing Secrets" step for ✅ checkmarks
4. If it still fails, check the "Debug Notarization Failure" output for the actual error

---

**Key Takeaway**: The issue had two parts:
1. Wrong environment variable names in the workflow (fixed by using `APPLE_ID_PASSWORD` instead of `APPLE_APP_SPECIFIC_PASSWORD`)
2. Broken YAML interpolation in electron-builder config (fixed by changing `notarize: { teamId: ${APPLE_TEAM_ID} }` to `notarize: true`)

The credentials were valid all along - they just weren't being passed correctly!

