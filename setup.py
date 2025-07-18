from setuptools import find_packages, setup

setup(
    name="goldenverba",
    version="1.0.0",
    packages=find_packages(),
    python_requires=">=3.10.0",
    entry_points={
        "console_scripts": [
            "verba=goldenverba.server.cli:cli",
        ],
    },
    author="Weaviate",
    author_email="edward@weaviate.io",
    description="Welcome to Verba: The Golden RAGtriever, an open-source initiative designed to offer a streamlined, user-friendly interface for Retrieval-Augmented Generation (RAG) applications. In just a few easy steps, dive into your data and make meaningful interactions!",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/weaviate/Verba",
    classifiers=[
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    include_package_data=True,
    install_requires=[
        #"weaviate-client==3.23.1",
        "weaviate-client==4.6.4",
        "python-dotenv>=0.21.0,<0.22.0",
        "openai>=1.97.0",# Updated to modern OpenAI library with OpenAI class support
        "wasabi==1.1.2",
        "fastapi==0.102.0",
        "uvicorn[standard]==0.29.0",
        "click==8.1.7",
        "asyncio==3.4.3",
        "tiktoken==0.6.0",
        "requests==2.31.0",
        "pypdf==4.2.0",
        "python-multipart==0.0.9",
        "supabase==2.7.4",
        "google-generativeai==0.8.2",
        "vertexai>=1.70.0",
        "aiofiles==23.2.1",
        "PyPDF2==3.0.1",
        "voyageai==0.3.2",
        "langchain-text-splitters==0.3.7",
        "aiohttp==3.11.14",
        "trafilatura==2.0.0",
        "httpx==0.27.0"
    ],
    extras_require={
        "dev": ["pytest", "wheel", "twine", "black>=23.7.0", "setuptools"],
        "huggingface": [
            "sentence-transformers==2.7.0",
            "transformers==4.40.1",
            "torch==2.3.0",
            "accelerate==0.29.2",
        ],
        "google": [
            "vertexai==1.46.0",
        ],
        "manim": [
            # Animation and video generation dependencies
            "manim==0.19.0",
            "manim-voiceover==0.3.7", 
            "ffmpeg-python==0.2.0",
            "psutil",
            "matplotlib",
            # Note: openai, google-generativeai, aiofiles, aiohttp, python-dotenv 
            # are already included in main install_requires with compatible versions
        ]
    },
)
