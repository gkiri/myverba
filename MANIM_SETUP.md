# Manim Integration Setup

## Overview
Manim dependencies have been integrated as optional extras to avoid breaking existing functionality.

## Installation Options

### 1. Standard Verba (without Manim)
```bash
pip install -e .
# or
docker-compose up
```

### 2. Verba with Manim Support
```bash
# Local installation
pip install -e ".[manim]"

# Docker (automatically includes Manim system dependencies)
docker-compose up
```

## Dependencies Added

### Python Packages (setup.py extras_require["manim"])
- `manim==0.19.0` - Animation engine
- `manim-voiceover==0.3.7` - Voice synthesis for animations  
- `ffmpeg-python==0.2.0` - Python FFmpeg wrapper
- `psutil` - System and process utilities
- `matplotlib` - Plotting library

### System Dependencies (Dockerfile)
- `build-essential, python3-dev, pkg-config` - Build tools
- Graphics libraries for Manim:
  - `libcairo2-dev` - Cairo graphics library  
  - `libpango1.0-dev` - Pango text rendering (fixes manimpango build errors)
  - `libpangocairo-1.0-0` - Pango Cairo integration
  - `libgdk-pixbuf2.0-dev` - GDK Pixbuf for image handling
  - `libffi-dev, shared-mime-info` - Additional graphics support
- `ffmpeg` - Video processing
- `sox, libsox-fmt-all` - Audio processing
- LaTeX packages for mathematical rendering:
  - `texlive-latex-base, texlive-latex-extra`
  - `texlive-fonts-extra, texlive-fonts-recommended` 
  - `texlive-latex-recommended, texlive-science`
  - `dvisvgm` - SVG conversion

## Troubleshooting

### manimpango Build Errors
If you encounter `pangocairo >= 1.30.0 is required` errors:
- Ensure all Pango development packages are installed
- This is resolved by the updated Dockerfile which includes `libpango1.0-dev`

### ARM64/M1 Mac Issues  
- The Dockerfile should work on ARM64 architectures
- If problems persist, try building with `--platform linux/amd64`

### LaTeX Rendering Issues
- Full LaTeX support requires ~500MB+ of packages
- For minimal setup, you can remove LaTeX packages and disable LaTeX in Manim

## Version Preservation
Existing package versions are preserved to avoid breaking changes:
- `openai==0.27.9` (kept instead of manim's 1.84.0)
- `google-generativeai==0.8.2` (kept instead of manim's 0.8.5)
- `aiofiles==23.2.1`, `aiohttp==3.11.14`, `python-dotenv==1.0.0`

## Docker Build
The Docker image now includes all Manim system dependencies by default but Python packages are only installed when using the `[manim]` extra.

```bash
# Build and run with all dependencies
docker-compose up --build
``` 