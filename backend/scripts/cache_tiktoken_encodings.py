#!/usr/bin/env python3
"""
Pre-cache tiktoken encodings for offline operation
Prevents SSL certificate verification failures in corporate environments
"""
import os
import sys
from pathlib import Path

def get_tiktoken_cache_dir():
    """Get the actual tiktoken cache directory"""
    import platform
    
    # Platform-specific default cache locations
    if platform.system() == "Windows":
        # Windows: AppData\Local\tiktoken_cache
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            return os.path.join(local_app_data, "tiktoken_cache")
        # Fallback
        return os.path.join(os.path.expanduser("~"), "AppData", "Local", "tiktoken_cache")
    else:
        # Unix/macOS: ~/.cache/tiktoken
        return os.path.join(os.path.expanduser("~"), ".cache", "tiktoken")

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
    first_encoding = None
    
    # Cache by encoding name
    print("\n[1/2] Caching encodings by name...")
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
    
    # Detect actual cache directory by searching for cached files
    print("\n" + "=" * 60)
    print("Detecting Cache Location")
    print("=" * 60)
    
    # Try to get cache directory from environment variable (if set by tiktoken)
    cache_dir = os.environ.get("TIKTOKEN_CACHE_DIR")
    
    if not cache_dir:
        # Try platform-specific default location
        cache_dir = get_tiktoken_cache_dir()
        print(f"Trying default location: {cache_dir}")
    
    # If default doesn't exist, search for tiktoken cache files
    if not os.path.exists(cache_dir):
        print(f"Default location not found, searching...")
        
        # Search common locations
        search_paths = []
        home = os.path.expanduser("~")
        
        if os.name == 'nt':  # Windows
            search_paths = [
                os.path.join(os.environ.get("LOCALAPPDATA", ""), "tiktoken_cache"),
                os.path.join(os.environ.get("APPDATA", ""), "tiktoken_cache"),
                os.path.join(home, "AppData", "Local", "tiktoken_cache"),
                os.path.join(home, ".tiktoken_cache"),
            ]
        else:  # Unix/macOS
            search_paths = [
                os.path.join(home, ".cache", "tiktoken"),
                os.path.join(home, ".tiktoken_cache"),
                os.path.join("/tmp", "tiktoken_cache"),
            ]
        
        for search_path in search_paths:
            if os.path.exists(search_path):
                # Check if it contains .tiktoken files
                for root, dirs, files in os.walk(search_path):
                    if any(f.endswith('.tiktoken') for f in files):
                        cache_dir = search_path
                        print(f"Found cache at: {cache_dir}")
                        break
                if os.path.exists(cache_dir) and cache_dir != search_path:
                    break
    
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
    if cache_dir and os.path.exists(cache_dir):
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
        # Encodings were cached successfully but we couldn't locate the directory
        # This is OK - tiktoken will find them at runtime
        print(f"\nWARNING: Could not locate cache directory")
        print(f"Searched: {cache_dir if cache_dir else 'unknown'}")
        print(f"\nEncodings were cached successfully by tiktoken.")
        print(f"tiktoken will find them automatically at runtime.")
        print(f"\nNote: The build script will use tiktoken's default cache location.")
        
        # Return success since caching operations succeeded
        return 0 if not failed_encodings else 1

if __name__ == "__main__":
    sys.exit(cache_tiktoken_encodings())

