"""
Final Manim Package
==================

This package contains the complete Manim-based text-to-video generation system.

Main Components:
- anim_gemini: Core animation generation system
"""

# Use lazy imports to avoid failing when dependencies are missing
def __getattr__(name):
    if name == 'anim_gemini':
        try:
            from . import anim_gemini
            return anim_gemini
        except ImportError as e:
            raise ImportError(f"anim_gemini module not available: {e}")
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = ['anim_gemini'] 