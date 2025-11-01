"""Generate JWT test token for subscription testing"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from domain.subscription.license_validator import LicenseValidator
from domain.subscription.tier_config import TIER_LIMITS
from datetime import datetime, timedelta


def print_header():
    """Print welcome header"""
    print("\n" + "=" * 70)
    print("JWT TEST TOKEN GENERATOR")
    print("=" * 70 + "\n")


def print_tier_info():
    """Display available tiers and their features"""
    print("Available Subscription Tiers:")
    print("-" * 70)
    
    tier_descriptions = {
        "trial": "Trial - Unlimited queries, 3 docs, 7 days, default API keys",
        "free": "Free - 50 queries/month, 20/day, 3 docs, custom API keys only",
        "paid": "Paid - Unlimited everything, default API keys included",
        "paid_limited": "Paid Limited - Grace period (7 days), limited access"
    }
    
    for idx, (tier, description) in enumerate(tier_descriptions.items(), 1):
        print(f"{idx}. {tier.upper():<15} - {description}")
    
    print("-" * 70)


def get_tier_choice():
    """Prompt user to select a tier"""
    tier_map = {
        "1": "trial",
        "2": "free",
        "3": "paid",
        "4": "paid_limited"
    }
    
    while True:
        choice = input("\nSelect tier (1-4) or enter tier name: ").strip().lower()
        
        # Check if it's a number selection
        if choice in tier_map:
            return tier_map[choice]
        
        # Check if it's a direct tier name
        if choice in ["trial", "free", "paid", "paid_limited"]:
            return choice
        
        print("❌ Invalid selection. Please enter 1-4 or a valid tier name.")


def get_duration():
    """Prompt user for token duration in days"""
    while True:
        try:
            duration = input("\nEnter duration in days (e.g., 7, 30, 365): ").strip()
            days = int(duration)
            
            if days < 1:
                print("❌ Duration must be at least 1 day.")
                continue
            
            if days > 3650:  # 10 years max
                print("❌ Duration cannot exceed 3650 days (10 years).")
                continue
            
            return days
        except ValueError:
            print("❌ Please enter a valid number.")


def confirm_generation(tier, days):
    """Ask user to confirm token generation"""
    print("\n" + "=" * 70)
    print("TOKEN CONFIGURATION SUMMARY")
    print("=" * 70)
    print(f"Tier:         {tier.upper()}")
    print(f"Duration:     {days} days")
    print(f"Expires:      {(datetime.utcnow() + timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 70)
    
    while True:
        confirm = input("\nGenerate token with these settings? (y/n): ").strip().lower()
        if confirm in ['y', 'yes']:
            return True
        elif confirm in ['n', 'no']:
            return False
        else:
            print("❌ Please enter 'y' or 'n'.")


def display_token(tier, days, token):
    """Display the generated token"""
    print("\n" + "=" * 70)
    print("✅ JWT TEST TOKEN GENERATED SUCCESSFULLY!")
    print("=" * 70)
    print(f"Tier:         {tier.upper()}")
    print(f"Duration:     {days} days")
    print(f"Expires:      {(datetime.utcnow() + timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 70)
    print("\nYour Token:")
    print("-" * 70)
    print(token)
    print("-" * 70)
    print("\n📋 To activate:")
    print("   1. Copy the token above")
    print("   2. Open your app's Settings > Subscription")
    print("   3. Paste it in the 'Enter License Key' field")
    print("=" * 70 + "\n")


def main():
    """Main interactive flow"""
    print_header()
    print_tier_info()
    
    # Get user choices
    tier = get_tier_choice()
    days = get_duration()
    
    # Confirm before generating
    if not confirm_generation(tier, days):
        print("\n❌ Token generation cancelled.\n")
        return
    
    # Generate token
    print("\n🔄 Generating token...")
    validator = LicenseValidator()
    token = validator.generate_test_token(tier=tier, duration_days=days)
    
    # Display result
    display_token(tier, days, token)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Operation cancelled by user.\n")
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        sys.exit(1)

