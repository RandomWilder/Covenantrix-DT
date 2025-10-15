#!/usr/bin/env python3
"""
Script to list available OpenAI models via API
"""
import asyncio
import sys
from openai import AsyncOpenAI
import os

async def list_openai_models():
    """List all available OpenAI models, with focus on GPT chat models"""
    
    # Try to get API key from environment or config
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        # Try to load from backend config
        try:
            sys.path.insert(0, 'backend')
            from core.config import get_settings
            settings = get_settings()
            api_key = settings.openai_api_key or settings.openai.api_key
        except:
            pass
    
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found in environment or config")
        print("Please set OPENAI_API_KEY environment variable or ensure backend/.env is configured")
        return
    
    print(f"🔑 Using API key: {api_key[:15]}..." if len(api_key) >= 15 else f"🔑 Using API key: {api_key[:10]}...")
    print("=" * 80)
    print()
    
    try:
        client = AsyncOpenAI(api_key=api_key)
        
        print("📡 Fetching models from OpenAI API...")
        models_response = await client.models.list()
        
        # Extract model IDs
        all_models = [model.id for model in models_response.data]
        
        # Filter GPT chat models (for text generation)
        gpt_models = [m for m in all_models if 'gpt' in m.lower()]
        gpt_models.sort()
        
        # Filter embedding models
        embedding_models = [m for m in all_models if 'embedding' in m.lower()]
        embedding_models.sort()
        
        # Other models
        other_models = [m for m in all_models if m not in gpt_models and m not in embedding_models]
        other_models.sort()
        
        print()
        print("=" * 80)
        print("🤖 GPT CHAT MODELS (for RAG generation)")
        print("=" * 80)
        if gpt_models:
            for i, model in enumerate(gpt_models, 1):
                # Highlight main production models
                if model in ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-4', 'gpt-3.5-turbo']:
                    print(f"  {i:2}. ⭐ {model}")
                else:
                    print(f"  {i:2}.    {model}")
        else:
            print("  None found")
        
        print()
        print("=" * 80)
        print("📊 EMBEDDING MODELS")
        print("=" * 80)
        if embedding_models:
            for i, model in enumerate(embedding_models, 1):
                print(f"  {i:2}. {model}")
        else:
            print("  None found")
        
        print()
        print("=" * 80)
        print("🔧 OTHER MODELS (TTS, Whisper, etc.)")
        print("=" * 80)
        if other_models:
            for i, model in enumerate(other_models, 1):
                print(f"  {i:2}. {model}")
        else:
            print("  None found")
        
        print()
        print("=" * 80)
        print(f"📋 SUMMARY: {len(all_models)} total models found")
        print(f"   - GPT Chat: {len(gpt_models)}")
        print(f"   - Embeddings: {len(embedding_models)}")
        print(f"   - Other: {len(other_models)}")
        print("=" * 80)
        
        # Suggest models for RAG enum
        print()
        print("💡 SUGGESTED MODELS FOR RAG CONFIGURATION:")
        print("=" * 80)
        suggested = [m for m in gpt_models if any(x in m for x in ['gpt-5', 'gpt-4o', 'gpt-4-turbo', 'gpt-4', 'gpt-3.5-turbo']) 
                     and not any(x in m for x in ['vision', 'instruct', 'realtime'])]
        
        if suggested:
            print("class LLMModel(str, Enum):")
            print('    """Available OpenAI models"""')
            for model in suggested[:10]:  # Limit to top 10
                enum_name = model.upper().replace('-', '_').replace('.', '_')
                print(f'    {enum_name} = "{model}"')
        else:
            print("  No suitable models found for RAG")
        
        print()
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(list_openai_models())

