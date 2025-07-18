"""
Final Manim Package
==================

This package contains the complete Manim-based text-to-video generation system.

Main Components:
- anim_gemini: Core animation generation system
"""

import sys
import importlib

# Cache for lazy-loaded modules
_modules = {}

def __getattr__(name):
    if name == 'anim_gemini':
        if name not in _modules:
            try:
                # Import the module directly using importlib
                module_name = f"{__name__}.{name}"
                _modules[name] = importlib.import_module(module_name)
            except ImportError as e:
                raise ImportError(f"anim_gemini module not available: {e}")
        return _modules[name]
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = ['anim_gemini'] 