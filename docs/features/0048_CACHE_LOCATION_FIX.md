# tiktoken Cache Location Fix - Explicit Directory Control

## Problem Identified

The tiktoken encodings were being cached successfully (all "OK" responses), but the cache files couldn't be located afterward. This happened because:

1. **tiktoken uses unpredictable cache locations** in different environments
2. **Embedded Python** may use different paths than standard Python
3. **Windows** vs **Unix** have different default cache locations
4. We were trying to **search for the cache after creating it** instead of controlling where it goes

## Root Cause

tiktoken's default caching behavior:
- Without `TIKTOKEN_CACHE_DIR` set, tiktoken chooses its own location
- In CI/CD with embedded Python, this location can be:
  - System temp directories
  - Hidden Python package directories  
  - Platform-specific cache locations we don't have visibility into

**Result**: Files cached successfully but impossible to locate and copy for bundling.

## ✅ Solution: Pre-Configure Cache Directory

Instead of searching for the cache **after** it's created, we now:

### 1. **Set Cache Location BEFORE tiktoken Runs**

```python
# In backend/scripts/cache_tiktoken_encodings.py
def setup_cache_directory():
    """Create and configure dedicated tiktoken cache directory"""
    # Use predictable location: PROJECT_ROOT/dist/tiktoken-cache-temp
    script_dir = Path(__file__).parent.parent.parent.resolve()
    cache_dir = script_dir / "dist" / "tiktoken-cache-temp"
    
    # Create directory
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    # CRITICAL: Set environment variable BEFORE importing tiktoken
    os.environ['TIKTOKEN_CACHE_DIR'] = str(cache_dir)
    
    return str(cache_dir)

# Set up BEFORE any tiktoken imports
CACHE_DIR = setup_cache_directory()
```

### 2. **tiktoken Honors This Setting**

When `TIKTOKEN_CACHE_DIR` environment variable is set, tiktoken uses that location exclusively. This gives us:
- ✅ **Predictable location**: Always `dist/tiktoken-cache-temp/`
- ✅ **Cross-platform**: Works on Windows, macOS, Linux
- ✅ **CI/CD compatible**: Same behavior in GitHub Actions
- ✅ **Verifiable**: We can check if files exist after caching

### 3. **Node.js Script Copies from Known Location**

```javascript
// In covenantrix-desktop/scripts/cache-tiktoken.js
function getTiktokenCacheDir(pythonOutput) {
  // 1. Parse from Python output (primary)
  const match = pythonOutput.match(/TIKTOKEN_CACHE_DIR=(.+)/);
  if (match) {
    return match[1].trim();
  }
  
  // 2. Try dedicated location (fallback)
  const dedicatedCache = path.join(__dirname, '..', '..', 'dist', 'tiktoken-cache-temp');
  if (fs.existsSync(dedicatedCache)) {
    return dedicatedCache;
  }
  
  // 3. Search common locations (last resort)
  return findTiktokenCache();
}
```

## Architecture

### Before (Broken):
```
1. Run tiktoken → Cache to ??? (unknown location)
2. Search for cache → Can't find it
3. Build fails or continues without cache
```

### After (Fixed):
```
1. Set TIKTOKEN_CACHE_DIR=dist/tiktoken-cache-temp/
2. Run tiktoken → Cache to dist/tiktoken-cache-temp/
3. Verify cache exists → SUCCESS
4. Copy to dist/tiktoken-cache/ for bundling
5. electron-builder includes in app resources
```

## File Changes

### 1. Python Script (`backend/scripts/cache_tiktoken_encodings.py`)

**Added**:
- `setup_cache_directory()` - Creates and configures dedicated cache location
- Sets `TIKTOKEN_CACHE_DIR` environment variable **before** importing tiktoken
- Removed search logic (no longer needed)
- Enhanced verification with file count and size reporting

**Output now includes**:
```
Pre-configured cache directory: /path/to/dist/tiktoken-cache-temp
TIKTOKEN_CACHE_DIR environment variable set

============================================================
tiktoken Encoding Cache Generator
============================================================
[1/2] Caching encodings by name...
  - Caching encoding: o200k_base... OK
  - Caching encoding: cl100k_base... OK
...
Cache directory: /path/to/dist/tiktoken-cache-temp
Directory exists: True
Cached files found: 2

Cached encoding files:
  - 9b5ad71b.../o200k_base.tiktoken (1.75 MB)
  - 9b5ad71b.../cl100k_base.tiktoken (1.75 MB)

Total cache size: 3.50 MB

TIKTOKEN_CACHE_DIR=/path/to/dist/tiktoken-cache-temp

============================================================
SUCCESS: Cache generated and verified
============================================================
```

### 2. Node.js Script (`covenantrix-desktop/scripts/cache-tiktoken.js`)

**Enhanced**:
- Primary: Parse `TIKTOKEN_CACHE_DIR` from Python output
- Secondary: Check dedicated `dist/tiktoken-cache-temp/` location
- Tertiary: Search common system locations (fallback)
- Better error messages and logging
- Graceful degradation if cache not found

## Expected Build Output

### Python Script Phase:
```
=== Pre-caching tiktoken encodings ===
Running tiktoken cache script...
Pre-configured cache directory: D:\a\Covenantrix-DT\Covenantrix-DT\dist\tiktoken-cache-temp
TIKTOKEN_CACHE_DIR environment variable set

============================================================
tiktoken Encoding Cache Generator
============================================================
[1/2] Caching encodings by name...
  - Caching encoding: o200k_base... OK
  - Caching encoding: cl100k_base... OK
[2/2] Caching encodings by model name...
  - Caching model: gpt-4o... OK
  - Caching model: gpt-4o-mini... OK
  - Caching model: gpt-4o-2024-08-06... OK
  - Caching model: text-embedding-3-large... OK

============================================================
Cache Summary
============================================================
Successfully cached: 6 encodings
Failed: 0 encodings

Cache directory: D:\a\Covenantrix-DT\Covenantrix-DT\dist\tiktoken-cache-temp
Directory exists: True
Cached files found: 2

Cached encoding files:
  - 9b5ad71b2ce5302211f9c61530b329a4922fc6a4\o200k_base.tiktoken (1.75 MB)
  - 9b5ad71b2ce5302211f9c61530b329a4922fc6a4\cl100k_base.tiktoken (1.75 MB)

Total cache size: 3.50 MB

TIKTOKEN_CACHE_DIR=D:\a\Covenantrix-DT\Covenantrix-DT\dist\tiktoken-cache-temp

============================================================
SUCCESS: Cache generated and verified
============================================================
✓ Found 2 encoding file(s) in cache
```

### Node.js Build Phase (prebuild):
```
============================================================
tiktoken Encoding Cache Builder
============================================================

[1/5] Detecting Python executable...
  ✓ Using: dist/python-dist/bin/python

[2/5] Verifying Python availability...
  ✓ Python 3.11.6

[3/5] Running tiktoken cache script...
[... Python output above ...]

[4/5] Copying cache to dist directory...
  Cache directory from Python: /path/to/dist/tiktoken-cache-temp
  ✓ Copied to: /path/to/dist/tiktoken-cache

[5/5] Verifying cache contents...
  ✓ Found 2 encoding file(s)
  ✓ Total size: 3.50 MB

============================================================
✓ tiktoken cache ready for bundling
============================================================
```

## Benefits of This Approach

### 1. **Deterministic Behavior**
- Cache always goes to `dist/tiktoken-cache-temp/`
- No guessing or searching required
- Same behavior on all platforms

### 2. **CI/CD Friendly**
- Works in GitHub Actions Windows/macOS runners
- Works with embedded Python distributions
- No dependency on user home directories

### 3. **Verifiable**
- Can confirm files exist after caching
- Can count files and measure size
- Build fails explicitly if caching actually fails

### 4. **Clean Build Process**
- Cache in `dist/` directory (already .gitignored)
- Cleaned up with `npm run clean`
- Temporary cache doesn't pollute user system

### 5. **Maintainable**
- Clear flow: Set location → Cache → Verify → Copy → Bundle
- Easy to debug (known paths)
- Logs show exactly what's happening

## Testing

### Local Test:
```bash
cd backend
python scripts/cache_tiktoken_encodings.py
# Should show SUCCESS and list files in dist/tiktoken-cache-temp/
```

### Build Test:
```bash
cd covenantrix-desktop
node scripts/cache-tiktoken.js
# Should copy from dist/tiktoken-cache-temp/ to dist/tiktoken-cache/
```

### Full Build:
```bash
npm run package:win
# Check build logs for "SUCCESS: Cache generated and verified"
```

## Commit Message

```
fix: Set tiktoken cache directory explicitly before caching

Previously, tiktoken would cache to unpredictable locations making
it impossible to locate and bundle the cache files. Now we set
TIKTOKEN_CACHE_DIR environment variable before any tiktoken operations,
ensuring cache always goes to dist/tiktoken-cache-temp/.

This fixes the "cache directory not found" issue on Windows CI runners
and ensures reliable cache bundling across all platforms.

Changes:
- Set TIKTOKEN_CACHE_DIR before importing tiktoken
- Use dedicated dist/tiktoken-cache-temp/ directory
- Enhanced verification with file counting
- Better error messages and logging

Fixes #48 (SSL certificate verification on corporate networks)
```

## Why This Works

tiktoken library respects the `TIKTOKEN_CACHE_DIR` environment variable:
- When set, tiktoken uses only that location
- When not set, tiktoken uses platform-specific defaults
- By setting it **before** importing tiktoken, we control the behavior

**Key insight**: Don't search for the cache after it's created. Tell tiktoken where to create it in the first place.

## Summary

- ✅ **Problem**: Cache created but location unknown
- ✅ **Solution**: Set `TIKTOKEN_CACHE_DIR` before caching
- ✅ **Location**: `dist/tiktoken-cache-temp/` (predictable)
- ✅ **Verification**: Check files exist, count them, measure size
- ✅ **Bundling**: Copy to `dist/tiktoken-cache/` for electron-builder
- ✅ **Result**: Reliable cache bundling on all platforms

