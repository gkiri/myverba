# Enhanced Manim Prompt Engineering Guide

## 🧠 Smart Prompt Engineering for High-Quality Manim Code Generation

### 🎯 Core Principles for LLM Manim Code Generation

#### 1. **Explicit Animation Instruction Pattern**
```
❌ BAD PROMPT: "Create animations for the concepts"
✅ GOOD PROMPT: "For every visual element, explicitly wrap in proper animation:
- Text objects → Write(text) or FadeIn(text)
- Shapes/VGroups → Create(shape) or FadeIn(shape)  
- Transformations → object.animate.method()
NEVER pass raw mobjects to self.play()"
```

#### 2. **Function Return Type Awareness**
```
✅ ESSENTIAL INSTRUCTION:
"These utility functions return TUPLES that must be unpacked:
- create_dramatic_title_entrance(text, zone, style) → (mobject, animation)
  Usage: obj, anim = create_dramatic_title_entrance(...); self.add(obj); self.play(anim)
- create_particle_explosion(center, num, colors, radius) → (particles, animation)
  Usage: particles, explosion = create_particle_explosion(...); self.add(particles); self.play(explosion)

These functions return SINGLE OBJECTS that need animation wrappers:
- create_energy_wave(...) → VGroup (use: self.play(Create(wave)))
- create_growth_spiral(...) → VGroup (use: self.play(Create(spiral)))
- create_layered_background(...) → VGroup (use: self.add(bg))
```

#### 3. **Class Name Precision**
```
✅ CRITICAL INSTRUCTION:
"The class name MUST be exactly: {manim_class_name}
Do not modify this name in any way. Use it exactly as provided."
```

### 🎨 Advanced Creative Prompt Patterns

#### Pattern 1: **Cinematic Storytelling Framework**
```
🎬 CINEMATIC STRUCTURE PROMPT:
"Structure your animation like a movie:

ACT I - DRAMATIC ENTRANCE (20% of time):
- Epic title reveal using create_dramatic_title_entrance() 
- Set the stage with create_layered_background()
- Introduce key visual elements with particle effects

ACT II - VISUAL STORYTELLING (60% of time):
- Transform concepts into visual metaphors
- Use create_concept_network() for interconnected ideas
- Use create_process_flow() for sequential processes  
- Use create_energy_wave() for relationships/connections
- Layer multiple visual elements for rich composition

ACT III - CLIMACTIC REVELATION (15% of time):
- Major visual revelation or transformation
- Use create_particle_explosion() for dramatic moments
- Resolve conflicts with create_conflict_visualization()

ACT IV - ELEGANT CONCLUSION (5% of time):
- Smooth fade-out of elements
- Leave lasting visual impression"
```

#### Pattern 2: **Educational Transformation Rules**
```
📚 CONTENT TRANSFORMATION PATTERNS:
"Apply these visual transformation rules:

Historical Events → create_timeline_visualization() with dramatic markers
Political Movements → create_concept_network() showing interconnections  
Conflicts → create_conflict_visualization() with visual tension
Processes → create_process_flow() with smooth transitions
Key Figures → Custom shapes with create_emphasis_effect()
Cause & Effect → create_energy_wave() connections
Growth/Development → create_growth_spiral() patterns
Dramatic Moments → create_particle_explosion() effects"
```

#### Pattern 3: **Visual Hierarchy Prompt**
```
🎨 VISUAL HIERARCHY INSTRUCTION:
"Create depth and professional composition:

BACKGROUND LAYER:
- create_layered_background() for atmospheric foundation
- Subtle, non-distracting elements

MIDDLE LAYER:
- Main content using zones (MAIN_CONTENT_AREA, LEFT_HALF, RIGHT_HALF)
- Primary visual elements and text

FOREGROUND LAYER:
- create_particle_explosion() effects
- create_emphasis_effect() highlights
- Dynamic animations that draw attention

INTERACTIVE LAYER:
- create_energy_wave() connections between elements
- Movement and transformation animations"
```

### 🔧 Technical Precision Prompts

#### CRITICAL ERROR FIX: Data Structure Compliance
```
🚨 TIMELINE VISUALIZATION DATA STRUCTURE (MANDATORY):
create_timeline_visualization(events_data, start_year, end_year, length)
# events_data MUST be: [(year: int, description: str, color), ...]
# ❌ WRONG: [("1920\nEvent", BLUE), ("1921\nEvent", GREEN)]  # 2-tuple
# ✅ CORRECT: [(1920, "Event", BLUE), (1921, "Event", GREEN)]  # 3-tuple

EXAMPLE:
events = [
    (1920, "Non-Cooperation Launched", BLUE),
    (1921, "Mass Participation", GREEN), 
    (1922, "Chauri Chaura Incident", RED),
    (1922, "Movement Suspended", PURPLE)
]
timeline = create_timeline_visualization(events, 1919, 1923)
```

#### 🎨 Centralized Color and Import Management
```
✅ CRITICAL INSTRUCTIONS FOR COLOR AND IMPORTS:

Your generated code **MUST BE a Python class** that inherits from `manim.Scene`. 
(e.g., `class MySectionScene(Scene):`)\n\nA dedicated color module is available at `anim_gemini.colors`. This module contains all standard Manim color definitions (e.g., RED, BLUE, GREEN_C, GOLD_E, etc.).\n\nThe main script that assembles all generated classes will handle importing the Manim library elements (like `Scene`, `Text`, `Circle`) and will also import the color module as `mcolors` at the top level. Specifically, the main script will include:\n`from manim import *` (or specific Manim imports)\n`import anim_gemini.colors as mcolors`\n\n**INSTRUCTIONS FOR YOUR GENERATED PYTHON CLASS:**\n\n1.  Within your class methods (especially `construct(self)`), you **MUST** reference all colors using the `mcolors` alias. For example:\n    *   `title_text = Text("My Title", color=mcolors.GOLD_E)`\n    *   `some_shape.set_color(mcolors.BLUE_D)`\n    *   `highlight_color = mcolors.YELLOW_C`\n2.  You **MUST NOT** include `import anim_gemini.colors as mcolors` within the class you generate. This import will be handled by the main script.\n3.  You **MUST NOT** include general Manim imports like `from manim import *` or `from manim import Scene, Text` within the class you generate. These will also be handled by the main script.\n4.  **CRITICAL COLOR RULE:** You **MUST ONLY** use color variable names that are *explicitly defined* in the `anim_gemini.colors` module (aliased as `mcolors`). For example, if `anim_gemini.colors.py` defines `BLUE_C`, you can use `mcolors.BLUE_C`. **DO NOT invent or use any color names (e.g., `AQUA_BLUE`, `PRIMARY_BLUE`, `DARK_BG`) that are not found in `anim_gemini.colors.py`. Using undefined color names will cause errors.** The `mcolors` module provides an extensive list of available colors.
5.  You **MUST NOT** define your own color variables using hex codes within the class (e.g., do not write `my_custom_red = "#FF0000"`).

Your task is to generate ONLY the Python class for the Manim scene based on the script section provided. Do not add any code outside this class definition.\n\nExample of the expected output format for a section:\n\n\`\`\`python\nclass MyDescriptiveSceneName(Scene):\n    def construct(self):\n        title = Text("Example Title", font_size=48, color=mcolors.TEAL_D)\n        circle = Circle(radius=1.5, color=mcolors.RED_B, fill_opacity=0.5)\n        self.play(Write(title))\n        self.play(Create(circle))\n        # ... more animation code using mcolors for all color properties ...\n        self.wait(2)\n\`\`\`\n```

#### Function Return Type Awareness (UPDATED)
```
✅ CRITICAL FUNCTION SIGNATURES:
create_timeline_visualization(events_data, start_year, end_year, length=8)
# events_data: List[(year: int, description: str, color: Color)]
# RETURNS: VGroup (use: self.play(Create(timeline)))

create_particle_explosion(center_point=ORIGIN, num_particles=20, colors=None, explosion_radius=2)
# RETURNS: (particles_group: VGroup, explosion_animation: Animation)
# Usage: particles, explosion = create_particle_explosion(...)
#        self.add(particles); self.play(explosion)

create_energy_wave(start_point, end_point, color=BLUE, amplitude=0.2, frequency=3)
# RETURNS: VGroup (use: self.play(Create(wave)))

create_dramatic_title_entrance(title_text, zone_name="TITLE_AREA", entrance_style="explosion")
# RETURNS: (title_object: Mobject, title_animation: Animation)
# Usage: obj, anim = create_dramatic_title_entrance(...)
#        self.add(obj); self.play(anim)
```

#### Error Prevention Framework
```
🛡️ ERROR PREVENTION CHECKLIST PROMPT:
"Before submitting code, verify:
□ Timeline events use (year: int, description: str, color) 3-tuple format
□ No raw Text/VGroup objects in self.play() calls
□ All utility function tuples properly unpacked
□ All single-object returns wrapped in animations
□ Class name matches exactly: {manim_class_name}
□ **Strict Color Adherence:** All colors are referenced **ONLY** via `mcolors` (e.g., `mcolors.RED`, `mcolors.BLUE_A`). **Verify that every color name used (e.g., `mcolors.XYZ`) corresponds to an actual variable in `anim_gemini.colors.py`. DO NOT use colors like `mcolors.AQUA_BLUE` or `mcolors.PRIMARY_BLUE` if they are not explicitly defined in `anim_gemini.colors.py`.**
□ No direct hex codes (e.g., `"#FF0000"`) are used for colors.
□ No color names are used without the `mcolors.` prefix (e.g., do not use `RED`, use `mcolors.RED`).
□ The generated code is ONLY a class definition; it does NOT include `from manim import ...` or `import anim_gemini.colors as mcolors`.
□ No SVGMobject or ImageMobject with file paths
□ All self.play() calls contain Animation objects only"
```

#### Animation Flow Pattern
```
⚡ ANIMATION FLOW INSTRUCTION:
"Follow this animation pattern:

1. SETUP (no animations):
   bg = create_layered_background(...)
   self.add(bg)

2. ENTRANCE ANIMATIONS:
   title_obj, title_anim = create_dramatic_title_entrance(...)
   self.add(title_obj); self.play(title_anim)

3. CONTENT ANIMATIONS:
   text = create_smart_text(...)
   self.play(Write(text))
   
   shape = Circle(...)
   self.play(Create(shape))

4. EFFECT ANIMATIONS:
   particles, explosion = create_particle_explosion(...)
   self.add(particles); self.play(explosion)

5. EXIT ANIMATIONS:
   self.play(FadeOut(VGroup(all_objects)))"
```

### 🎪 Creative Enhancement Techniques

#### Multi-Sensory Prompt Engineering
```
🌈 MULTI-SENSORY CREATIVE PROMPT:
"Engage multiple senses through visual design:

VISUAL RHYTHM:
- Use LaggedStart() for musical timing
- Vary animation speeds (run_time) for pacing
- Create visual beats with particle effects

COLOR PSYCHOLOGY:
- Warm colors (RED, ORANGE, YELLOW) for energy/conflict
- Cool colors (BLUE, GREEN, PURPLE) for calm/resolution  
- Use random_color() for dynamic variety
- Color transitions to show emotional journey

SPATIAL DYNAMICS:
- Use get_zone_center() for strategic positioning
- Create depth with layered backgrounds
- Use .animate.shift(), .animate.scale() for smooth motion
- Build tension with approaching elements"
```

#### Metaphorical Thinking Framework
```
🎭 METAPHORICAL VISUALIZATION PROMPT:
"Transform abstract concepts into concrete visuals:

ABSTRACT CONCEPT → VISUAL METAPHOR:
- Cooperation → create_energy_wave() connections
- Conflict → create_conflict_visualization() with opposing forces
- Growth → create_growth_spiral() expanding patterns
- Revolution → create_particle_explosion() with transformation
- Unity → create_concept_network() with strong connections
- Process → create_process_flow() with clear progression
- Power → Emphasized shapes with create_emphasis_effect()
- Change → Transform() animations between states"
```

### 🎯 Domain-Specific Prompt Templates

#### Historical Events Template
```
📜 HISTORICAL EVENTS PROMPT:
"For historical content, create cinematic narratives:

TIMELINE: Use create_timeline_visualization() for chronological events
FIGURES: Create character silhouettes with basic shapes + create_emphasis_effect()
CONFLICTS: Use create_conflict_visualization() for wars/disagreements
MOVEMENTS: Use create_energy_wave() for spreading ideas

CRITICAL: Timeline events MUST use 3-tuple format:
events = [(year_int, "description", COLOR), ...]
NOT: [("year_description", COLOR), ...]
TURNING POINTS: Use create_particle_explosion() for dramatic moments
CAUSE & EFFECT: Connect with animated arrows and energy flows"
```

#### Scientific Concepts Template  
```
🔬 SCIENTIFIC CONCEPTS PROMPT:
"For scientific content, emphasize process and discovery:

PROCESSES: Use create_process_flow() for scientific methods
NETWORKS: Use create_concept_network() for interconnected principles
GROWTH: Use create_growth_spiral() for evolutionary patterns
FORCES: Use create_energy_wave() for field effects
DISCOVERIES: Use create_particle_explosion() for eureka moments
SYSTEMS: Layer multiple elements showing interaction"
```

### 🚀 Advanced Prompt Optimization

#### Context Stacking Technique
```
🧠 CONTEXT STACKING METHOD:
"Layer your prompts with increasing specificity:

LAYER 1 - FOUNDATION:
Basic animation rules + function return types

LAYER 2 - CREATIVE FRAMEWORK:  
Cinematic structure + visual transformation rules

LAYER 3 - TECHNICAL PRECISION:
Error prevention + animation flow patterns

LAYER 4 - DOMAIN EXPERTISE:
Subject-specific visualization strategies

LAYER 5 - QUALITY BENCHMARKS:
Professional standards + memorable impact criteria"
```

#### Iteration and Refinement
```
🔄 ITERATIVE IMPROVEMENT PROMPT:
"Generate code with built-in quality escalation:

PASS 1: Functional code with proper animations
PASS 2: Add creative visual effects and timing
PASS 3: Enhance with advanced layout and composition  
PASS 4: Polish with seamless transitions and professional flow

Each pass should maintain all previous quality while adding new dimension."
```

### 🏆 Quality Assurance Framework

#### Professional Standards Checklist
```
✨ PROFESSIONAL QUALITY STANDARDS:
"Your animation should achieve:

TECHNICAL EXCELLENCE:
□ Zero animation errors (no raw mobjects in self.play())
□ Proper function usage (tuples unpacked correctly)
□ Smooth timing and transitions
□ Clean, readable code structure

CREATIVE EXCELLENCE:  
□ Visually engaging and memorable
□ Clear educational value
□ Professional aesthetic quality
□ Innovative use of available effects

EDUCATIONAL EXCELLENCE:
□ Concepts clearly communicated through visuals
□ Logical flow and progression
□ Appropriate for target audience (UPSC students)
□ Lasting impression and retention value"
```

## 💡 Implementation Strategy

### For Project Integration:
1. **Update prompt templates** with these patterns
2. **Layer prompts** starting with technical requirements, then creative framework
3. **Include examples** of correct vs incorrect patterns
4. **Add validation** for common error patterns
5. **Create feedback loops** to refine prompts based on output quality

### For Continuous Improvement:
1. **Monitor error patterns** in generated code
2. **Analyze successful outputs** for pattern extraction  
3. **A/B test different prompt variations**
4. **Build prompt libraries** for different content types
5. **Implement automated quality scoring**

This framework ensures that LLMs generate technically correct, creatively rich, and educationally effective Manim animations consistently. 