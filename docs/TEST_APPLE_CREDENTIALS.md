# Test Apple Credentials Locally

This guide shows you how to verify all your Apple credentials are valid and correctly formatted **before** pushing to GitHub Actions.

## Prerequisites

- macOS machine (required for certificate testing)
- Your Developer ID Application certificate installed in Keychain
- Apple Developer account credentials

## Test 1: Verify Certificate Identity and Team ID

### Check Installed Certificates

```bash
# List all Developer ID Application certificates
security find-identity -v -p codesigning

# Expected output should include:
# 1) AA071B68E9A27A08582D598461A5D178412488F1 "Developer ID Application: Your Name (TEAM_ID_HERE)"
```

**What to check:**
- ✅ You see "Developer ID Application" certificate(s)
- ✅ Note the 40-character hex identity (e.g., `AA071B68E9A27A08582D598461A5D178412488F1`)
- ✅ Note the 10-character Team ID in parentheses at the end

### Extract Team ID from Certificate

```bash
# Get detailed certificate info
security find-certificate -c "Developer ID Application" -p | openssl x509 -text -noout | grep "Subject:"

# Look for "OU = XXXXXXXXXX" in the output - that's your Team ID
```

**Alternative method if you have the .p12 file:**

```bash
# If you have your certificate exported as .p12:
openssl pkcs12 -in /path/to/your-cert.p12 -nokeys -passin pass:YOUR_P12_PASSWORD | openssl x509 -noout -text | grep "OU="

# The value after "OU=" is your APPLE_TEAM_ID
```

### Verify Certificate Validity

```bash
# Check certificate expiration
security find-certificate -c "Developer ID Application" -p | openssl x509 -noout -dates

# Output shows:
# notBefore=... (when it was issued)
# notAfter=...  (when it expires) ⚠️ Make sure this is in the future!
```

## Test 2: Verify Apple ID Format

```bash
# Your APPLE_ID should be an email address
# No command needed - just verify it matches this regex pattern:

# Valid format: name@example.com
# Common mistakes:
#   ❌ Missing @
#   ❌ Extra spaces
#   ❌ Wrong email (not the one used for developer.apple.com)
```

**Verify your Apple ID:**
1. Go to https://developer.apple.com/account
2. Sign in with your Apple ID
3. The email you used to sign in is your `APPLE_ID`

## Test 3: Verify Team ID Format

```bash
# Your APPLE_TEAM_ID should be exactly 10 uppercase alphanumeric characters
# Test with this command:

TEAM_ID="YOUR_TEAM_ID_HERE"

if [[ "$TEAM_ID" =~ ^[A-Z0-9]{10}$ ]]; then
    echo "✅ Team ID format is valid"
else
    echo "❌ Team ID format is invalid (expected: 10 uppercase alphanumeric chars)"
    echo "   Current length: ${#TEAM_ID}"
fi
```

**Get your Team ID:**
1. Go to https://developer.apple.com/account
2. Look in the top-right corner
3. You'll see "Team ID: XXXXXXXXXX"

## Test 4: Verify App-Specific Password Format

```bash
# Your APPLE_APP_PASSWORD should be in format: xxxx-xxxx-xxxx-xxxx

APP_PASSWORD="YOUR_APP_PASSWORD_HERE"

if [[ "$APP_PASSWORD" =~ ^[a-z]{4}-[a-z]{4}-[a-z]{4}-[a-z]{4}$ ]]; then
    echo "✅ App-Specific Password format is valid"
else
    echo "❌ App-Specific Password format is invalid"
    echo "   Expected: xxxx-xxxx-xxxx-xxxx (19 chars, lowercase with hyphens)"
    echo "   Current length: ${#APP_PASSWORD}"
fi
```

**Generate a new App-Specific Password:**
1. Go to https://appleid.apple.com/account/manage
2. Sign in with your Apple ID
3. Security → App-Specific Passwords
4. Click "Generate Password..."
5. Name it: "GitHub Actions Notarization"
6. Copy the password (format: `abcd-efgh-ijkl-mnop`)

## Test 5: Test Notarization Credentials with Apple

This is the **most important test** - it verifies Apple will accept your credentials.

### Create a Test App to Notarize

```bash
# Create a simple test app
mkdir -p TestApp.app/Contents/MacOS
cat > TestApp.app/Contents/MacOS/test << 'EOF'
#!/bin/bash
echo "Test app"
EOF
chmod +x TestApp.app/Contents/MacOS/test

# Create minimal Info.plist
cat > TestApp.app/Contents/Info.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>test</string>
    <key>CFBundleIdentifier</key>
    <string>com.test.app</string>
    <key>CFBundleName</key>
    <string>Test</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
</dict>
</plist>
EOF
```

### Sign the Test App

```bash
# Sign with your Developer ID certificate
# Replace "Developer ID Application: Your Name (TEAM_ID)" with your actual certificate name
codesign --force --options runtime --sign "Developer ID Application" --timestamp TestApp.app

# Verify signing
codesign -vvv --deep --strict TestApp.app

# Expected output: "TestApp.app: valid on disk" and "satisfies its Designated Requirement"
```

### Create DMG for Notarization

```bash
# Create a DMG from the signed app
hdiutil create -volname "TestApp" -srcfolder TestApp.app -ov -format UDZO TestApp.dmg
```

### Test Notarization (The Critical Test!)

```bash
# Set your credentials
export APPLE_ID="your-apple-id@example.com"
export APPLE_APP_PASSWORD="xxxx-xxxx-xxxx-xxxx"
export APPLE_TEAM_ID="XXXXXXXXXX"

# Submit for notarization
xcrun notarytool submit TestApp.dmg \
    --apple-id "$APPLE_ID" \
    --password "$APPLE_APP_PASSWORD" \
    --team-id "$APPLE_TEAM_ID" \
    --wait

# Expected outputs:
# ✅ SUCCESS: "status: Accepted" - Your credentials work!
# ❌ ERROR: "Invalid credentials" - One or more credentials are wrong
# ❌ ERROR: "Invalid team" - Team ID doesn't match Apple ID
```

### Check Notarization Status

```bash
# If submission succeeded, check the log
xcrun notarytool log <SUBMISSION_ID> \
    --apple-id "$APPLE_ID" \
    --password "$APPLE_APP_PASSWORD" \
    --team-id "$APPLE_TEAM_ID"
```

### Clean Up

```bash
# Remove test files
rm -rf TestApp.app TestApp.dmg
```

## Test 6: Verify CSC_LINK (Certificate) Format

If you need to verify your base64-encoded certificate:

### On macOS:

```bash
# If you have the .p12 file, encode it:
base64 -i /path/to/your-cert.p12 -o cert-base64.txt

# To verify it can be decoded:
base64 -D -i cert-base64.txt -o test-cert.p12

# Try to read it (will prompt for password):
openssl pkcs12 -in test-cert.p12 -noout -passin pass:YOUR_P12_PASSWORD

# If successful, your CSC_LINK is valid
# Clean up:
rm test-cert.p12
```

### On Windows (PowerShell):

```powershell
# Encode certificate to base64
[Convert]::ToBase64String([IO.File]::ReadAllBytes("C:\path\to\your-cert.p12")) | Out-File cert-base64.txt

# To verify, decode it back:
[IO.File]::WriteAllBytes("test-cert.p12", [Convert]::FromBase64String((Get-Content cert-base64.txt)))

# If no errors, your CSC_LINK is valid
```

## Test 7: Complete Credential Validation Script

Here's a complete script to test everything at once:

```bash
#!/bin/bash

echo "========================================"
echo "Apple Credential Validation Script"
echo "========================================"
echo ""

# Set your credentials here
APPLE_ID="your-apple-id@example.com"
APPLE_APP_PASSWORD="xxxx-xxxx-xxxx-xxxx"
APPLE_TEAM_ID="XXXXXXXXXX"

# Test 1: Certificate
echo "Test 1: Checking for Developer ID Application certificate..."
if security find-identity -v -p codesigning | grep -q "Developer ID Application"; then
    echo "✅ Certificate found"
    security find-identity -v -p codesigning | grep "Developer ID Application"
else
    echo "❌ No Developer ID Application certificate found"
    exit 1
fi
echo ""

# Test 2: Apple ID format
echo "Test 2: Validating Apple ID format..."
if [[ "$APPLE_ID" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
    echo "✅ Apple ID format is valid: $APPLE_ID"
else
    echo "❌ Apple ID format is invalid"
    exit 1
fi
echo ""

# Test 3: Team ID format
echo "Test 3: Validating Team ID format..."
if [[ "$APPLE_TEAM_ID" =~ ^[A-Z0-9]{10}$ ]]; then
    echo "✅ Team ID format is valid: $APPLE_TEAM_ID"
else
    echo "❌ Team ID format is invalid (expected: 10 uppercase alphanumeric)"
    echo "   Current: $APPLE_TEAM_ID (length: ${#APPLE_TEAM_ID})"
    exit 1
fi
echo ""

# Test 4: App-Specific Password format
echo "Test 4: Validating App-Specific Password format..."
if [[ "$APPLE_APP_PASSWORD" =~ ^[a-z]{4}-[a-z]{4}-[a-z]{4}-[a-z]{4}$ ]]; then
    echo "✅ App-Specific Password format is valid"
else
    echo "⚠️  App-Specific Password format might be invalid"
    echo "   Expected: xxxx-xxxx-xxxx-xxxx (19 chars)"
    echo "   Current length: ${#APPLE_APP_PASSWORD}"
fi
echo ""

# Test 5: Team ID matches certificate
echo "Test 5: Checking if Team ID matches certificate..."
CERT_TEAM_ID=$(security find-certificate -c "Developer ID Application" -p | openssl x509 -noout -text | grep "OU=" | sed -n 's/.*OU=\([A-Z0-9]*\).*/\1/p' | head -1)
if [ "$CERT_TEAM_ID" == "$APPLE_TEAM_ID" ]; then
    echo "✅ Team ID matches certificate: $CERT_TEAM_ID"
else
    echo "❌ Team ID mismatch!"
    echo "   Certificate Team ID: $CERT_TEAM_ID"
    echo "   Your APPLE_TEAM_ID: $APPLE_TEAM_ID"
    exit 1
fi
echo ""

# Test 6: Certificate expiration
echo "Test 6: Checking certificate expiration..."
CERT_END=$(security find-certificate -c "Developer ID Application" -p | openssl x509 -noout -enddate | cut -d= -f2)
echo "   Certificate expires: $CERT_END"
CERT_END_EPOCH=$(date -j -f "%b %d %T %Y %Z" "$CERT_END" "+%s" 2>/dev/null)
NOW_EPOCH=$(date "+%s")
if [ $CERT_END_EPOCH -gt $NOW_EPOCH ]; then
    echo "✅ Certificate is still valid"
else
    echo "❌ Certificate has expired!"
    exit 1
fi
echo ""

# Test 7: Test notarization credentials
echo "Test 7: Testing notarization credentials with Apple..."
echo "   (This will create a test app, sign it, and submit to Apple)"
echo ""

# Create test app
mkdir -p TestApp.app/Contents/MacOS
cat > TestApp.app/Contents/MacOS/test << 'EOFTEST'
#!/bin/bash
echo "test"
EOFTEST
chmod +x TestApp.app/Contents/MacOS/test

cat > TestApp.app/Contents/Info.plist << 'EOFTEST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>test</string>
    <key>CFBundleIdentifier</key>
    <string>com.test.credential.check</string>
</dict>
</plist>
EOFTEST

# Sign
echo "   Signing test app..."
codesign --force --options runtime --sign "Developer ID Application" --timestamp TestApp.app 2>&1 | head -3

# Create DMG
echo "   Creating DMG..."
hdiutil create -volname "Test" -srcfolder TestApp.app -ov -format UDZO TestApp.dmg > /dev/null 2>&1

# Submit to Apple
echo "   Submitting to Apple for notarization..."
echo "   (This may take 1-2 minutes...)"
RESULT=$(xcrun notarytool submit TestApp.dmg \
    --apple-id "$APPLE_ID" \
    --password "$APPLE_APP_PASSWORD" \
    --team-id "$APPLE_TEAM_ID" \
    --wait 2>&1)

if echo "$RESULT" | grep -q "status: Accepted"; then
    echo "✅ Notarization credentials are VALID! Apple accepted the test submission."
elif echo "$RESULT" | grep -q "Invalid credentials"; then
    echo "❌ Invalid credentials! Apple rejected authentication."
    echo "   Most likely: APPLE_APP_PASSWORD is wrong - generate a new one"
elif echo "$RESULT" | grep -q "Invalid team"; then
    echo "❌ Invalid team! APPLE_TEAM_ID doesn't match your Apple ID."
else
    echo "⚠️  Notarization test result:"
    echo "$RESULT" | head -10
fi

# Clean up
rm -rf TestApp.app TestApp.dmg

echo ""
echo "========================================"
echo "Validation Complete"
echo "========================================"
```

## Save and Run the Script

```bash
# Save the script above as test-credentials.sh
chmod +x test-credentials.sh

# Edit it to add your credentials
nano test-credentials.sh

# Run it
./test-credentials.sh
```

## Expected Output for Valid Credentials

```
========================================
Apple Credential Validation Script
========================================

Test 1: Checking for Developer ID Application certificate...
✅ Certificate found
1) AA071B68E9A27A08582D598461A5D178412488F1 "Developer ID Application: Your Name (XXXXXXXXXX)"

Test 2: Validating Apple ID format...
✅ Apple ID format is valid: your@email.com

Test 3: Validating Team ID format...
✅ Team ID format is valid: XXXXXXXXXX

Test 4: Validating App-Specific Password format...
✅ App-Specific Password format is valid

Test 5: Checking if Team ID matches certificate...
✅ Team ID matches certificate: XXXXXXXXXX

Test 6: Checking certificate expiration...
   Certificate expires: Dec 31 23:59:59 2025 GMT
✅ Certificate is still valid

Test 7: Testing notarization credentials with Apple...
   Signing test app...
   Creating DMG...
   Submitting to Apple for notarization...
   (This may take 1-2 minutes...)
✅ Notarization credentials are VALID! Apple accepted the test submission.

========================================
Validation Complete
========================================
```

## Troubleshooting Common Errors

### "No Developer ID Application certificate found"
- You need to install your Developer ID certificate in Keychain
- Download from https://developer.apple.com/account/resources/certificates

### "Invalid credentials"
- Your APPLE_APP_PASSWORD is wrong or expired
- Generate a new app-specific password at https://appleid.apple.com

### "Invalid team"
- Your APPLE_TEAM_ID doesn't match the Apple ID
- Verify at https://developer.apple.com/account

### "Certificate has expired"
- Renew your Developer ID certificate
- Download new certificate and install in Keychain

## Next Steps

Once all tests pass:
1. Copy the exact values you used in the script
2. Update GitHub Secrets with these values
3. Push to trigger GitHub Actions build
4. The build should now succeed!

