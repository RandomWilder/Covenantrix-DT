#!/usr/bin/env python3
"""
Pre-cache tiktoken encodings for offline operation
Prevents SSL certificate verification failures in corporate environments
"""
import os
import sys
from pathlib import Path

# CRITICAL: Set cache directory BEFORE importing tiktoken
# This ensures we know exactly where the cache will be stored
def setup_cache_directory():
    """Create and configure dedicated tiktoken cache directory"""
    import platform
    
    # Determine platform-specific cache location
    if platform.system() == "Windows":
        # Windows: Use script's parent directory for predictable location
        script_dir = Path(__file__).parent.parent.parent.resolve()
        cache_dir = script_dir / "dist" / "tiktoken-cache-temp"
    else:
        # Unix/macOS: Use script's parent directory
        script_dir = Path(__file__).parent.parent.parent.resolve()
        cache_dir = script_dir / "dist" / "tiktoken-cache-temp"
    
    # Create cache directory
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    # Set environment variable so tiktoken uses this location
    os.environ['TIKTOKEN_CACHE_DIR'] = str(cache_dir)
    
    return str(cache_dir)

# Set up cache directory BEFORE any tiktoken imports
CACHE_DIR = setup_cache_directory()
print(f"Pre-configured cache directory: {CACHE_DIR}")
print(f"TIKTOKEN_CACHE_DIR environment variable set\n")

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
    
    cache_dir = CACHE_DIR  # Use pre-configured directory
    cached_count = 0
    failed_encodings = []
    
    # Cache by encoding name
    print("[1/2] Caching encodings by name...")
    for encoding_name in encodings_to_cache:
        try:
            print(f"  - Caching encoding: {encoding_name}...", end=" ", flush=True)
            encoding = tiktoken.get_encoding(encoding_name)
            
            # Store first encoding to detect cache directory later
            if first_encoding is None:
                first_encoding = encoding
            
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
    
    # Cache directory was pre-configured, verify it was used
    print("\n" + "=" * 60)
    print("Cache Summary")
    print("=" * 60)
    print(f"Successfully cached: {cached_count} encodings")
    print(f"Failed: {len(failed_encodings)} encodings")
    
    if failed_encodings:
        print("\nFailed encodings:")
        for name, error in failed_encodings:
            print(f"  - {name}: {error}")
    
    # Verify cache directory has files
    cache_files = []
    if os.path.exists(cache_dir):
        for root, dirs, files in os.walk(cache_dir):
            for file in files:
                if file.endswith('.tiktoken'):
                    cache_files.append(os.path.join(root, file))
    
    print(f"\nCache directory: {cache_dir}")
    print(f"Directory exists: {os.path.exists(cache_dir)}")
    print(f"Cached files found: {len(cache_files)}")
    
    if cache_files:
        print("\nCached encoding files:")
        total_size = 0
        for file_path in cache_files:
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
            total_size += file_size
            rel_path = os.path.relpath(file_path, cache_dir)
            print(f"  - {rel_path} ({file_size:.2f} MB)")
        print(f"\nTotal cache size: {total_size:.2f} MB")
    
    # Output cache directory for build script to parse
    print(f"\nTIKTOKEN_CACHE_DIR={cache_dir}")
    
    # Verify success
    if cache_files:
        print("\n" + "=" * 60)
        print("SUCCESS: Cache generated and verified")
        print("=" * 60)
        return 0 if not failed_encodings else 1
    else:
        print("\n" + "=" * 60)
        print("ERROR: No cache files found after caching")
        print("=" * 60)
        print("Encodings appeared to cache successfully but files not found.")
        print("This may indicate a tiktoken configuration issue.")
        return 1

if __name__ == "__main__":
    sys.exit(cache_tiktoken_encodings())

