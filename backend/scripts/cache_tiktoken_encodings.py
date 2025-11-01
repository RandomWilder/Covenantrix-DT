#!/usr/bin/env python3
"""
Pre-cache tiktoken encodings for offline operation
Prevents SSL certificate verification failures in corporate environments
"""
import os
import sys
from pathlib import Path

def cache_tiktoken_encodings():
    """Download and cache all required tiktoken encodings"""
    try:
        import tiktoken
    except ImportError:
        print("ERROR: tiktoken not installed. Install with: pip install tiktoken")
        sys.exit(1)
    
    # Models and encodings to cache
    encodings_to_cache = [
        "o200k_base",      # Used by gpt-4o, gpt-4o-mini
        "cl100k_base",     # Used by gpt-4, gpt-3.5-turbo, text-embedding-3-large
    ]
    
    models_to_cache = [
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4o-2024-08-06",
        "text-embedding-3-large",
    ]
    
    print("=" * 60)
    print("tiktoken Encoding Cache Generator")
    print("=" * 60)
    
    cache_dir = None
    cached_count = 0
    failed_encodings = []
    
    # Cache by encoding name
    print("\n[1/2] Caching encodings by name...")
    for encoding_name in encodings_to_cache:
        try:
            print(f"  - Caching encoding: {encoding_name}...", end=" ", flush=True)
            encoding = tiktoken.get_encoding(encoding_name)
            
            # Get cache directory from the encoding object
            if cache_dir is None:
                # Access the internal cache directory
                import tiktoken.registry
                cache_dir = os.path.join(os.path.expanduser("~"), ".cache", "tiktoken")
                if hasattr(encoding, '_tiktoken_cache_dir'):
                    cache_dir = encoding._tiktoken_cache_dir
            
            cached_count += 1
            print("OK")
        except Exception as e:
            print(f"FAILED ({e})")
            failed_encodings.append((encoding_name, str(e)))
    
    # Cache by model name
    print("\n[2/2] Caching encodings by model name...")
    for model_name in models_to_cache:
        try:
            print(f"  - Caching model: {model_name}...", end=" ", flush=True)
            encoding = tiktoken.encoding_for_model(model_name)
            cached_count += 1
            print("OK")
        except Exception as e:
            print(f"FAILED ({e})")
            failed_encodings.append((model_name, str(e)))
    
    # Detect actual cache directory
    if cache_dir is None:
        # Fallback to default tiktoken cache location
        cache_dir = os.path.join(os.path.expanduser("~"), ".cache", "tiktoken")
    
    print("\n" + "=" * 60)
    print("Cache Summary")
    print("=" * 60)
    print(f"Successfully cached: {cached_count} encodings")
    print(f"Failed: {len(failed_encodings)} encodings")
    
    if failed_encodings:
        print("\nFailed encodings:")
        for name, error in failed_encodings:
            print(f"  - {name}: {error}")
    
    # Check if cache directory exists and has files
    if os.path.exists(cache_dir):
        cache_files = []
        for root, dirs, files in os.walk(cache_dir):
            for file in files:
                if file.endswith('.tiktoken'):
                    cache_files.append(os.path.join(root, file))
        
        print(f"\nCache directory: {cache_dir}")
        print(f"Cached files: {len(cache_files)}")
        
        if cache_files:
            print("\nCached encoding files:")
            for file_path in cache_files:
                file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
                rel_path = os.path.relpath(file_path, cache_dir)
                print(f"  - {rel_path} ({file_size:.2f} MB)")
        
        # Output cache directory for build script to parse
        print(f"\nTIKTOKEN_CACHE_DIR={cache_dir}")
        
        return 0 if not failed_encodings else 1
    else:
        print(f"\nERROR: Cache directory not found: {cache_dir}")
        return 1

if __name__ == "__main__":
    sys.exit(cache_tiktoken_encodings())

