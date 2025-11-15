"""
Simple test script to verify system prompt implementation
Run from backend directory: python test_prompts.py
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from domain.chat.prompts import SystemPrompts


def test_system_prompts():
    """Test all system prompt variations"""
    print("=" * 80)
    print("SYSTEM PROMPTS TEST")
    print("=" * 80)
    print()
    
    # Test 1: Document Query Context
    print("1. DOCUMENT QUERY CONTEXT")
    print("-" * 80)
    doc_prompt = SystemPrompts.get_system_prompt(
        context_type="document_query",
        language_instruction="Respond in the same language as the user's query."
    )
    print(doc_prompt)
    print()
    
    # Test 2: General Query Context
    print("2. GENERAL QUERY CONTEXT")
    print("-" * 80)
    general_prompt = SystemPrompts.get_system_prompt(
        context_type="general_query",
        language_instruction="Respond in the same language as the user's query."
    )
    print(general_prompt)
    print()
    
    # Test 3: No Info Found Context
    print("3. NO INFO FOUND CONTEXT")
    print("-" * 80)
    no_info_prompt = SystemPrompts.get_system_prompt(
        context_type="no_info_found",
        language_instruction="Respond in the same language as the user's query."
    )
    print(no_info_prompt)
    print()
    
    # Test 4: Streaming Prompt (should be same)
    print("4. STREAMING PROMPT (Document Query)")
    print("-" * 80)
    streaming_prompt = SystemPrompts.get_streaming_prompt(
        context_type="document_query",
        language_instruction="Respond in the same language as the user's query."
    )
    print(streaming_prompt)
    print()
    
    # Verify all prompts contain base personality
    print("5. VERIFICATION")
    print("-" * 80)
    
    checks = [
        ("Document prompt contains base personality", "legal counsel" in doc_prompt.lower()),
        ("General prompt contains base personality", "legal counsel" in general_prompt.lower()),
        ("No info prompt contains base personality", "legal counsel" in no_info_prompt.lower()),
        ("Document prompt mentions documents", "documents" in doc_prompt.lower()),
        ("General prompt mentions general advice", "general" in general_prompt.lower()),
        ("No info prompt mentions searching", "searched" in no_info_prompt.lower()),
        ("All prompts have language instruction", all(
            "same language" in p.lower() 
            for p in [doc_prompt, general_prompt, no_info_prompt]
        )),
    ]
    
    for check_name, result in checks:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {check_name}")
    
    print()
    print("=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    test_system_prompts()

