# Covenantrix Subscription Model

## Tier Structure

```
TRIAL (7 days) → FREE (forever) → PAID (subscription) ⇄ PAID LIMITED (7-day grace)
```

---

## Tier Definitions

### **TRIAL** (Free Trial)
**Duration:** 7 days from first launch
**Purpose:** Full product experience to hook new users

**Limits:**
- Documents: 3 max
- Storage: 10MB per doc, 30MB total
- Queries: Unlimited
- API Keys: Default keys (your keys)

**Trigger:** First application launch
**Auto-downgrade:** To FREE after 7 days

---

### **FREE** (Freemium)
**Duration:** Indefinite
**Purpose:** Maintain user engagement, require own API keys

**Limits:**
- Documents: 3 max
- Storage: 10MB per doc, 30MB total
- Queries: 50 per month + 20 per day
- API Keys: Must use own keys (default blocked)

**Entry Points:**
- TRIAL expiration (7 days)
- PAID LIMITED expiration (7 days)

---

### **PAID** (Premium Subscription)
**Duration:** Active subscription
**Purpose:** Full unlimited access

**Limits:**
- Documents: Unlimited
- Storage: 100MB per doc, unlimited total
- Queries: Unlimited
- API Keys: Default keys available

**Pricing:**
- Full price: Default keys enabled
- 50% discount: If using own keys

**Entry Point:** License activation (payment)

---

### **PAID LIMITED** (Grace Period)
**Duration:** 7 days
**Purpose:** Grace period for payment issues

**Limits:**
- Documents: First 3 uploaded only (hide rest)
- Storage: Same as FREE
- Queries: Same as FREE (50/month + 20/day)
- API Keys: Default blocked

**Behavior:**
- Show subscription expiry notification
- Prompt for payment resolution
- Countdown visible in UI

**Entry Point:** 
- Subscription cancelled by user
- Payment failure from provider

**Exit:**
- To PAID: Payment resolved
- To FREE: After 7 days → hard delete hidden docs

---

## Transition Rules

### Trial → FREE (Auto)
- Trigger: 7 days elapsed since first launch
- Action: Block default keys, apply query limits
- Notification: "Trial ended, upgrade or use own keys"

### FREE → PAID (Manual)
- Trigger: User activates license key
- Action: Unlock all limits, enable default keys
- Notification: "Welcome to Premium!"

### PAID → PAID LIMITED (Auto)
- Trigger: Payment failure OR user cancellation
- Action: 
  - Hide all docs except first 3
  - Apply FREE query limits
  - Block default keys
  - Start 7-day countdown
- Notification: "Payment issue - 7 days to resolve"

### PAID LIMITED → PAID (Manual)
- Trigger: Payment resolved
- Action: Restore all hidden docs, unlock limits
- Notification: "Subscription restored!"

### PAID LIMITED → FREE (Auto)
- Trigger: 7 days elapsed without payment
- Action: 
  - Hard delete hidden docs (keep first 3)
  - Apply FREE tier permanently
- Notification: "Downgraded to Free tier"

---

## Implementation Notes

### Query Limit Reset
- **Monthly:** Rolling 30-day window from first query
- **Daily:** 24-hour rolling window OR midnight UTC

### Document Handling on Downgrade
- **Soft Delete:** PAID → PAID LIMITED (hide, keep 7 days)
- **Hard Delete:** PAID LIMITED → FREE (delete after 7 days)
- **Keep:** First 3 uploaded docs (psychological retention)

### Trial Activation
- **Trigger:** First application launch (not installation)
- **Storage:** Timestamp in user_settings.json
- **Check:** On every app startup

### Per-Document Limits
- **FREE/TRIAL:** 10MB per doc
- **PAID:** 100MB per doc
- **System Safe Limit:** 100MB (configurable)

---

## Payment Integration (Future)

### License Activation Flow
1. User purchases subscription (external provider)
2. Receives license key via email
3. Enters key in app
4. App validates key → upgrades to PAID

### Payment Provider Integration
- **NOT a blocker** for initial development
- Can be added later (Stripe/Gumroad/Paddle)
- Mock license validation for testing

---

## Scalability Considerations

### Easy to Modify
- All limits in single config file
- Tier structure supports unlimited tiers
- Query/doc limits easily adjustable

### Future Tiers (Examples)
- **TEAM:** Multi-user, shared storage
- **ENTERPRISE:** Custom limits, dedicated support
- **LIFETIME:** One-time payment, permanent PAID

---

## Key Psychological Hooks

1. **TRIAL:** Full experience with default keys → show value
2. **FREE → PAID:** Friction from key management + query limits
3. **PAID LIMITED:** Keep first 3 docs → emotional attachment
4. **Grace Period:** 7 days to prevent churn from payment issues