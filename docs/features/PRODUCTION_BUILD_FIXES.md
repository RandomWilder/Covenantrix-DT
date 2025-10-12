# Production Build Fixes - v1.1.3

## Summary
Fixed critical production build issues that prevented the application from launching after installation on Windows.

## Issues Identified

### 1. Frontend Build Directory Mismatch (CRITICAL)
**Problem**: Vite was building to `dist-electron/` but electron-builder was looking for files in `dist/`, resulting in no frontend files being included in the production build.

**Symptoms**:
- Application window opens but shows blank screen
- Console errors: `Failed to load resource: net::ERR_FILE_NOT_FOUND` for `index.html`
- Backend starts successfully but no UI appears

### 2. Auto-Updater Repository Mismatch
**Problem**: electron-builder was configured to check for updates in `RandomWilder/covenantrix-desktop` but the actual repository is `RandomWilder/Covenantrix-DT`.

**Symptoms**:
- Error dialog: "No published versions on GitHub"
- Auto-update feature completely broken

### 3. NSIS Installer Process Handling
**Problem**: Windows installer didn't properly handle running Covenantrix processes during installation.

**Symptoms**:
- Error during installation: "Something seems to be stuck"
- Required manual retry even after fresh system restart
- Inconsistent installation experience

## Fixes Applied

### Fix 1: Standardized Build Output Directory
**Files Changed**:
- `covenantrix-desktop/vite.config.ts`: Changed `outDir` from `'dist-electron'` to `'dist'`
- `covenantrix-desktop/electron/main.js`: Updated path from `'../dist-electron/index.html'` to `'../dist/index.html'`

**Reasoning**: Using the standard `dist/` directory aligns with Vite defaults and electron-builder expectations.

### Fix 2: Corrected Repository Configuration
**Files Changed**:
- `covenantrix-desktop/electron-builder.yml`: Changed `repo` from `covenantrix-desktop` to `Covenantrix-DT`

**Impact**: Auto-updater will now correctly check for and download updates from GitHub releases.

### Fix 3: Improved NSIS Installer Configuration
**Files Changed**:
- `covenantrix-desktop/electron-builder.yml`: 
  - Added `allowElevation: true`
  - Changed `packElevateHelper` from `false` to `true`
  - Added `runAfterFinish: true`

**Features**:
- Better elevation handling for installation
- Launch application after installation completes
- Improved installer reliability

## Testing Checklist

### Development Build
- [x] `npm run dev` - Development mode works
- [ ] Frontend loads correctly in dev mode
- [ ] Backend connects properly in dev mode

### Production Build
- [ ] `npm run build` - Build completes without errors
- [ ] `npm run package:win` - Windows installer created successfully
- [ ] Install on clean system - No "cannot be closed" errors
- [ ] Application launches - Frontend loads correctly
- [ ] Application launches - Backend starts within timeout
- [ ] Auto-updater - Checks correct repository
- [ ] Auto-updater - Downloads updates correctly

### Regression Testing
- [ ] Document upload works
- [ ] Chat functionality works
- [ ] Settings persistence works
- [ ] RAG engine initializes correctly
- [ ] OCR processing works

## Version Impact

These changes should be released as **v1.1.3** to fix the broken v1.1.2 release.

## Build Process Verification

### Before Release:
1. Update version in `covenantrix-desktop/package.json` to `1.1.3`
2. Test local build: `cd covenantrix-desktop && npm run package:win`
3. Install locally and verify all functionality
4. Commit changes: `git commit -m "v1.1.3: fix production build issues"`
5. Tag: `git tag v1.1.3`
6. Push: `git push && git push --tags`
7. Monitor GitHub Actions build
8. Test installer from GitHub Releases

### After Release:
1. Download installer from GitHub Releases
2. Test fresh installation on clean Windows machine
3. Verify auto-updater shows correct version
4. Verify all core functionality works

## Notes

- The Python distribution bundling is working correctly (verified by manual testing)
- Backend startup code handles missing API keys gracefully
- The issue was entirely frontend-related (missing HTML/JS files)
- NSIS improvements provide better user experience during installation

