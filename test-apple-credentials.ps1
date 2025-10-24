# Apple Credentials Validation Script for Windows
# Edit the variables below with your actual credentials and run: .\test-apple-credentials.ps1

# YOUR CREDENTIALS - EDIT THESE
$APPLE_ID = "rasdedi@gmail.com"
$APPLE_APP_PASSWORD = "ueop-tots-hjqv-munc"
$APPLE_TEAM_ID = "2FN24V2Y82"
$CSC_KEY_PASSWORD = "yoStrongFrom1983"
$CSC_LINK = "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"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Apple Credentials Validation (Windows)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$allValid = $true

# Test 1: Apple ID Format
Write-Host "Test 1: Validating Apple ID format..." -ForegroundColor Yellow
if ($APPLE_ID -match "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$") {
    Write-Host "  ✅ Apple ID format is VALID" -ForegroundColor Green
    Write-Host "     Value: $APPLE_ID" -ForegroundColor Gray
} else {
    Write-Host "  ❌ Apple ID format is INVALID" -ForegroundColor Red
    Write-Host "     Expected: email@example.com" -ForegroundColor Gray
    Write-Host "     Current: $APPLE_ID" -ForegroundColor Gray
    $allValid = $false
}
Write-Host ""

# Test 2: Team ID Format
Write-Host "Test 2: Validating Apple Team ID format..." -ForegroundColor Yellow
if ($APPLE_TEAM_ID -match "^[A-Z0-9]{10}$") {
    Write-Host "  ✅ Team ID format is VALID" -ForegroundColor Green
    Write-Host "     Value: $APPLE_TEAM_ID" -ForegroundColor Gray
} else {
    Write-Host "  ❌ Team ID format is INVALID" -ForegroundColor Red
    Write-Host "     Expected: 10 uppercase alphanumeric characters" -ForegroundColor Gray
    Write-Host "     Current: $APPLE_TEAM_ID (length: $($APPLE_TEAM_ID.Length))" -ForegroundColor Gray
    $allValid = $false
}
Write-Host ""

# Test 3: App-Specific Password Format
Write-Host "Test 3: Validating App-Specific Password format..." -ForegroundColor Yellow
if ($APPLE_APP_PASSWORD -match "^[a-z]{4}-[a-z]{4}-[a-z]{4}-[a-z]{4}$") {
    Write-Host "  ✅ App-Specific Password format is VALID" -ForegroundColor Green
    Write-Host "     Format: xxxx-xxxx-xxxx-xxxx (correct)" -ForegroundColor Gray
} else {
    Write-Host "  ⚠️  App-Specific Password format might be INVALID" -ForegroundColor Yellow
    Write-Host "     Expected: xxxx-xxxx-xxxx-xxxx (19 chars, lowercase with hyphens)" -ForegroundColor Gray
    Write-Host "     Current length: $($APPLE_APP_PASSWORD.Length)" -ForegroundColor Gray
    Write-Host "     Note: Some passwords may have different formats" -ForegroundColor Gray
}
Write-Host ""

# Test 4: CSC_KEY_PASSWORD
Write-Host "Test 4: Checking CSC_KEY_PASSWORD..." -ForegroundColor Yellow
if ($CSC_KEY_PASSWORD -and $CSC_KEY_PASSWORD.Length -gt 0) {
    Write-Host "  ✅ CSC_KEY_PASSWORD is set" -ForegroundColor Green
    Write-Host "     Length: $($CSC_KEY_PASSWORD.Length) characters" -ForegroundColor Gray
} else {
    Write-Host "  ❌ CSC_KEY_PASSWORD is EMPTY" -ForegroundColor Red
    Write-Host "     This should be the password for your .p12 certificate" -ForegroundColor Gray
    $allValid = $false
}
Write-Host ""

# Test 5: CSC_LINK (Base64 Certificate)
Write-Host "Test 5: Validating CSC_LINK (Base64 Certificate)..." -ForegroundColor Yellow
if ($CSC_LINK -and $CSC_LINK.Length -gt 0) {
    try {
        $null = [Convert]::FromBase64String($CSC_LINK.Trim())
        Write-Host "  ✅ CSC_LINK appears to be valid Base64" -ForegroundColor Green
        Write-Host "     Length: $($CSC_LINK.Length) characters" -ForegroundColor Gray
        
        $bytes = [Convert]::FromBase64String($CSC_LINK.Trim())
        if ($bytes.Length -gt 100) {
            Write-Host "  ✅ Decoded size looks reasonable: $($bytes.Length) bytes" -ForegroundColor Green
        } else {
            Write-Host "  ⚠️  Decoded size is very small: $($bytes.Length) bytes" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  ❌ CSC_LINK is NOT valid Base64" -ForegroundColor Red
        Write-Host "     Error: $($_.Exception.Message)" -ForegroundColor Gray
        $allValid = $false
    }
} else {
    Write-Host "  ⚠️  CSC_LINK is EMPTY (skipping validation)" -ForegroundColor Yellow
    Write-Host "     If you have the value, paste it in the script to test" -ForegroundColor Gray
}
Write-Host ""

# Test 6: Cross-Reference Information
Write-Host "Test 6: Additional Checks..." -ForegroundColor Yellow
$domain = $APPLE_ID.Split("@")[1]
Write-Host "  • Apple ID domain: $domain" -ForegroundColor Gray
Write-Host "  • Remember: Your Team ID must match the certificate" -ForegroundColor Gray
Write-Host "    Get it from: https://developer.apple.com/account" -ForegroundColor Gray
Write-Host ""

# Test 7: GitHub Secrets Checklist
Write-Host "Test 7: GitHub Secrets Checklist..." -ForegroundColor Yellow
Write-Host "  Verify these secrets are set in GitHub:" -ForegroundColor Gray
Write-Host "  Settings -> Secrets and variables -> Actions" -ForegroundColor Gray
Write-Host ""
Write-Host "  CSC_LINK - Base64 of .p12 certificate" -ForegroundColor White
Write-Host "  CSC_KEY_PASSWORD - Password for .p12 file" -ForegroundColor White  
Write-Host "  APPLE_ID - $APPLE_ID" -ForegroundColor White
Write-Host "  APPLE_APP_PASSWORD - 19 chars" -ForegroundColor White
Write-Host "  APPLE_TEAM_ID - $APPLE_TEAM_ID" -ForegroundColor White
Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SUMMARY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if ($allValid) {
    Write-Host "✅ All testable validations PASSED!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Yellow
    Write-Host "  1. Copy these exact values to GitHub Secrets" -ForegroundColor White
    Write-Host "  2. Make sure no extra spaces or newlines are added" -ForegroundColor White
    Write-Host "  3. Push to GitHub to trigger the build" -ForegroundColor White
    Write-Host "  4. Watch the Verify macOS Signing Secrets step for validation" -ForegroundColor White
} else {
    Write-Host "❌ Some validations FAILED!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please fix the issues above before updating GitHub Secrets." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "⚠️  Important Reminders:" -ForegroundColor Yellow
Write-Host "  • App-Specific Password must be generated at appleid.apple.com" -ForegroundColor White
Write-Host "  • Team ID must match your Developer ID certificate" -ForegroundColor White
Write-Host "  • All secrets must match EXACTLY" -ForegroundColor White
Write-Host "  • The real test happens when GitHub Actions runs on macOS" -ForegroundColor White
Write-Host ""
