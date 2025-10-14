# JWT License & Tier Control System

## Core Concept

**License = JWT Token** that encodes subscription data and controls tier access.

**Philosophy:**
- License key is a signed JWT (JSON Web Token)
- Contains tier, expiry, and metadata
- Validated locally (offline-capable)
- No backend required for validation
- Future-proof for payment provider integration

---

## JWT Structure

### Encoded License Key Format
```
eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0aWVyIjoicGFpZCIsImlzc3VlZCI6MTczNDU...
```

### Decoded Payload
```json
{
  "tier": "paid",                    // trial | free | paid | paid_limited
  "issued": 1734567890000,           // Timestamp
  "expiry": 1766103890000,           // Timestamp (null = never expires)
  "license_id": "uuid-v4",           // Unique license identifier
  "features": {
    "max_documents": -1,             // -1 = unlimited
    "max_queries_monthly": -1,
    "max_queries_daily": -1,
    "max_doc_size_mb": 100,
    "use_default_keys": true,
    "discount_rate": 0               // 0.5 = 50% discount
  }
}
```

### Signature
- Signed with **private key** (kept secret by you)
- Validated with **public key** (embedded in app)
- Cannot be forged without private key

---

## Tier Lifecycle with JWT

### **TRIAL Tier (Auto-generated)**
```
App First Launch
    ↓
Generate JWT automatically
    tier: "trial"
    expiry: now + 7 days
    features: { maxDocs: 3, useDefaultKeys: true, ... }
    ↓
Store in user_settings.json
    ↓
Validate on startup
    ↓
After 7 days → Auto-downgrade to FREE
```

### **FREE Tier (Default)**
```
No JWT or expired trial JWT
    ↓
Default tier = FREE
    ↓
Features hardcoded in app:
    { maxDocs: 3, maxQueries: 50/month + 20/day, useDefaultKeys: false }
```

### **PAID Tier (Manual Activation)**
```
User obtains license key
    ↓
Opens app → Profile → Subscription tab
    ↓
Pastes key → Validates JWT
    ↓
Extracts tier + features from JWT
    ↓
Stores in user_settings.json (encrypted)
    ↓
Upgrades to PAID
```

### **PAID LIMITED (Grace Period)**
```
PAID JWT expires OR payment fails
    ↓
Detect expiry on startup
    ↓
Generate PAID_LIMITED JWT:
    tier: "paid_limited"
    expiry: now + 7 days
    features: { maxDocs: 3, useDefaultKeys: false, ... }
    ↓
Show grace period notification
    ↓
After 7 days → Downgrade to FREE
```

---

## Integration Points

### **Backend Changes**

#### New Service: `backend/domain/subscription/license_service.py`
**Responsibilities:**
- Validate JWT signatures
- Check expiry dates
- Extract tier and features
- Handle tier transitions
- Track trial start date

#### New Storage: Extend `backend/api/schemas/settings.py`
```python
class LicenseSettings(BaseModel):
    license_key: Optional[str] = None
    tier: str = "free"  # trial | free | paid | paid_limited
    trial_started_at: Optional[str] = None
    features: FeatureFlags

class UserSettings(BaseModel):
    # ... existing fields ...
    license: LicenseSettings = Field(default_factory=LicenseSettings)
```

#### New Endpoints: `backend/api/routes/subscription.py`
```python
POST   /subscription/activate      # Activate license key
GET    /subscription/status        # Get current tier + limits
GET    /subscription/features      # Get allowed features
POST   /subscription/validate      # Validate JWT (for testing)
```

---

### **Frontend Changes**

#### New Context: `covenantrix-desktop/src/contexts/SubscriptionContext.tsx`
**State:**
```typescript
{
  tier: SubscriptionTier,           // current tier
  license: LicenseSettings | null,  // license data
  features: FeatureFlags,           // current limits
  isLoading: boolean,
  trialDaysRemaining: number | null
}
```

**Methods:**
```typescript
activateLicense(key: string): Promise<void>
checkExpiry(): void
canUseFeature(feature: string): boolean
getRemainingQuota(resource: string): number
```

#### New Components:
```
features/subscription/
├── LicenseActivation.tsx          # Input field for key entry
├── SubscriptionStatus.tsx         # Current tier display
├── TrialBanner.tsx                # 7-day countdown
├── UpgradeModal.tsx               # Limit reached prompts
└── GracePeriodNotification.tsx    # PAID_LIMITED warning
```

#### Feature Gates:
```typescript
// In document upload
const { canUseFeature } = useSubscription();
if (!canUseFeature('upload_document')) {
  showUpgradeModal();
  return;
}

// In chat query
if (!canUseFeature('send_query')) {
  showUpgradeModal();
  return;
}
```

#### Profile Integration:
```
Profile Modal → New Tab: "Subscription"
├── Current tier display
├── License activation input
├── Usage stats (docs/queries used)
├── Trial countdown (if applicable)
└── Tier feature comparison
```

---

## Development Flow (Current Scope)

### **Manual License Generation**

**Admin Tool:** `scripts/generate-license.js`
```javascript
// Generate test licenses
node generate-license.js trial 7
node generate-license.js paid 365
node generate-license.js paid 30 --discount 0.5

// Output: JWT token to paste in app
```

**Developer Testing:**
1. Run admin script → Get JWT
2. Open app → Profile → Subscription tab
3. Paste JWT → Click "Activate"
4. App validates → Upgrades tier
5. Test feature gates

**Automated Testing:**
```typescript
// In tests: inject test JWTs
const testLicense = generateTestJWT('paid', 365);
await subscriptionContext.activateLicense(testLicense);
expect(canUseFeature('upload_document')).toBe(true);
```

---

## Security Considerations

### **Private Key Protection**
- **NEVER** embed in app code
- Store on secure server
- Use for license generation only
- Rotate periodically

### **Public Key Embedding**
- Embedded in app (safe)
- Used for validation only
- Can't be used to forge licenses

### **License Storage**
- Stored encrypted in `user_settings.json`
- Uses existing encryption infrastructure
- Same security as API keys

### **Offline Validation**
- No internet required to validate
- Works completely offline
- Expiry checked on startup

### **Anti-Piracy Measures** (Phase 2)
- Device fingerprinting (limit activations)
- Online validation (periodic check)
- Revocation list (blocked licenses)

---

## Implementation Priority

### **Phase 1: Core Infrastructure** (Week 1)
1. Create JWT validation service (backend)
2. Extend user_settings schema with license fields
3. Add subscription endpoints
4. Build SubscriptionContext (frontend)
5. Implement tier detection logic

### **Phase 2: UI Components** (Week 2)
1. Add Subscription tab to Profile modal
2. License activation screen
3. Trial countdown banner
4. Feature gate implementation
5. Upgrade prompts/notifications

### **Phase 3: Testing & Refinement** (Week 2-3)
1. Admin license generator script
2. Dev mode bypass for testing
3. Automated test suite
4. Manual testing checklist
5. Usage tracking and quota enforcement

---

## Future Enhancements

### **Payment Provider Integration** (Post-MVP)
- Webhook handler for automatic JWT generation
- Email delivery of license keys
- Subscription renewal automation
- Payment failure handling

### **Cloud Validation** (Optional)
- Periodic online license check
- Device limit enforcement
- License revocation list
- Usage analytics

---

## Key Benefits of This Approach

âœ… **No Backend Dependency** - Works offline, validates locally  
âœ… **Future-Proof** - JWT format ready for payment integration when needed  
âœ… **Testable** - Easy to generate test licenses for development  
âœ… **Secure** - Cannot be forged without private key  
âœ… **Flexible** - Easy to add new tiers and features  
âœ… **Standard** - JWT is industry-proven technology  

---

## Future Integration Path

### **When Payment Provider is Added:**
- Current JWT system remains unchanged
- Payment webhooks generate same JWT format
- Zero modifications to app validation logic
- Seamless transition from manual to automated license generation

### **When Cloud Validation is Added:**
- JWT continues to work offline (primary validation)
- Optional online check for additional security
- Device fingerprinting and activation limits
- License revocation capability