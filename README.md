# Covenantrix Desktop

RAG-powered Document Intelligence Desktop Application

## Features

- RAG-powered document intelligence
- Self-contained with bundled Python backend
- Multi-platform support (Windows, macOS, Linux)
- Automatic updates

## Installation

Download the latest release for your platform from [GitHub Releases](https://github.com/RandomWilder/Covenantrix-DT/releases):
- **Windows**: `Covenantrix-Setup-{version}.exe`
- **macOS**: `Covenantrix-{version}.dmg`
- **Linux**: `Covenantrix-{version}.AppImage`

## System Requirements

- **Windows**: Windows 10 or later
- **macOS**: macOS 10.15 (Catalina) or later
- **Linux**: Ubuntu 20.04 or later, or equivalent

No Python installation required - the backend is bundled.

## Development

### Prerequisites
- Node.js 20+
- Python 3.11+
- Git

### Setup
```bash
# Clone repository
git clone https://github.com/RandomWilder/Covenantrix-DT.git
cd covenantrix

# Install frontend dependencies
cd covenantrix-desktop
npm install

# Start development mode
npm run dev
```

### Building
```bash
# Build for current platform
npm run dist

# Build unpacked (for testing)
npm run dist:dir
```

For detailed build and release documentation, see [docs/BUILD_AND_RELEASE.md](docs/BUILD_AND_RELEASE.md).

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - Copyright © 2025 Covenantrix