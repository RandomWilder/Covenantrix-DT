/**
 * electron-builder afterPack hook
 * Ensures Python executables have correct permissions on macOS
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
    console.log('Skipping permission fix on non-macOS platform');
    return;
  }

  console.log('Running afterPack hook for macOS...');
  
  const appPath = path.join(appOutDir, `${context.packager.appInfo.productFilename}.app`);
  const pythonDistPath = path.join(appPath, 'Contents', 'Resources', 'python-dist', 'bin');
  
  console.log(`App path: ${appPath}`);
  console.log(`Python dist path: ${pythonDistPath}`);
  
  // Check if python-dist exists
  if (!fs.existsSync(pythonDistPath)) {
    console.warn(`WARNING: Python dist path not found: ${pythonDistPath}`);
    return;
  }

  try {
    // Make all Python executables executable
    console.log('Setting executable permissions on Python binaries...');
    await execAsync(`chmod +x "${pythonDistPath}"/python*`);
    
    // Verify permissions
    const { stdout } = await execAsync(`ls -la "${pythonDistPath}"`);
    console.log('Python dist directory contents:');
    console.log(stdout);
    
    console.log('✓ Python executable permissions set successfully');
  } catch (error) {
    console.error('ERROR setting Python permissions:', error);
    throw error;
  }
};