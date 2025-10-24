# Test Apple Credentials on Windows

Since you're on Windows and can't run macOS-specific tools, this guide shows you how to validate your Apple credentials before updating GitHub Secrets.

## What Can Be Tested on Windows

✅ **Format Validation:**
- Apple ID email format
- Team ID format (10 characters)
- App-Specific Password format
- Base64 certificate format

❌ **Cannot Test on Windows:**
- Certificate installation/validity
- Code signing
- Actual Apple notarization API

The real authentication test happens when GitHub Actions runs on macOS, but these format checks catch 90% of common mistakes.

## Method 1: PowerShell Script (Recommended for Windows)

### Step 1: Get Your Credentials

First, gather all your credentials from GitHub Secrets (Settings → Secrets and variables → Actions):

1. **APPLE_ID**: Your Apple Developer email
2. **APPLE_APP_PASSWORD**: App-specific password (19 chars with hyphens)
3. **APPLE_TEAM_ID**: 10-character Team ID
4. **CSC_KEY_PASSWORD**: Your .p12 certificate password
5. **CSC_LINK**: Base64 string of your certificate (optional for testing)

### Step 2: Edit the Test Script

Open `test-apple-credentials.ps1` and replace the placeholder values:

```powershell
$APPLE_ID = "your-actual-email@example.com"
$APPLE_APP_PASSWORD = "abcd-efgh-ijkl-mnop"
$APPLE_TEAM_ID = "XXXXXXXXXX"
$CSC_KEY_PASSWORD = "your-actual-p12-password"
```

### Step 3: Run the Script

```powershell
# In PowerShell:
.\test-apple-credentials.ps1
```

### Expected Output

```
========================================
Apple Credentials Validation (Windows)
========================================

Test 1: Validating Apple ID format...
  ✅ Apple ID format is VALID
     Value: your@email.com

Test 2: Validating Apple Team ID format...
  ✅ Team ID format is VALID
     Value: AA071B68E9

Test 3: Validating App-Specific Password format...
  ✅ App-Specific Password format is VALID
     Format: xxxx-xxxx-xxxx-xxxx (correct)

Test 4: Checking CSC_KEY_PASSWORD...
  ✅ CSC_KEY_PASSWORD is set
     Length: 12 characters

Test 5: Validating CSC_LINK (Base64 Certificate)...
  ✅ CSC_LINK appears to be valid Base64
     Length: 4832 characters
  ✅ Decoded size looks reasonable: 3623 bytes

...

✅ All testable validations PASSED!
```

## Method 2: Git Bash Script (Alternative)

If you prefer bash or have Git Bash installed:

### Edit and Run

```bash
# Edit the credentials in test-apple-credentials.sh
nano test-apple-credentials.sh

# Make executable (Git Bash)
chmod +x test-apple-credentials.sh

# Run it
./test-apple-credentials.sh
```

## Method 3: Manual Checks (No Script)

### Check 1: Apple ID Format

Your `APPLE_ID` should be:
- ✅ A valid email address
- ✅ The email you use to log into developer.apple.com
- ❌ NOT have spaces before/after
- ❌ NOT be a different email

**Test in PowerShell:**
```powershell
$email = "your@email.com"
if ($email -match "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$") {
    Write-Host "✅ Valid email format"
} else {
    Write-Host "❌ Invalid email format"
}
```

### Check 2: Team ID Format

Your `APPLE_TEAM_ID` should be:
- ✅ Exactly 10 characters
- ✅ Only uppercase letters and numbers
- ✅ Match the Team ID on developer.apple.com/account

**Get your Team ID:**
1. Go to https://developer.apple.com/account
2. Sign in
3. Look in top-right corner for "Team ID: XXXXXXXXXX"

**Test in PowerShell:**
```powershell
$teamId = "XXXXXXXXXX"
if ($teamId -match "^[A-Z0-9]{10}$") {
    Write-Host "✅ Valid Team ID format"
    Write-Host "Length: $($teamId.Length)"
} else {
    Write-Host "❌ Invalid Team ID format"
    Write-Host "Length: $($teamId.Length) (expected: 10)"
}
```

### Check 3: App-Specific Password Format

Your `APPLE_APP_PASSWORD` should be:
- ✅ Format: `xxxx-xxxx-xxxx-xxxx` (19 characters with hyphens)
- ✅ All lowercase letters
- ✅ Freshly generated (not expired)

**Generate a new one:**
1. Go to https://appleid.apple.com/account/manage
2. Sign in
3. Security → App-Specific Passwords
4. Click "Generate Password"
5. Name it: "GitHub Actions Notarization"
6. Copy the password (includes hyphens)

**Test in PowerShell:**
```powershell
$appPwd = "abcd-efgh-ijkl-mnop"
if ($appPwd -match "^[a-z]{4}-[a-z]{4}-[a-z]{4}-[a-z]{4}$") {
    Write-Host "✅ Valid App-Specific Password format"
    Write-Host "Length: $($appPwd.Length) (expected: 19)"
} else {
    Write-Host "⚠️ Unexpected format (might still work)"
    Write-Host "Length: $($appPwd.Length)"
}
```

### Check 4: CSC_LINK (Certificate Base64)

Your `CSC_LINK` should be:
- ✅ Base64-encoded string
- ✅ Several thousand characters long
- ✅ No spaces or newlines

**Create from .p12 file (PowerShell):**
```powershell
# Convert .p12 to base64
$certPath = "C:\path\to\your-cert.p12"
$base64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes($certPath))
$base64 | Out-File cert-base64.txt

# Check the size
Write-Host "Base64 length: $($base64.Length) characters"
```

**Validate existing base64 (PowerShell):**
```powershell
$base64 = "YOUR_BASE64_STRING_HERE"

try {
    $bytes = [Convert]::FromBase64String($base64)
    Write-Host "✅ Valid Base64"
    Write-Host "Decoded size: $($bytes.Length) bytes"
} catch {
    Write-Host "❌ Invalid Base64"
}
```

### Check 5: CSC_KEY_PASSWORD

Your `CSC_KEY_PASSWORD` should be:
- ✅ The password you set when exporting the .p12 file
- ✅ At least 4 characters (Apple requirement)
- ❌ NOT empty

**No validation needed** - just make sure it matches your certificate password.

## Common Mistakes to Avoid

### ❌ Extra Spaces/Newlines
```
# BAD:
APPLE_ID=" user@email.com "  # spaces!

# GOOD:
APPLE_ID="user@email.com"
```

### ❌ Wrong Email
```
# Make sure it's the SAME email you use for:
# - developer.apple.com
# - The certificate you exported
```

### ❌ Expired App-Specific Password
```
# If you generated it more than a year ago, generate a new one
# Old ones can be revoked or expired
```

### ❌ Wrong Team ID
```
# Team ID must match:
# 1. The one at developer.apple.com/account
# 2. The one embedded in your certificate
# 3. Must be EXACTLY 10 characters
```

### ❌ Certificate Issues
```
# Make sure your .p12 file contains:
# - Private key
# - "Developer ID Application" certificate
# - Not expired
```

## What Happens After Testing

### If All Tests Pass ✅

1. **Copy values to GitHub Secrets**
   - Go to your repo → Settings → Secrets and variables → Actions
   - Update each secret with the exact values you tested
   - **No extra spaces or newlines!**

2. **Commit and push your code changes**
   ```bash
   git add .
   git commit -m "Update macOS signing configuration"
   git push
   ```

3. **Watch the GitHub Actions build**
   - The "Verify macOS Signing Secrets" step will validate formats
   - The "Build Electron App" step will attempt signing and notarization
   - Check the debug output for any issues

### If Tests Fail ❌

**Apple ID Invalid:**
- Double-check it's the correct email
- Make sure it's your developer.apple.com login

**Team ID Invalid:**
- Go to developer.apple.com/account
- Copy the Team ID from the top-right corner
- Must be exactly 10 characters, uppercase

**App-Specific Password Invalid:**
- Generate a NEW password at appleid.apple.com
- Don't reuse old passwords
- Copy it exactly with hyphens

**Certificate Invalid:**
- Re-export your certificate from Keychain Access (macOS required)
- Make sure it's "Developer ID Application" not "Installer"
- Set a password when exporting
- Base64 encode the .p12 file

## Real Authentication Test

The scripts above only validate **format**. The real test is when GitHub Actions runs on macOS and tries to:

1. ✅ Import the certificate (tests `CSC_LINK` and `CSC_KEY_PASSWORD`)
2. ✅ Sign the app (tests certificate validity)
3. ✅ Submit to Apple for notarization (tests `APPLE_ID`, `APPLE_APP_PASSWORD`, `APPLE_TEAM_ID`)

The **"Verify macOS Signing Secrets"** step in your workflow will show detailed validation results.

## Need Help?

If format validation passes but GitHub Actions still fails:

1. Check the exact error in GitHub Actions logs
2. Look for "Invalid credentials" → Wrong App-Specific Password
3. Look for "Invalid team" → Team ID doesn't match Apple ID
4. Look for "Cannot find identity" → Certificate issue

Refer to `docs/MACOS_SIGNING_GUIDE.md` for detailed troubleshooting.

