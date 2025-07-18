#!/usr/bin/env python3

from manim import *

class TestLatex(Scene):
    def construct(self):
        # Simple test equation
        equation = MathTex("E = mc^2")
        self.add(equation) 