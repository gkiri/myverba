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

# Use lazy imports to avoid manim dependency failures at startup
def __getattr__(name):
    if name == 'DidacticScripter':
        try:
            from .didactic_scripter import DidacticScripter
            return DidacticScripter
        except ImportError as e:
            raise ImportError(f"DidacticScripter not available: {e}")
    elif name == 'VisualArchitect':
        try:
            from .visual_architect import VisualArchitect
            return VisualArchitect
        except ImportError as e:
            raise ImportError(f"VisualArchitect not available: {e}")
    elif name == 'ManimRenderer':
        try:
            from .manim_renderer import ManimRenderer
            return ManimRenderer
        except ImportError as e:
            raise ImportError(f"ManimRenderer not available: {e}")
    elif name == 'VideoAnalyzer':
        try:
            from .video_analyzer import VideoAnalyzer
            return VideoAnalyzer
        except ImportError as e:
            raise ImportError(f"VideoAnalyzer not available: {e}")
    elif name == 'ManimCompiler':
        try:
            from .manim_compiler import ManimCompiler
            return ManimCompiler
        except ImportError as e:
            raise ImportError(f"ManimCompiler not available: {e}")
    elif name == 'config':
        try:
            from . import config
            return config
        except ImportError as e:
            raise ImportError(f"config not available: {e}")
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = [
    'DidacticScripter',
    'VisualArchitect', 
    'ManimRenderer',
    'VideoAnalyzer',
    'ManimCompiler',
    'config',
] 