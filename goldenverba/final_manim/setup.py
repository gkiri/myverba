from setuptools import setup, find_packages

setup(
    name="anim_gemini",
    version="1.0.0",
    description="Project Drishti - Enhanced Manim Color Management System",
    packages=find_packages(),
    install_requires=[
        "manim>=0.19.0",
        "numpy",
    ],
    python_requires=">=3.8",
) 