# Manim Community v0.19.0 API Reference for LLM Guidance

## General Tips for LLM:
- Always use Manim Community Edition v0.19.0 syntax.
- Import necessary modules: `from manim import *`.
- The main class for your animation should inherit from `Scene`.
- Use `self.add(mobject, ...)` to add mobjects to the scene without animation.
- Use `self.play(animation_type(mobject, ...), ...)` to animate mobjects.
- Use `self.wait(duration)` to pause the animation.
- Ensure Mobjects are created (e.g., `my_circle = Circle()`) before being added or animated.
- Pay attention to required arguments for constructors and methods. Check the documentation for specifics.
- Colors are typically uppercase constants (e.g., `BLUE`, `RED`) or hex strings (e.g., `"#FF0000"`).
- Positions and directions are often NumPy arrays (e.g., `UP`, `DOWN`, `LEFT`, `RIGHT`, `ORIGIN`) or explicit coordinates like `[x, y, z]`.

## Scenes (`manim.scene.scene.Scene`)
The base class for creating animations.

```python
from manim import *

class MyAnimation(Scene):
    def construct(self):
        # Your code here
        circle = Circle()
        self.play(Create(circle))
        self.wait(1)
```

### Key Scene Methods:
- `self.add(*mobjects)`: Adds mobjects to the scene. They appear instantly.
  - Example: `self.add(Circle(), Square().shift(RIGHT*2))`
- `self.play(*animations, run_time=None, **kwargs)`: Plays one or more animations.
  - Example: `self.play(Create(my_object), FadeIn(another_object), run_time=2)`
- `self.wait(duration=1)`: Pauses the scene for a number of seconds.
  - Example: `self.wait()` or `self.wait(2.5)`
- `self.remove(*mobjects)`: Removes mobjects from the scene instantly.

## Mobjects (Mathematical Objects - The visual elements)

### Basic Shapes (primarily from `manim.mobject.geometry.polygram` and `manim.mobject.geometry.arc`)
- `Circle(**kwargs)`:
  - `radius`: float (default: 1.0)
  - `color`: ManimColor (e.g., `BLUE`)
  - `fill_opacity`: float (0 to 1, for fill transparency)
  - `stroke_color`: ManimColor (color of the border)
  - `stroke_width`: float (width of the border)
  - Example: `my_circle = Circle(radius=0.5, color=BLUE, fill_opacity=0.5)`
- `Square(**kwargs)`:
  - `side_length`: float (default: 2.0)
  - Example: `my_square = Square(side_length=1.5, color=RED)`
- `Rectangle(**kwargs)`:
  - `width`: float (default: 4.0)
  - `height`: float (default: 2.0)
  - Example: `my_rect = Rectangle(width=3, height=1, color=GREEN)`
- `Polygon(*vertices, **kwargs)`: Creates a polygon from a list of vertex coordinates.
  - `vertices`: Each argument is a point (list or np.array `[x,y,z]`)
  - Example: `triangle = Polygon([-1,-1,0], [1,-1,0], [0,1,0], color=YELLOW)`
- `Line(start=LEFT, end=RIGHT, **kwargs)` (from `manim.mobject.geometry.line`):
  - `start`, `end`: Points (e.g., `LEFT`, `RIGHT`, `[0,0,0]`, `np.array([1,2,0])`)
  - `buff`: float (buffer space at ends)
  - Example: `my_line = Line(np.array([-1,-1,0]), np.array([1,1,0]), stroke_color=WHITE)`
- `Arrow(start=LEFT, end=RIGHT, **kwargs)` (from `manim.mobject.geometry.line`):
  - Inherits from `Line`, adds an arrowhead.
  - `max_tip_length_to_length_ratio`: Controls tip size relative to arrow length.
  - Example: `my_arrow = Arrow(ORIGIN, UP*2, buff=0)`
- `Dot(point=ORIGIN, radius=0.08, **kwargs)` (from `manim.mobject.geometry.arc`):
  - `point`: Location of the dot.
  - `radius`: Radius of the dot.
  - Example: `my_dot = Dot(point=[1,2,0], radius=0.1, color=PINK)`
- `Annulus(inner_radius=1, outer_radius=2, **kwargs)` (from `manim.mobject.geometry.arc`): A ring shape.
    - Example: `ring = Annulus(inner_radius=0.5, outer_radius=0.8, color=TEAL, fill_opacity=1)`


### Text and Formulas
- `Text(text, font="", font_size=DEFAULT_FONT_SIZE, **kwargs)` (from `manim.mobject.text.text_mobject`):
  - `text`: The string to display.
  - `font`: Name of the font.
  - `font_size`: Size of the font.
  - Example: `hello_text = Text("Hello Manim", font_size=48)`
- `MathTex(*tex_strings, arg_separator="", environment="align*", **kwargs)` (from `manim.mobject.svg.tex_mobject.MathTex`): For LaTeX math expressions.
  - `tex_strings`: Raw LaTeX strings (use `r"..."` for raw strings).
  - Example: `formula = MathTex(r"E = mc^2", font_size=60)`
  - For multiple lines or aligned equations: `MathTex(r"a &= b \\ c &= d")`
- `Tex(*tex_strings, arg_separator="", environment="align*", **kwargs)` (from `manim.mobject.svg.tex_mobject.Tex`): For general TeX content.
  - Similar to `MathTex` but can use different TeX environments.
  - Example: `general_tex = Tex("Some text and \\textit{italic}.", font_size=36)`

### Grouping Mobjects
- `VGroup(*mobjects, **kwargs)` (from `manim.mobject.types.vectorized_mobject.VGroup`): Groups multiple mobjects. Transformations applied to the group affect all members.
  - Example: `group = VGroup(my_circle, my_square)`
  - `group.arrange(direction=RIGHT, buff=0.5, center=True)`: Arranges mobjects in the group.
    - `direction`: `RIGHT`, `DOWN`, `LEFT`, `UP`, or a custom vector.
    - `buff`: Spacing between mobjects.
  - Example: `group.arrange(DOWN, buff=0.2)`

## Animations (from `manim.animation.*`)

### Creation & Destruction
- `Create(mobject_or_vmobject, **kwargs)` (from `manim.animation.creation`): Animates the "drawing" or creation of an mobject.
  - Example: `self.play(Create(my_circle))`
- `Uncreate(mobject_or_vmobject, reverse_rate_function=True, **kwargs)` (from `manim.animation.creation`): Reverse of `Create`.
  - Example: `self.play(Uncreate(my_circle))`
- `Write(mobject_or_vmobject, **kwargs)` (from `manim.animation.creation`): Animates writing text or drawing shapes progressively.
  - Example: `self.play(Write(hello_text))`
- `DrawBorderThenFill(mobject_or_vmobject, **kwargs)` (from `manim.animation.creation`): Draws the border, then fills the mobject.
  - Example: `self.play(DrawBorderThenFill(my_square))`
- `FadeIn(mobject_or_vmobject, **kwargs)` (from `manim.animation.fading`): Fades in an mobject.
  - Example: `self.play(FadeIn(my_dot))`
- `FadeOut(mobject_or_vmobject, **kwargs)` (from `manim.animation.fading`): Fades out an mobject.
  - Example: `self.play(FadeOut(my_dot))`

### Transformations
- `Transform(mobject, target_mobject, **kwargs)` (from `manim.animation.transform`): Transforms `mobject` into the shape and position of `target_mobject`. `mobject` is modified.
  - Example: `self.play(Transform(my_square, my_circle))` (square turns into circle)
- `ReplacementTransform(mobject, target_mobject, **kwargs)` (from `manim.animation.transform`): Similar to `Transform`, but `mobject` is replaced by `target_mobject`. `mobject` is removed, `target_mobject` is added.
  - Example:
    ```python
    square = Square()
    circle = Circle()
    self.add(square)
    self.play(ReplacementTransform(square, circle)) # square is gone, circle remains
    ```
- `MoveToTarget(mobject, **kwargs)` (from `manim.animation.transform`): Animates `mobject` to its `.target` attribute.
  - First, create and modify the target:
    ```python
    my_object = Circle()
    self.add(my_object)
    my_object.generate_target() # Create a copy to modify
    my_object.target.shift(RIGHT*2).scale(0.5).set_color(YELLOW)
    ```
  - Then, play the animation: `self.play(MoveToTarget(my_object))`
- `ApplyMethod(mobject_method, *args, **kwargs)` (from `manim.animation.transform`): Animates a method call on an mobject.
  - Example (color change): `self.play(ApplyMethod(my_circle.set_fill, YELLOW, 1))` (color, opacity)
  - Example (shift): `self.play(ApplyMethod(my_square.shift, UP*2))`
- `Rotate(mobject, angle=PI, axis=OUT, about_point=None, **kwargs)` (from `manim.animation.rotation`):
  - `angle`: Rotation angle in radians (e.g., `PI/2`, `np.radians(90)`).
  - `axis`: Axis of rotation (e.g., `OUT`, `UP`, `[1,1,0]`).
  - `about_point`: Point to rotate around (default is mobject's center).
  - Example: `self.play(Rotate(my_square, angle=PI/2, about_point=ORIGIN))`

### `.animate` Syntax (Convenient alternative to `ApplyMethod` for many common transformations)
Many mobject methods can be animated directly using the `.animate` syntax.
- `mobject.animate.method_name(*args)`
- This is often preferred for its conciseness.
- Examples:
  - `self.play(my_circle.animate.shift(RIGHT*3))`
  - `self.play(my_square.animate.scale(2))`
  - `self.play(my_text.animate.set_color(BLUE))`
  - `self.play(my_dot.animate.move_to([2,2,0]))`
  - `self.play(my_arrow.animate.put_start_and_end_on(ORIGIN, RIGHT*2))`

### Movement (Mobject methods - use with `.animate` or `ApplyMethod` for animation)
- `mobject.shift(direction_vector)`: Moves mobject.
  - Example (animation): `self.play(my_circle.animate.shift(LEFT*2))`
- `mobject.move_to(point_or_mobject)`: Moves mobject's center to a new location.
  - Example (animation): `self.play(my_square.animate.move_to(UP + RIGHT))`
- `mobject.next_to(other_mobject, direction=RIGHT, buff=0.25)`: Positions mobject next to another.
  - Example (animation): `self.play(my_square.animate.next_to(my_circle, DOWN, buff=0.5))`
- `mobject.scale(scale_factor, **kwargs)`: Scales mobject.
  - `about_point`: Point to scale around (default is mobject's center).
  - Example (animation): `self.play(my_circle.animate.scale(0.5))`
- `mobject.set_color(color)`: Changes color.
  - Example (animation): `self.play(my_text.animate.set_color(GREEN))`
- `mobject.set_opacity(opacity)`: Changes fill opacity.
  - Example (animation): `self.play(my_rect.animate.set_opacity(0.5))`

### Indication Animations (from `manim.animation.indication`)
- `Indicate(mobject, scale_factor=1.1, color=None, **kwargs)`: Briefly scales and optionally changes color.
  - Example: `self.play(Indicate(my_text))`
- `Flash(mobject_or_point, color=None, flash_radius=None, **kwargs)`: Creates a flash effect.
  - Example: `self.play(Flash(my_dot, color=YELLOW, flash_radius=0.5))`
- `Circumscribe(mobject_or_point, shape=Circle, color=YELLOW, **kwargs)`: Draws a shape (default Circle) around an mobject.
  - Example: `self.play(Circumscribe(formula, color=BLUE))`
- `Wiggle(mobject, scale_value=1.1, rotation_angle=0.01 * TAU, **kwargs)`: Wiggles the mobject.
  - Example: `self.play(Wiggle(my_text))`

### Animation Composition (from `manim.animation.composition`)
- `AnimationGroup(*animations, lag_ratio=0.0, **kwargs)`: Plays multiple animations simultaneously.
  - `lag_ratio`: Staggers the start of animations. `lag_ratio=0` means all start together. `lag_ratio=1` means they play sequentially (like Succession).
  - Example: `self.play(AnimationGroup(FadeIn(my_circle), Create(my_square), lag_ratio=0.2))`
- `Succession(*animations, lag_ratio=1.0, **kwargs)`: Plays animations one after another.
  - By default, `lag_ratio=1.0` means the next animation starts after the previous one finishes.
  - Example: `self.play(Succession(Create(my_circle), Write(my_text), FadeOut(my_circle)))`

## Colors (from `manim.utils.color` and `manim.utils.color.manim_colors`)
- Common predefined colors: `BLUE`, `RED`, `GREEN`, `YELLOW`, `PINK`, `PURPLE`, `ORANGE`, `TEAL`, `GOLD`, `WHITE`, `BLACK`, `GREY`.
  - Often, variants like `BLUE_A`, `BLUE_B`, `BLUE_C`, `BLUE_D`, `BLUE_E` exist. `BLUE` is often `BLUE_C`.
- Specify by hex string: `"#RRGGBB"` (e.g., `"#FFD700"` for a gold-like color).
- `ManimColor` class can be used for more complex color operations, but direct use of constants or hex is common.
- Example: `my_circle.set_color(RED)` or `my_square = Square(color=PURPLE)`

## Coordinates and Positioning
- **Constants** (NumPy arrays from `manim.constants`):
  - `ORIGIN`: `[0,0,0]`
  - `UP`: `[0,1,0]`, `DOWN`: `[0,-1,0]`, `LEFT`: `[-1,0,0]`, `RIGHT`: `[1,0,0]`
  - `IN`: `[0,0,-1]` (towards viewer), `OUT`: `[0,0,1]` (away from viewer, for 3D)
  - `X_AXIS`, `Y_AXIS`, `Z_AXIS`
  - `UL` (Up-Left), `UR` (Up-Right), `DL` (Down-Left), `DR` (Down-Right)
- Directions can be scaled: `2*UP`, `0.5*LEFT`.
- Points can be added/subtracted: `circle.get_center() + RIGHT * 2`.
- **Mobject position getters**:
  - `mobject.get_center()`
  - `mobject.get_left()`, `mobject.get_right()`, `mobject.get_top()`, `mobject.get_bottom()`
  - `mobject.get_corner(direction_vector)` (e.g., `mobject.get_corner(UL)`)
  - `mobject.get_critical_point(direction)`: Returns point on border in that direction.

## Common Pitfalls for LLM & Best Practices:
- **Animation Syntax**:
  - **BAD**: `self.play(square.shift(UP))` (This shifts `square` instantly, then `self.play` has no animation to play for its duration).
  - **GOOD (using `.animate`)**: `self.play(square.animate.shift(UP))`
  - **GOOD (using `ApplyMethod`)**: `self.play(ApplyMethod(square.shift, UP))`
  - **GOOD (using `Transform`)**: If changing multiple properties, `Transform` or `MoveToTarget` might be better.
    ```python
    square_target = square.copy().shift(UP).set_color(BLUE)
    self.play(Transform(square, square_target))
    ```
- **Mobject Not Added**: An mobject must be on screen (added via `self.add` or as part of a previous animation like `Create`) for many animations like `FadeOut` or `Transform` (when it's the source) to make sense. `Create`, `FadeIn`, `Write` will add the mobject.
- **Forgetting `self.play` or `self.add`**: Mobjects/animations won't appear or happen without these scene methods.
- **`MathTex` vs `Tex` vs `Text`**:
  - `MathTex`: For LaTeX mathematical expressions (e.g., `r"\sum_{i=0}^n x_i"`). Use raw strings `r"..."`.
  - `Tex`: For general TeX content, can include text and simple math.
  - `Text`: For plain text strings without LaTeX processing. Faster and simpler for non-math.
- **Outdated APIs**: Focus on Manim Community v0.19.0. Avoid APIs from very old Manim versions (e.g., `ShowCreation` is now `Create`, `ShowPassingFlash` has replacements or can be composed).
- **`VGroup` Arrangement**: After adding mobjects to a `VGroup`, call `group.arrange()` to position them relative to each other. Animating this arrangement:
  ```python
  group = VGroup(Circle(), Square())
  self.add(group) # Add them at their default positions (likely ORIGIN)
  # Then animate the arrangement
  self.play(group.animate.arrange(RIGHT, buff=1))
  ```
  Or, arrange first, then `Create` or `FadeIn` the group:
  ```python
  group = VGroup(Circle(), Square()).arrange(RIGHT, buff=1)
  self.play(Create(group))
  ```
- **Target for `MoveToTarget`**:
  ```python
  obj = Circle()
  self.add(obj)
  obj.generate_target() # Crucial: creates obj.target as a copy
  obj.target.shift(RIGHT*2).set_color(YELLOW) # Modify the target
  self.play(MoveToTarget(obj)) # Animates obj to become like obj.target
  ```
- **Chaining `.animate` calls for simultaneous effects**:
    - **BAD (often leads to only the last `.animate` in the chain being effective, or errors)**: `self.play(my_obj.animate.shift(UP).scale(2))`
    - **GOOD (Using `MoveToTarget` for a clear final state)**:
      ```python
      my_obj.generate_target()
      my_obj.target.shift(UP).scale(2) # Define the combined final state
      self.play(MoveToTarget(my_obj))
      ```
    - **GOOD (Sequential animations)**:
      ```python
      self.play(my_obj.animate.shift(UP))
      self.play(my_obj.animate.scale(2))
      ```
    - **Note**: The most reliable way to achieve a state that is *both* shifted and scaled simultaneously is using `MoveToTarget`. Chaining `.animate.method1().method2()` is not reliably supported for combining transformations in a single `self.play` call.


This document is not exhaustive but covers common elements and patterns for Manim Community v0.19.0. For more detailed information, the LLM should be reminded to (conceptually) refer to the official Manim Community documentation. 