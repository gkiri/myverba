"""
Project Drishti Package
======================

Vision: To revolutionize AI-driven educational content creation using Manim animations.

This package provides:
- Didactic scripting for educational content
- Visual architecture for Manim code generation
- Manim rendering capabilities
- Video analysis tools
- Ultra-optimized rendering system

Main Components:
- DidacticScripter: AI-powered script generation
- VisualArchitect: Manim code generation
- ManimRenderer: Video rendering
- VideoAnalyzer: Video analysis
- UltraOptimizedRender: Performance optimization
"""

# Import main modules
from .didactic_scripter import DidacticScripter
from .visual_architect import VisualArchitect
from .manim_renderer import ManimRenderer
from .video_analyzer import VideoAnalyzer
from .manim_compiler import ManimCompiler
from . import config


__all__ = [
    'DidacticScripter',
    'VisualArchitect',
    'ManimRenderer',
    'VideoAnalyzer',
    'ManimCompiler',
    'config',
] 