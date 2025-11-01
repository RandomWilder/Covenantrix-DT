#!/usr/bin/env python3
"""
One-time script to generate tiktoken cache for committing to repository.
Run this manually when you need to update the bundled cache.

Usage:
    python backend/scripts/generate_tiktoken_cache.py
    
This creates backend/tiktoken_cache/ with the encoding files.
Commit these files to the repository.
"""
import os
import sys
from pathlib import Path

def generate_cache():
    """Generate tiktoken cache in backend/tiktoken_cache/"""
    
    # Set cache directory to backend/tiktoken_cache/
    script_dir = Path(__file__).parent.resolve()
    cache_dir = script_dir.parent / "tiktoken_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    # Set environment variable BEFORE importing tiktoken
    os.environ['TIKTOKEN_CACHE_DIR'] = str(cache_dir)
    
    print("=" * 70)
    print("tiktoken Cache Generator (for repository commit)")
    print("=" * 70)
    print(f"\nCache directory: {cache_dir}")
    print(f"This will generate cache files to commit to the repository.\n")
    
    try:
        import tiktoken
    except ImportError:
        print("ERROR: tiktoken not installed.")
        print("Install with: pip install tiktoken")
        sys.exit(1)
    
    # Encodings to cache
    encodings = ["o200k_base", "cl100k_base"]
    models = ["gpt-4o", "gpt-4o-mini", "gpt-4o-2024-08-06", "text-embedding-3-large"]
    
    cached = 0
    failed = []
    
    print("Caching encodings...")
    for enc in encodings:
        try:
            print(f"  - {enc}...", end=" ", flush=True)
            tiktoken.get_encoding(enc)
            cached += 1
            print("OK")
        except Exception as e:
            print(f"FAILED: {e}")
            failed.append((enc, str(e)))
    
    print("\nCaching model encodings...")
    for model in models:
        try:
            print(f"  - {model}...", end=" ", flush=True)
            tiktoken.encoding_for_model(model)
            cached += 1
            print("OK")
        except Exception as e:
            print(f"FAILED: {e}")
            failed.append((model, str(e)))
    
    # Verify files were created
    cache_files = []
    if cache_dir.exists():
        for root, dirs, files in os.walk(cache_dir):
            for f in files:
                if f.endswith('.tiktoken'):
                    cache_files.append(Path(root) / f)
    
    print("\n" + "=" * 70)
    print("Results")
    print("=" * 70)
    print(f"Operations completed: {cached}")
    print(f"Failed: {len(failed)}")
    print(f"Cache files found: {len(cache_files)}")
    
    if cache_files:
        print(f"\nGenerated files (in {cache_dir}):")
        total_size = 0
        for f in cache_files:
            size_mb = f.stat().st_size / (1024 * 1024)
            total_size += size_mb
            rel_path = f.relative_to(cache_dir)
            print(f"  - {rel_path} ({size_mb:.2f} MB)")
        print(f"\nTotal size: {total_size:.2f} MB")
        
        print("\n" + "=" * 70)
        print("SUCCESS!")
        print("=" * 70)
        print("\nNext steps:")
        print("1. Review the files in backend/tiktoken_cache/")
        print("2. Commit them to the repository:")
        print("   git add backend/tiktoken_cache/")
        print("   git commit -m 'chore: Add pre-cached tiktoken encodings'")
        print("\nThe build process will use these pre-cached files.")
        return 0
    else:
        print("\n" + "=" * 70)
        print("ERROR: No cache files generated")
        print("=" * 70)
        print("\nPossible issues:")
        print("- tiktoken may not respect TIKTOKEN_CACHE_DIR on your system")
        print("- Network issues prevented downloading")
        print("- Permission issues writing to directory")
        return 1

if __name__ == "__main__":
    sys.exit(generate_cache())

