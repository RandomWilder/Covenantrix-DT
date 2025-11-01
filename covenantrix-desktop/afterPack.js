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
  
  console.log('Running afterPack hook...');
  
  // Determine resources path based on platform
  let resourcesPath;
  if (electronPlatformName === 'darwin') {
    const appPath = path.join(appOutDir, `${context.packager.appInfo.productFilename}.app`);
    resourcesPath = path.join(appPath, 'Contents', 'Resources');
  } else {
    // Windows/Linux
    resourcesPath = path.join(appOutDir, 'resources');
  }
  
  console.log(`Resources path: ${resourcesPath}`);
  
  // Verify tiktoken cache exists
  const tiktokenCachePath = path.join(resourcesPath, 'tiktoken-cache');
  if (fs.existsSync(tiktokenCachePath)) {
    let fileCount = 0;
    function countFiles(dir) {
      const entries = fs.readdirSync(dir, { withFileTypes: true });
      for (const entry of entries) {
        const fullPath = path.join(dir, entry.name);
        if (entry.isDirectory()) {
          countFiles(fullPath);
        } else if (entry.name.endsWith('.tiktoken')) {
          fileCount++;
        }
      }
    }
    countFiles(tiktokenCachePath);
    console.log(`✓ tiktoken cache bundled: ${fileCount} encoding file(s)`);
  } else {
    console.warn('WARNING: tiktoken cache not found - SSL issues may occur on corporate networks');
  }
  
  // macOS-specific: Set Python executable permissions
  if (electronPlatformName === 'darwin') {
    console.log('Setting Python executable permissions (macOS)...');
    
    const pythonDistPath = path.join(resourcesPath, 'python-dist', 'bin');
    
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
  }
};