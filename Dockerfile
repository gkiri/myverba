FROM python:3.11
WORKDIR /Verba

# Install system dependencies for Manim and multimedia processing
RUN apt-get update && apt-get install -y \
    # Build tools and development headers
    build-essential \
    python3-dev \
    pkg-config \
    # Cairo and Pango graphics libraries for Manim
    libcairo2-dev \
    libpango1.0-dev \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-dev \
    libffi-dev \
    shared-mime-info \
    # Video processing
    ffmpeg \
    # Audio processing  
    sox \
    libsox-fmt-all \
    # LaTeX for mathematical rendering
    texlive-latex-base \
    texlive-latex-extra \
    texlive-fonts-extra \
    texlive-latex-recommended \
    texlive-science \
    texlive-fonts-recommended \
    dvisvgm \
    # Clean up package cache to reduce image size
    && rm -rf /var/lib/apt/lists/*

# Create the data directory (if it doesn't already exist in your project)
RUN mkdir -p /data

# Copy the key file from your local context into the image's /data directory
COPY goldenverba/components/generation/myupsc-mentor-ded3f62e859b.json /data/

# Set the necessary permissions inside the image
RUN chmod 600 /data/myupsc-mentor-ded3f62e859b.json

# Copy your application code
COPY . /Verba

# Upgrade setuptools and pip to fix pkg_resources issues
RUN pip install --upgrade setuptools pip

# Install dependencies step by step to avoid pkg_resources conflicts
RUN pip install -e . && \
    pip install manim==0.19.0 && \
    pip install manim-voiceover==0.3.7 && \
    pip install ffmpeg-python==0.2.0 psutil matplotlib

# Set the environment variable inside the image
ENV GOOGLE_APPLICATION_CREDENTIALS /data/myupsc-mentor-ded3f62e859b.json

EXPOSE 8000
CMD ["verba", "start"]
