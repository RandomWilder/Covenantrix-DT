#!/bin/bash
# ============================================
# Apple Credentials Validation Script (Git Bash/WSL)
# ============================================
# This script validates your Apple credentials format without requiring macOS
#
# Usage:
#   1. Edit the variables below with your GitHub Secret values
#   2. Run: bash test-apple-credentials.sh

# ============================================
# YOUR CREDENTIALS - EDIT THESE
# ============================================

APPLE_ID="your-apple-id@example.com"
APPLE_APP_PASSWORD="xxxx-xxxx-xxxx-xxxx"
APPLE_TEAM_ID="XXXXXXXXXX"
CSC_KEY_PASSWORD="your-p12-password"
# For CSC_LINK, paste the base64 string (or leave empty if testing from GitHub)
CSC_LINK=""

# ============================================
# VALIDATION TESTS
# ============================================

echo ""
echo "========================================"
echo "Apple Credentials Validation (Windows)"
echo "========================================"
echo ""

all_valid=true

# Test 1: Apple ID Format
echo "Test 1: Validating Apple ID format..."
if [[ "$APPLE_ID" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
    echo "  ✅ Apple ID format is VALID"
    echo "     Value: $APPLE_ID"
else
    echo "  ❌ Apple ID format is INVALID"
    echo "     Expected: email@example.com"
    echo "     Current: $APPLE_ID"
    all_valid=false
fi
echo ""

# Test 2: Team ID Format
echo "Test 2: Validating Apple Team ID format..."
if [[ "$APPLE_TEAM_ID" =~ ^[A-Z0-9]{10}$ ]]; then
    echo "  ✅ Team ID format is VALID"
    echo "     Value: $APPLE_TEAM_ID"
else
    echo "  ❌ Team ID format is INVALID"
    echo "     Expected: 10 uppercase alphanumeric characters"
    echo "     Current: $APPLE_TEAM_ID (length: ${#APPLE_TEAM_ID})"
    all_valid=false
fi
echo ""

# Test 3: App-Specific Password Format
echo "Test 3: Validating App-Specific Password format..."
if [[ "$APPLE_APP_PASSWORD" =~ ^[a-z]{4}-[a-z]{4}-[a-z]{4}-[a-z]{4}$ ]]; then
    echo "  ✅ App-Specific Password format is VALID"
    echo "     Format: xxxx-xxxx-xxxx-xxxx (correct)"
else
    echo "  ⚠️  App-Specific Password format might be INVALID"
    echo "     Expected: xxxx-xxxx-xxxx-xxxx (19 chars, lowercase with hyphens)"
    echo "     Current length: ${#APPLE_APP_PASSWORD}"
    echo "     Note: Some passwords may have different formats"
fi
echo ""

# Test 4: CSC_KEY_PASSWORD
echo "Test 4: Checking CSC_KEY_PASSWORD..."
if [ -n "$CSC_KEY_PASSWORD" ]; then
    echo "  ✅ CSC_KEY_PASSWORD is set"
    echo "     Length: ${#CSC_KEY_PASSWORD} characters"
else
    echo "  ❌ CSC_KEY_PASSWORD is EMPTY"
    echo "     This should be the password for your .p12 certificate"
    all_valid=false
fi
echo ""

# Test 5: CSC_LINK (Base64 Certificate)
echo "Test 5: Validating CSC_LINK (Base64 Certificate)..."
if [ -n "$CSC_LINK" ]; then
    # Check if it looks like base64
    if echo "$CSC_LINK" | grep -qE '^[A-Za-z0-9+/=]+$'; then
        echo "  ✅ CSC_LINK appears to be valid Base64"
        echo "     Length: ${#CSC_LINK} characters"
        
        # Try to get decoded size (if base64 command is available)
        if command -v base64 &> /dev/null; then
            decoded_size=$(echo "$CSC_LINK" | base64 -d 2>/dev/null | wc -c)
            if [ $? -eq 0 ] && [ "$decoded_size" -gt 100 ]; then
                echo "  ✅ Decoded size looks reasonable: $decoded_size bytes"
            else
                echo "  ⚠️  Could not decode or size is suspicious"
            fi
        fi
    else
        echo "  ❌ CSC_LINK does NOT look like valid Base64"
        all_valid=false
    fi
else
    echo "  ⚠️  CSC_LINK is EMPTY (skipping validation)"
    echo "     If you have the value, paste it in the script to test"
fi
echo ""

# Test 6: Cross-Reference Information
echo "Test 6: Additional Checks..."
domain=$(echo "$APPLE_ID" | cut -d'@' -f2)
echo "  • Apple ID domain: $domain"
echo "  • Remember: Your Team ID must match the certificate"
echo "    Get it from: https://developer.apple.com/account"
echo ""

# Test 7: GitHub Secrets Checklist
echo "Test 7: GitHub Secrets Checklist..."
echo "  Verify these secrets are set in GitHub:"
echo "  └─ Settings → Secrets and variables → Actions"
echo ""
echo "  [ ] CSC_LINK - Base64 of .p12 certificate"
echo "  [ ] CSC_KEY_PASSWORD - Password for .p12 file"
echo "  [ ] APPLE_ID - $APPLE_ID"
echo "  [ ] APPLE_APP_PASSWORD - (19 chars)"
echo "  [ ] APPLE_TEAM_ID - $APPLE_TEAM_ID"
echo ""

# Summary
echo "========================================"
echo "SUMMARY"
echo "========================================"
echo ""

if [ "$all_valid" = true ]; then
    echo "✅ All testable validations PASSED!"
    echo ""
    echo "Next Steps:"
    echo "  1. Copy these exact values to GitHub Secrets"
    echo "  2. Make sure no extra spaces or newlines are added"
    echo "  3. Push to GitHub to trigger the build"
    echo "  4. Watch the 'Verify macOS Signing Secrets' step for validation"
else
    echo "❌ Some validations FAILED!"
    echo ""
    echo "Please fix the issues above before updating GitHub Secrets."
fi

echo ""
echo "⚠️  Important Reminders:"
echo "  • App-Specific Password must be generated at appleid.apple.com"
echo "  • Team ID must match your Developer ID certificate"
echo "  • All secrets must match EXACTLY (case-sensitive)"
echo "  • The real test happens when GitHub Actions runs on macOS"
echo ""

