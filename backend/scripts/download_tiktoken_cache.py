#!/usr/bin/env python3
"""
Download tiktoken cache files directly from OpenAI's blob storage.
This bypasses tiktoken's caching mechanism entirely.
"""
import os
import urllib.request
from pathlib import Path

def download_cache():
    """Download tiktoken cache files directly"""
    
    # Cache directory
    script_dir = Path(__file__).parent.resolve()
    cache_dir = script_dir.parent / "tiktoken_cache"
    
    # tiktoken uses a hash directory
    hash_dir = cache_dir / "9b5ad71b2ce5302211f9c61530b329a4922fc6a4"
    
    # Create directories, handling existing ones
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
        hash_dir.mkdir(parents=True, exist_ok=True)
    except FileExistsError:
        # Directory already exists, that's fine
        pass
    except Exception as e:
        print(f"Error creating directories: {e}")
        print(f"Trying to use existing directory...")
    
    # Verify hash_dir is actually a directory
    if not hash_dir.is_dir():
        print(f"ERROR: {hash_dir} exists but is not a directory")
        return 1
    
    print("=" * 70)
    print("tiktoken Cache Direct Download")
    print("=" * 70)
    print(f"\nCache directory: {cache_dir}")
    print("Downloading encoding files from OpenAI...\n")
    
    # Files to download
    files = {
        "o200k_base.tiktoken": "https://openaipublic.blob.core.windows.net/encodings/o200k_base.tiktoken",
        "cl100k_base.tiktoken": "https://openaipublic.blob.core.windows.net/encodings/cl100k_base.tiktoken"
    }
    
    downloaded = []
    failed = []
    
    for filename, url in files.items():
        target_path = hash_dir / filename
        
        # Check if file already exists
        if target_path.exists():
            try:
                size_mb = target_path.stat().st_size / (1024 * 1024)
                print(f"{filename} already exists ({size_mb:.2f} MB) - SKIPPED")
                downloaded.append((filename, size_mb))
                continue
            except Exception:
                # File exists but can't stat it, try to download anyway
                pass
        
        try:
            print(f"Downloading {filename}...", end=" ", flush=True)
            
            # Download file
            urllib.request.urlretrieve(url, target_path)
            
            # Verify downloaded
            size_mb = target_path.stat().st_size / (1024 * 1024)
            print(f"OK ({size_mb:.2f} MB)")
            downloaded.append((filename, size_mb))
            
        except Exception as e:
            print(f"FAILED: {e}")
            failed.append((filename, str(e)))
    
    # Summary
    print("\n" + "=" * 70)
    print("Results")
    print("=" * 70)
    print(f"Downloaded: {len(downloaded)}")
    print(f"Failed: {len(failed)}")
    
    if downloaded:
        print(f"\nDownloaded files (in {hash_dir}):")
        total_size = 0
        for filename, size in downloaded:
            print(f"  - {filename} ({size:.2f} MB)")
            total_size += size
        print(f"\nTotal size: {total_size:.2f} MB")
    
    if failed:
        print("\nFailed downloads:")
        for filename, error in failed:
            print(f"  - {filename}: {error}")
    
    if len(downloaded) == len(files):
        print("\n" + "=" * 70)
        print("SUCCESS!")
        print("=" * 70)
        print("\nNext steps:")
        print("1. Verify the files in backend/tiktoken_cache/")
        print("2. Commit them to the repository:")
        print("   git add backend/tiktoken_cache/")
        print("   git commit -m 'chore: Add pre-cached tiktoken encodings'")
        print("\nThe build process will use these pre-downloaded files.")
        return 0
    else:
        print("\n" + "=" * 70)
        print("ERROR: Some downloads failed")
        print("=" * 70)
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(download_cache())

