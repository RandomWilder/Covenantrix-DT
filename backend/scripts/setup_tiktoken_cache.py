#!/usr/bin/env python3
"""
Simple script to download tiktoken cache files.
This does everything: cleanup, download, verify.
"""
import os
import shutil
import urllib.request
from pathlib import Path

def main():
    print("=" * 70)
    print("tiktoken Cache Setup")
    print("=" * 70)
    
    # Get paths
    script_dir = Path(__file__).parent.resolve()
    cache_dir = script_dir.parent / "tiktoken_cache"
    
    # Step 1: Clean up any existing corrupted files
    print("\n[1/3] Cleaning up old files...")
    if cache_dir.exists():
        try:
            shutil.rmtree(cache_dir)
            print("  ✓ Removed old tiktoken_cache directory")
        except Exception as e:
            print(f"  Error removing directory: {e}")
            return 1
    
    # Step 2: Create fresh directory structure
    print("\n[2/3] Creating directory structure...")
    hash_dir = cache_dir / "9b5ad71b2ce5302211f9c61530b329a4922fc6a4"
    hash_dir.mkdir(parents=True, exist_ok=True)
    print(f"  ✓ Created {cache_dir}")
    
    # Step 3: Download files
    print("\n[3/3] Downloading encoding files...")
    files = {
        "o200k_base.tiktoken": "https://openaipublic.blob.core.windows.net/encodings/o200k_base.tiktoken",
        "cl100k_base.tiktoken": "https://openaipublic.blob.core.windows.net/encodings/cl100k_base.tiktoken"
    }
    
    success = 0
    for filename, url in files.items():
        target_path = hash_dir / filename
        try:
            print(f"  Downloading {filename}...", end=" ", flush=True)
            urllib.request.urlretrieve(url, target_path)
            size_mb = target_path.stat().st_size / (1024 * 1024)
            print(f"OK ({size_mb:.2f} MB)")
            success += 1
        except Exception as e:
            print(f"FAILED: {e}")
    
    # Summary
    print("\n" + "=" * 70)
    if success == len(files):
        print("SUCCESS!")
        print("=" * 70)
        print(f"\nDownloaded {success} files to:")
        print(f"  {cache_dir}")
        print(f"\nNext: Commit these files to git:")
        print(f"  git add backend/tiktoken_cache/")
        print(f"  git commit -m 'chore: Add tiktoken cache files'")
        return 0
    else:
        print("FAILED!")
        print("=" * 70)
        print(f"Only {success}/{len(files)} files downloaded successfully")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())

