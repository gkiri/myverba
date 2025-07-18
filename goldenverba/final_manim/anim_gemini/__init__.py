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

# Use lazy imports to avoid failing when dependencies are missing
def __getattr__(name):
    if name == 'project_drishti':
        try:
            from . import project_drishti
            return project_drishti
        except ImportError as e:
            raise ImportError(f"project_drishti module not available: {e}")
    elif name == 'layout_utils':
        try:
            from . import layout_utils
            return layout_utils
        except ImportError as e:
            raise ImportError(f"layout_utils module not available: {e}")
    elif name == 'colors':
        try:
            from . import colors
            return colors
        except ImportError as e:
            raise ImportError(f"colors module not available: {e}")
    elif name == 'main_pipeline':
        try:
            from . import main_pipeline
            return main_pipeline
        except ImportError as e:
            raise ImportError(f"main_pipeline module not available: {e}")
    elif name in ['DidacticScripter', 'VisualArchitect', 'ManimRenderer', 'VideoAnalyzer', 'ManimCompiler', 'config']:
        # Import each component individually to avoid single point of failure
        if name == 'DidacticScripter':
            try:
                from .project_drishti import DidacticScripter
                return DidacticScripter
            except ImportError as e:
                raise ImportError(f"DidacticScripter not available: {e}")
        elif name == 'VisualArchitect':
            try:
                from .project_drishti import VisualArchitect
                return VisualArchitect
            except ImportError as e:
                raise ImportError(f"VisualArchitect not available: {e}")
        elif name == 'ManimRenderer':
            try:
                from .project_drishti import ManimRenderer
                return ManimRenderer
            except ImportError as e:
                raise ImportError(f"ManimRenderer not available: {e}")
        elif name == 'VideoAnalyzer':
            try:
                from .project_drishti import VideoAnalyzer
                return VideoAnalyzer
            except ImportError as e:
                raise ImportError(f"VideoAnalyzer not available: {e}")
        elif name == 'ManimCompiler':
            try:
                from .project_drishti import ManimCompiler
                return ManimCompiler
            except ImportError as e:
                raise ImportError(f"ManimCompiler not available: {e}")
        elif name == 'config':
            try:
                from .project_drishti import config
                return config
            except ImportError as e:
                raise ImportError(f"config not available: {e}")
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = [
    'project_drishti',
    'layout_utils',
    'colors',
    'main_pipeline',
    'DidacticScripter',
    'VisualArchitect',
    'ManimRenderer',
    'VideoAnalyzer',
    'ManimCompiler',
    'config',
] 