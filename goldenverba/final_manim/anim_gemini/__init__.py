"""
Anim Gemini Package
==================

AI-powered Manim animation generation system.

This package provides:
- Project Drishti: Core educational content creation
- Layout utilities for consistent Manim animations
- Color palette management
- Main pipeline orchestration

Main Components:
- project_drishti: Core educational content pipeline
- layout_utils: Manim layout utilities
- colors: Standardized color palette
- main_pipeline: End-to-end orchestration
"""

# Import main modules
from . import project_drishti
from . import layout_utils
from . import colors
from .main_pipeline import *

# Re-export project_drishti components for convenience
from .project_drishti import (
    DidacticScripter,
    VisualArchitect,
    ManimRenderer,
    VideoAnalyzer,
    ManimCompiler,
    config,
)

__all__ = [
    'project_drishti',
    'layout_utils',
    'colors',
    'DidacticScripter',
    'VisualArchitect',
    'ManimRenderer',
    'VideoAnalyzer',
    'ManimCompiler',
    'config',
] 