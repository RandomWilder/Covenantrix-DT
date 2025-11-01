/**
 * Pre-cache tiktoken encodings for bundling with the application
 * Runs before electron-builder packaging
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// ANSI color codes for better output
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  red: '\x1b[31m',
  cyan: '\x1b[36m'
};

function log(message, color = colors.reset) {
  console.log(`${color}${message}${colors.reset}`);
}

function getPythonExecutable() {
  const platform = process.platform;
  
  // Try bundled Python first
  if (platform === 'win32') {
    const bundledPython = path.join(__dirname, '..', '..', 'dist', 'python-dist', 'python.exe');
    if (fs.existsSync(bundledPython)) {
      return bundledPython;
    }
  } else {
    const bundledPython = path.join(__dirname, '..', '..', 'dist', 'python-dist', 'bin', 'python');
    if (fs.existsSync(bundledPython)) {
      return bundledPython;
    }
  }
  
  // Fall back to system Python
  return 'python3';
}

function findTiktokenCache() {
  /**
   * Search for tiktoken cache directory across common locations
   * Returns the path if found, null otherwise
   */
  const homeDir = process.env.HOME || process.env.USERPROFILE;
  const searchPaths = [];
  
  if (process.platform === 'win32') {
    // Windows locations
    const localAppData = process.env.LOCALAPPDATA || path.join(homeDir, 'AppData', 'Local');
    searchPaths.push(
      path.join(localAppData, 'tiktoken_cache'),
      path.join(localAppData, 'tiktoken'),
      path.join(process.env.APPDATA || path.join(homeDir, 'AppData', 'Roaming'), 'tiktoken_cache'),
      path.join(homeDir, '.tiktoken_cache'),
      path.join(homeDir, '.cache', 'tiktoken')
    );
  } else {
    // Unix/macOS locations
    searchPaths.push(
      path.join(homeDir, '.cache', 'tiktoken'),
      path.join(homeDir, '.tiktoken_cache'),
      path.join('/tmp', 'tiktoken_cache')
    );
  }
  
  // Search for directory containing .tiktoken files
  for (const searchPath of searchPaths) {
    if (fs.existsSync(searchPath)) {
      // Check if it contains .tiktoken files
      try {
        const hasTokenFiles = searchForTiktokenFiles(searchPath);
        if (hasTokenFiles) {
          return searchPath;
        }
      } catch (err) {
        // Continue searching
      }
    }
  }
  
  return null;
}

function searchForTiktokenFiles(dir) {
  /**
   * Recursively search for .tiktoken files in directory
   * Returns true if found
   */
  try {
    const entries = fs.readdirSync(dir, { withFileTypes: true });
    for (const entry of entries) {
      if (entry.isFile() && entry.name.endsWith('.tiktoken')) {
        return true;
      }
      if (entry.isDirectory()) {
        const subPath = path.join(dir, entry.name);
        if (searchForTiktokenFiles(subPath)) {
          return true;
        }
      }
    }
  } catch (err) {
    // Permission denied or other error
  }
  return false;
}

function getTiktokenCacheDir(pythonOutput) {
  // Parse the TIKTOKEN_CACHE_DIR from Python script output (primary method)
  const match = pythonOutput.match(/TIKTOKEN_CACHE_DIR=(.+)/);
  if (match) {
    const cacheDir = match[1].trim();
    log(`  Cache directory from Python: ${cacheDir}`, colors.cyan);
    
    // Verify it exists and has files
    if (fs.existsSync(cacheDir)) {
      const hasFiles = searchForTiktokenFiles(cacheDir);
      if (hasFiles) {
        return cacheDir;
      } else {
        log(`  WARNING: Cache directory exists but no .tiktoken files found`, colors.yellow);
      }
    }
  }
  
  // Try the dedicated temporary cache location (set by Python script)
  const dedicatedCache = path.join(__dirname, '..', '..', 'dist', 'tiktoken-cache-temp');
  if (fs.existsSync(dedicatedCache) && searchForTiktokenFiles(dedicatedCache)) {
    log(`  Found cache in dedicated location: ${dedicatedCache}`, colors.green);
    return dedicatedCache;
  }
  
  // Search for actual cache location
  const foundCache = findTiktokenCache();
  if (foundCache) {
    log(`  Found cache via search: ${foundCache}`, colors.green);
    return foundCache;
  }
  
  log(`  WARNING: Could not locate tiktoken cache`, colors.yellow);
  return null;
}

function copyDirectory(src, dest) {
  // Create destination directory
  if (!fs.existsSync(dest)) {
    fs.mkdirSync(dest, { recursive: true });
  }
  
  // Copy all files and subdirectories
  const entries = fs.readdirSync(src, { withFileTypes: true });
  
  for (const entry of entries) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);
    
    if (entry.isDirectory()) {
      copyDirectory(srcPath, destPath);
    } else {
      fs.copyFileSync(srcPath, destPath);
    }
  }
}

function main() {
  log('\n' + '='.repeat(60), colors.cyan);
  log('tiktoken Encoding Cache Builder', colors.bright + colors.cyan);
  log('='.repeat(60), colors.cyan);
  
  // Step 1: Detect Python executable
  log('\n[1/5] Detecting Python executable...', colors.bright);
  const pythonExec = getPythonExecutable();
  log(`  ✓ Using: ${pythonExec}`, colors.green);
  
  // Step 2: Verify Python is available
  log('\n[2/5] Verifying Python availability...', colors.bright);
  try {
    const pythonVersion = execSync(`"${pythonExec}" --version`, { encoding: 'utf8' });
    log(`  ✓ ${pythonVersion.trim()}`, colors.green);
  } catch (error) {
    log('  ✗ Python not found!', colors.red);
    log('  WARNING: Skipping tiktoken cache generation', colors.yellow);
    log('  Application will attempt to download encodings at runtime', colors.yellow);
    process.exit(0); // Exit gracefully to allow development builds
  }
  
  // Step 3: Run Python cache script
  log('\n[3/5] Running tiktoken cache script...', colors.bright);
  const scriptPath = path.join(__dirname, '..', '..', 'backend', 'scripts', 'cache_tiktoken_encodings.py');
  
  if (!fs.existsSync(scriptPath)) {
    log(`  ✗ Script not found: ${scriptPath}`, colors.red);
    log('  WARNING: Skipping tiktoken cache generation', colors.yellow);
    process.exit(0);
  }
  
  try {
    const output = execSync(`"${pythonExec}" "${scriptPath}"`, { 
      encoding: 'utf8',
      stdio: 'pipe'
    });
    
    // Show Python script output
    console.log(output);
    
    // Parse cache directory from output
    const cacheDir = getTiktokenCacheDir(output);
    log(`  ✓ Cache generated at: ${cacheDir}`, colors.green);
    
    // Step 4: Copy cache to dist directory
    log('\n[4/5] Copying cache to dist directory...', colors.bright);
    const distCacheDir = path.join(__dirname, '..', '..', 'dist', 'tiktoken-cache');
    
    if (!cacheDir) {
      log(`  ✗ Cache directory could not be determined`, colors.red);
      log('  WARNING: Cache will not be bundled', colors.yellow);
      log('  Application will attempt to download encodings at runtime', colors.yellow);
      process.exit(0);
    }
    
    if (!fs.existsSync(cacheDir)) {
      log(`  ✗ Cache directory not found: ${cacheDir}`, colors.red);
      log('  WARNING: Cache will not be bundled', colors.yellow);
      log('  Application will attempt to download encodings at runtime', colors.yellow);
      process.exit(0);
    }
    
    // Remove old cache if exists
    if (fs.existsSync(distCacheDir)) {
      fs.rmSync(distCacheDir, { recursive: true, force: true });
    }
    
    // Copy cache
    copyDirectory(cacheDir, distCacheDir);
    log(`  ✓ Copied to: ${distCacheDir}`, colors.green);
    
    // Step 5: Verify cache contents
    log('\n[5/5] Verifying cache contents...', colors.bright);
    let fileCount = 0;
    let totalSize = 0;
    
    function countFiles(dir) {
      const entries = fs.readdirSync(dir, { withFileTypes: true });
      for (const entry of entries) {
        const fullPath = path.join(dir, entry.name);
        if (entry.isDirectory()) {
          countFiles(fullPath);
        } else if (entry.name.endsWith('.tiktoken')) {
          fileCount++;
          totalSize += fs.statSync(fullPath).size;
        }
      }
    }
    
    countFiles(distCacheDir);
    
    const sizeMB = (totalSize / (1024 * 1024)).toFixed(2);
    log(`  ✓ Found ${fileCount} encoding file(s)`, colors.green);
    log(`  ✓ Total size: ${sizeMB} MB`, colors.green);
    
    if (fileCount === 0) {
      log('  ✗ WARNING: No .tiktoken files found in cache!', colors.yellow);
      log('  Application may fail to initialize on corporate networks', colors.yellow);
    }
    
    log('\n' + '='.repeat(60), colors.cyan);
    log('✓ tiktoken cache ready for bundling', colors.bright + colors.green);
    log('='.repeat(60) + '\n', colors.cyan);
    
  } catch (error) {
    log(`  ✗ Error running cache script: ${error.message}`, colors.red);
    log('  WARNING: Cache generation failed', colors.yellow);
    log('  Application will attempt to download encodings at runtime', colors.yellow);
    // Exit gracefully to allow development builds
    process.exit(0);
  }
}

// Run the script
main();

