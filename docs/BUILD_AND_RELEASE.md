# Build and Release Process

This document describes the simplified build and release pipeline for Covenantrix Desktop.

## Overview

The application uses a hybrid architecture:
- **Frontend**: Electron + React + TypeScript
- **Backend**: Python FastAPI bundled with PyInstaller

The build pipeline follows official Electron best practices while accommodating the Python backend requirement.

## Prerequisites

- Node.js 20+
- Python 3.11+
- Git

## Development Build

To build locally for testing:

```bash
cd covenantrix-desktop
npm install
npm run dist:dir
```

This creates an unpacked distribution in `covenantrix-desktop/dist/` for quick testing without creating installers.

## Local Distribution Build

To create installers for your current platform:

```bash
cd covenantrix-desktop
npm run dist
```

Installers will be created in `covenantrix-desktop/dist/`:
- Windows: `.exe` installer
- macOS: `.dmg` disk image
- Linux: `.AppImage` executable

## Release Process

The release process is fully automated via GitHub Actions when you push a version tag.

### Step 1: Update Version

Update the version in `covenantrix-desktop/package.json`:

```json
{
  "version": "1.0.12"
}
```

### Step 2: Commit and Tag

```bash
git add covenantrix-desktop/package.json
git commit -m "v1.0.12: release description"
git tag v1.0.12
```

### Step 3: Push to GitHub

```bash
git push
git push --tags
```

### Step 4: Automated Build

GitHub Actions will automatically:
1. Build the Python backend using PyInstaller
2. Build the React frontend
3. Package the Electron app for all platforms
4. Create a GitHub release with installers
5. Enable auto-update for existing installations

The entire process takes approximately 15-20 minutes.

## GitHub Actions Workflow

The workflow is defined in `.github/workflows/build.yml` and follows these steps:

### 1. Matrix Build
Builds simultaneously on three platforms:
- `windows-latest` - Windows 10/11 x64
- `macos-latest` - macOS Universal (Intel + Apple Silicon)
- `ubuntu-latest` - Linux x64

### 2. Build Steps Per Platform

**Setup:**
- Checkout code
- Setup Node.js 20 with npm cache
- Setup Python 3.11

**Backend Build:**
- Install Python dependencies
- Build backend executable using PyInstaller with `main.spec`
- Copy backend to `covenantrix-desktop/resources/backend/`

**Frontend Build:**
- Install npm dependencies
- Build React app
- Run electron-builder to create installers

**Release:**
- Upload installers to GitHub Release (if triggered by version tag)
- Enable auto-update channel

## NPM Scripts

The `package.json` includes simplified scripts:

- `npm run dev` - Start development mode with hot reload
- `npm run build` - Build React frontend only
- `npm run dist:dir` - Build unpacked distribution (fast, for testing)
- `npm run dist` - Build installer for current platform
- `npm run release` - Build and publish to GitHub (CI only)
- `npm run clean` - Clean build artifacts

## Electron Builder Configuration

Configuration is in `covenantrix-desktop/electron-builder.yml`:

**Key Settings:**
- `asar: true` - Compress app code
- `asarUnpack: resources/backend/**/*` - Keep backend uncompressed
- `compression: maximum` - Minimize installer size
- Platform-specific icons and signing configurations
- Auto-update configuration pointing to GitHub releases

## PyInstaller Configuration

Configuration is in `backend/main.spec`:

**Key Settings:**
- Single-file executable mode
- Optimized exclusions for unused packages
- Hidden imports for dynamic dependencies
- Binary stripping for smaller size

## Auto-Update

The app checks for updates on startup and periodically:
- Uses `electron-updater` package
- Checks GitHub releases for new versions
- Downloads and installs updates in background
- Prompts user to restart when ready

## Troubleshooting

### Build fails on Python step
- Ensure Python 3.11 is installed
- Check `backend/requirements.txt` for dependency issues
- Verify `backend/main.spec` configuration

### Build fails on Electron step
- Run `npm ci` to ensure clean dependencies
- Check `electron-builder.yml` configuration
- Verify `resources/backend/` contains backend executable

### Installer too large
- electron-builder automatically optimizes size
- Backend executable is already compressed
- Maximum compression is enabled

### Auto-update not working
- Ensure `electron-builder.yml` has correct publish configuration
- Check that GitHub release is not marked as draft or pre-release
- Verify `GH_TOKEN` is set in GitHub Actions

## Architecture Notes

### Why PyInstaller?
The Python backend is packaged as a standalone executable to avoid requiring users to install Python. This makes the app truly self-contained.

### Why separate backend/frontend builds?
- Backend: Built once with PyInstaller, copied to all platforms
- Frontend: Built by Vite, then packaged by electron-builder per platform

### Resource Handling
The backend executable is placed in `resources/backend/` which electron-builder:
- Includes in the app bundle
- Unpacks from asar for execution
- Makes accessible via `process.resourcesPath` in Electron

## Best Practices

1. **Version tags must start with 'v'** (e.g., v1.0.0)
2. **Always test locally before pushing tags**
3. **Keep commit messages simple** (e.g., "v1.0.12: description")
4. **Monitor GitHub Actions** for build status
5. **Test installers** from GitHub Releases before announcing

## Manual Release (Emergency)

If GitHub Actions fails, you can build locally:

```bash
# Build backend
cd backend
pip install -r requirements.txt pyinstaller
pyinstaller main.spec
cp dist/* ../covenantrix-desktop/resources/backend/

# Build and release
cd ../covenantrix-desktop
npm ci
npm run build
npm run release
```

This requires proper credentials and should only be used in emergencies.

## File Size Optimization

Current approximate sizes:
- Backend executable: 50-70 MB
- Frontend (Electron + React): 80-100 MB
- Total installer: 130-170 MB (varies by platform)

These sizes are normal for Electron apps with embedded Python backends.

