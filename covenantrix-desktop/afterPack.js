/**
 * electron-builder afterPack hook
 * Ensures Python executables have correct permissions on macOS
 * and sets up libmagic environment variables
 */

const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');
const util = require('util');

const execAsync = util.promisify(exec);

exports.default = async function(context) {
  const { electronPlatformName, appOutDir } = context;
  
  // Only run on macOS
  if (electronPlatformName !== 'darwin') {
    console.log('Skipping macOS-specific setup on non-macOS platform');
    return;
  }

  console.log('Running afterPack hook for macOS...');
  
  const appPath = path.join(appOutDir, `${context.packager.appInfo.productFilename}.app`);
  const resourcesPath = path.join(appPath, 'Contents', 'Resources');
  const pythonDistPath = path.join(resourcesPath, 'python-dist', 'bin');
  
  console.log(`App path: ${appPath}`);
  console.log(`Resources path: ${resourcesPath}`);
  console.log(`Python dist path: ${pythonDistPath}`);
  
  // Check if python-dist exists
  if (!fs.existsSync(pythonDistPath)) {
    console.warn(`WARNING: Python dist path not found: ${pythonDistPath}`);
    return;
  }

  try {
    // === PYTHON PERMISSIONS ===
    console.log('Setting executable permissions on Python binaries...');
    await execAsync(`chmod +x "${pythonDistPath}"/python*`);
    
    // Verify permissions
    const { stdout } = await execAsync(`ls -la "${pythonDistPath}"`);
    console.log('Python dist directory contents:');
    console.log(stdout);
    
    console.log('✓ Python executable permissions set successfully');
    
    // === LIBMAGIC SETUP ===
    console.log('\nSetting up libmagic environment...');
    
    // Check if libmagic files exist
    const libPath = path.join(resourcesPath, 'lib');
    const magicDbPath = path.join(resourcesPath, 'share', 'misc');
    
    if (!fs.existsSync(libPath)) {
      console.warn(`WARNING: lib directory not found: ${libPath}`);
      console.warn('libmagic will not be available - file type detection may fail');
      return;
    }
    
    if (!fs.existsSync(magicDbPath)) {
      console.warn(`WARNING: magic database directory not found: ${magicDbPath}`);
      console.warn('libmagic will not be available - file type detection may fail');
      return;
    }
    
    // Verify magic database file exists
    const magicFiles = fs.readdirSync(magicDbPath);
    console.log('Magic database files:', magicFiles);
    
    const hasMagicDb = magicFiles.some(f => f === 'magic.mgc' || f === 'magic');
    
    if (!hasMagicDb) {
      console.warn('WARNING: No magic database file found in', magicDbPath);
      console.warn('libmagic will not be available - file type detection may fail');
      return;
    }
    
    // Create wrapper script that sets MAGIC environment variable
    const wrapperScriptPath = path.join(pythonDistPath, 'python-wrapper');
    const magicDbFile = magicFiles.includes('magic.mgc') 
      ? path.join(magicDbPath, 'magic.mgc')
      : path.join(magicDbPath, 'magic');
    
    const wrapperScript = `#!/bin/bash
# Python wrapper with libmagic environment setup

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RESOURCES_DIR="$(cd "$SCRIPT_DIR/../../" && pwd)"

# Set libmagic paths
export MAGIC="${RESOURCES_DIR}/share/misc/magic.mgc"
export DYLD_LIBRARY_PATH="${RESOURCES_DIR}/lib:$DYLD_LIBRARY_PATH"

# Execute Python with all arguments
exec "$SCRIPT_DIR/python3" "$@"
`;
    
    fs.writeFileSync(wrapperScriptPath, wrapperScript, { mode: 0o755 });
    console.log('✓ Created Python wrapper script with libmagic environment');
    console.log(`  MAGIC="${magicDbFile}"`);
    console.log(`  DYLD_LIBRARY_PATH="${libPath}"`);
    
    // Create .magic-env file for reference
    const magicEnvPath = path.join(resourcesPath, '.magic-env');
    const envConfig = `MAGIC=${magicDbFile}
DYLD_LIBRARY_PATH=${libPath}
`;
    fs.writeFileSync(magicEnvPath, envConfig);
    console.log('✓ Created .magic-env reference file');
    
    console.log('\n✅ macOS afterPack setup completed successfully');
    
  } catch (error) {
    console.error('ERROR in afterPack hook:', error);
    throw error;
  }
};