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
- `libcairo2-dev` - Cairo graphics library  
- `ffmpeg` - Video processing
- `sox, libsox-fmt-all` - Audio processing
- LaTeX packages for mathematical rendering:
  - `texlive-latex-base, texlive-latex-extra`
  - `texlive-fonts-extra, texlive-fonts-recommended` 
  - `texlive-latex-recommended, texlive-science`
  - `dvisvgm` - SVG conversion

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