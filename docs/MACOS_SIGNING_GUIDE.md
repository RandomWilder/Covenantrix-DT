# macOS Code Signing & Notarization Guide

## Overview

This guide explains how to properly configure code signing and notarization for your Covenantrix macOS application.

## Current Issueds

Your build is failing with:
```
⨯ Unexpected token 'E', "Error: HTT"... is not valid JSON
```

This error indicates that **Apple's notarization service is rejecting your credentials**. The service returned an HTTP error (likely 401 Unauthorized) instead of valid JSON.

## Required Credentials

You need 5 secrets configured in GitHub (Settings → Secrets and variables → Actions):

| Secret Name | What It Is | How to Get It | Format | Status |
|-------------|------------|---------------|--------|---------|
| **CSC_LINK** | Code signing certificate | Export Developer ID Application cert as .p12, then base64 encode it | Base64 string | ✅ Set |
| **CSC_KEY_PASSWORD** | Certificate password | Password you set when exporting the .p12 | String | ✅ Set |
| **APPLE_ID** | Apple Developer email | Your Apple ID used for developer.apple.com | email@example.com | ✅ Set |
| **APPLE_APP_PASSWORD** | App-specific password | Generated at appleid.apple.com | xxxx-xxxx-xxxx-xxxx | ⚠️ Check |
| **APPLE_TEAM_ID** | Developer Team ID | From developer.apple.com/account | 10 uppercase chars | ⚠️ Check |

## Step-by-Step Fix

### 1. Verify Your Team ID

Your certificate identity is: `AA071B68E9A27A08582D598461A5D178412488F1`

The Team ID **must** match the one embedded in this certificate.

**How to find your Team ID:**

#### Option A: From Apple Developer Portal
1. Go to https://developer.apple.com/account
2. Sign in with your Apple ID
3. Look in the top-right corner for "Team ID"
4. It's a 10-character uppercase alphanumeric string (e.g., `AA071B68E9`)

#### Option B: From Your Certificate
If you have the .p12 certificate file locally:

```bash
# macOS/Linux:
openssl pkcs12 -in your-certificate.p12 -nokeys -passin pass:YOUR_PASSWORD | openssl x509 -noout -text | grep "OU="

# The value after "OU=" is your Team ID
```

#### Option C: From Keychain Access (macOS)
1. Open **Keychain Access** app
2. Search for "Developer ID Application"
3. Double-click your certificate
4. Look for "Organizational Unit" - that's your Team ID

**Action Required:**
- Verify your `APPLE_TEAM_ID` secret matches the Team ID in your certificate
- Update it if it doesn't match

### 2. Generate New App-Specific Password

The most common cause of this error is an invalid App-Specific Password.

**Important:** This is NOT your Apple ID password. It's a separate password for applications.

**How to generate:**

1. Go to https://appleid.apple.com/account/manage
2. Sign in with your Apple ID (the one in `APPLE_ID` secret)
3. Scroll to **Security** section
4. Under **App-Specific Passwords**, click **Generate Password**
5. Label it: "GitHub Actions Notarization"
6. Copy the generated password - format: `xxxx-xxxx-xxxx-xxxx` (19 characters including hyphens)
7. **Update the `APPLE_APP_PASSWORD` secret in GitHub** with this new password

⚠️ **Common Mistakes:**
- Using your Apple ID password (wrong!)
- Using an old/expired app-specific password
- Copying the password with spaces or extra characters

### 3. Verify Apple ID

Make sure the email in `APPLE_ID` secret is:
- The same email you use to log into https://developer.apple.com
- Associated with the Developer ID certificate you're using
- Has an active Apple Developer Program membership

### 4. Verify Certificate (CSC_LINK)

Your certificate should be:
- A "Developer ID Application" certificate (not "Developer ID Installer")
- Exported as a .p12 file
- Base64 encoded

**To create CSC_LINK:**

```bash
# Export certificate from Keychain Access as .p12 file
# Then base64 encode it:

# macOS/Linux:
base64 -i your-certificate.p12 -o certificate-base64.txt

# Windows (PowerShell):
[Convert]::ToBase64String([IO.File]::ReadAllBytes("your-certificate.p12")) | Out-File certificate-base64.txt

# Copy the entire contents of certificate-base64.txt to the CSC_LINK secret
```

## Testing Your Configuration

After updating the secrets, you can test by:

1. Commit and push the updated configuration
2. Check the "Verify macOS Signing Secrets" step in GitHub Actions
3. It will validate the format of each credential
4. The "Test Apple Credentials" step will verify code signing works
5. The build will show detailed debug output with `DEBUG: electron-notarize*`

## Temporary Workaround: Skip Notarization

If you need to build immediately while fixing credentials, you can skip notarization and just sign the app:

**In `covenantrix-desktop/electron-builder.yml`, line 96:**

```yaml
# Change from:
notarize:
  teamId: ${APPLE_TEAM_ID}

# To:
notarize: false
```

This will:
- ✅ Still code sign the app (users can run it)
- ❌ Not notarize it (users will see Gatekeeper warning on first run)
- ✅ Allow your build to complete

You can notarize later using:
```bash
xcrun notarytool submit YourApp.dmg --apple-id <email> --password <app-password> --team-id <team-id> --wait
```

## Common Errors and Solutions

### "The teamId property is required"
- **Cause:** Missing or improperly formatted `teamId` in notarize config
- **Solution:** Use the configuration we have now: `notarize: { teamId: ${APPLE_TEAM_ID} }`

### "Unexpected token 'E', Error: HTT"
- **Cause:** Apple rejected credentials (401 Unauthorized)
- **Solution:** Follow steps 1-4 above to verify all credentials
- **Most likely:** Wrong APPLE_APP_PASSWORD - regenerate it

### "Keychain authorization failed"
- **Cause:** CSC_KEY_PASSWORD is incorrect
- **Solution:** Verify the password you set when exporting the .p12

### "No identity found"
- **Cause:** CSC_LINK is invalid or malformed
- **Solution:** Re-export and re-encode the certificate

## Verification Checklist

Before pushing a new build, verify:

- [ ] APPLE_ID is the correct email (developer.apple.com login)
- [ ] APPLE_APP_PASSWORD is freshly generated (xxxx-xxxx-xxxx-xxxx format)
- [ ] APPLE_TEAM_ID matches the certificate (10 uppercase alphanumeric)
- [ ] CSC_LINK is valid base64 of .p12 file
- [ ] CSC_KEY_PASSWORD matches the .p12 export password
- [ ] All 5 secrets are set in GitHub without extra spaces/newlines
- [ ] Your Apple Developer Program membership is active

## Additional Resources

- [Apple's Notarization Guide](https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution)
- [electron-builder Code Signing](https://www.electron.build/code-signing)
- [App-Specific Passwords](https://support.apple.com/en-us/HT204397)

## Support

If you continue to have issues after following all steps:

1. Check the validation output in the "Verify macOS Signing Secrets" GitHub Action step
2. Look for warnings about credential format
3. Enable debug mode by checking the `DEBUG: electron-notarize*` output in build logs
4. Verify your Apple Developer Program membership is active and in good standing

