#!/usr/bin/env python3
"""
Scene 5 TTS Performance Benchmark: Sequential vs Async Preprocessing

This script benchmarks the actual production Scene 5 (Legacy of the Movement) 
comparing traditional sequential TTS vs async parallel preprocessing approaches.

Usage:
    python benchmark_scene5_tts.py

The script will render both versions and show the performance difference.
"""

import asyncio
import time
import os
from pathlib import Path
from dotenv import load_dotenv

from manim import *
from manim_voiceover import VoiceoverScene

# Load environment variables from the specific .env file
env_path = Path("/root/manim_gemini/.env")
if env_path.exists():
    load_dotenv(env_path)

# Import our custom services and async scene
from deepinfra_service import DeepInfraService
from async_deepinfra_service import AsyncDeepInfraService
from async_voiceover_scene import AsyncVoiceoverScene

# Import the helper functions from the original scene
import logging
logger = logging.getLogger(__name__)
import numpy as np

# Import colors - fallback to basic colors if not available
try:
    import anim_gemini.colors as mcolors
except ImportError:
    # Fallback color definitions
    class MockColors:
        YELLOW = YELLOW
        WHITE = WHITE
    mcolors = MockColors()

# --- Helper Functions from Original Scene ---
def stack_mobjects_vertically(mobjects_list, center_point=None, buff=0.5):
    if not mobjects_list:
        return VGroup()
    group = VGroup(*mobjects_list).arrange(DOWN, buff=buff)
    if center_point is not None:
        group.move_to(center_point)
    return group

def get_zone_center(zone_name: str):
    logger.warning(f"get_zone_center called for '{zone_name}'. It currently returns ORIGIN (0,0,0).")
    return ORIGIN

def create_smart_text(text, zone_name=None, font_size=48, color=WHITE):
    """Create text with smart positioning - simplified version"""
    text_obj = Text(text, font_size=font_size, color=color)
    if zone_name == "TITLE_AREA":
        text_obj.to_edge(UP, buff=0.5)
    return text_obj


class SequentialScene5Legacy(VoiceoverScene):
    """
    Sequential version of Scene 5: TTS calls made during animation rendering.
    This mirrors the original production scene structure.
    """
    
    def construct(self):
        # Set up the synchronous TTS service
        self.set_speech_service(
            DeepInfraService(
                voice="af_bella",
                model="hexgrad/Kokoro-82M",
                api_key=os.getenv("DEEPINFRA_API_KEY"),
                transcription_model=None
            )
        )
        
        # Create the title
        title_mobj = create_smart_text("Legacy of the Movement", zone_name="TITLE_AREA", font_size=48, color=mcolors.YELLOW)
        self.add(title_mobj)

        # Create visual elements for the legacy of the movement
        non_violence_icon = VGroup(
            Circle(radius=0.5, color=mcolors.WHITE, stroke_width=2),
            Text("Non-Violence", font_size=24).next_to(ORIGIN, DOWN, buff=0.5)
        )
        mass_mobilization_icon = VGroup(
            Square(side_length=1.0, color=mcolors.WHITE, stroke_width=2),
            Text("Mass Mobilization", font_size=24).next_to(ORIGIN, DOWN, buff=0.5)
        )
        self_reliance_icon = VGroup(
            Polygon([0, 0.5, 0], [0.5, -0.5, 0], [-0.5, -0.5, 0], color=mcolors.WHITE, stroke_width=2),
            Text("Self-Reliance", font_size=24).next_to(ORIGIN, DOWN, buff=0.5)
        )
        independence_icon = VGroup(
            Star(n=5, outer_radius=0.5, color=mcolors.WHITE, stroke_width=2),
            Text("Independence", font_size=24).next_to(ORIGIN, DOWN, buff=0.5)
        )

        # Arrange icons in a grid
        icons = VGroup(non_violence_icon, mass_mobilization_icon, self_reliance_icon, independence_icon)
        icons.arrange_in_grid(rows=2, cols=2, buff=(1.0, 1.0))
        icons.move_to(get_zone_center("MAIN_CONTENT_AREA"))

        # Narration and animation - Sequential TTS processing
        narration_chunks = [
            "Despite its suspension, the Non-Cooperation Movement left a lasting legacy.",
            "It demonstrated the power of non-violent resistance and mass mobilization, inspiring future movements for Indian independence.",
            "The movement also highlighted the importance of self-reliance and the promotion of Indian culture and industries.",
            "It paved the way for further civil disobedience campaigns, ultimately contributing to India's independence in 1947."
        ]

        for i, chunk in enumerate(narration_chunks):
            with self.voiceover(text=chunk) as tracker:
                if i == 0:
                    self.play(Create(icons), run_time=tracker.duration)
                else:
                    self.play(Indicate(icons[i-1]), run_time=tracker.duration)
            self.wait(0.5)

        # Final emphasis
        with self.voiceover(text="ultimately contributing to India's independence in 1947.") as tracker:
            self.play(Circumscribe(independence_icon), run_time=tracker.duration)

        self.wait(2)


class AsyncScene5Legacy(AsyncVoiceoverScene):
    """
    Async version of Scene 5: All TTS calls preprocessed in parallel,
    then audio files reused during animation rendering.
    """
    
    def construct(self):
        """Regular construct method - audio files are already generated and cached"""
        
        # Create the title
        title_mobj = create_smart_text("Legacy of the Movement", zone_name="TITLE_AREA", font_size=48, color=mcolors.YELLOW)
        self.add(title_mobj)

        # Create visual elements for the legacy of the movement
        non_violence_icon = VGroup(
            Circle(radius=0.5, color=mcolors.WHITE, stroke_width=2),
            Text("Non-Violence", font_size=24).next_to(ORIGIN, DOWN, buff=0.5)
        )
        mass_mobilization_icon = VGroup(
            Square(side_length=1.0, color=mcolors.WHITE, stroke_width=2),
            Text("Mass Mobilization", font_size=24).next_to(ORIGIN, DOWN, buff=0.5)
        )
        self_reliance_icon = VGroup(
            Polygon([0, 0.5, 0], [0.5, -0.5, 0], [-0.5, -0.5, 0], color=mcolors.WHITE, stroke_width=2),
            Text("Self-Reliance", font_size=24).next_to(ORIGIN, DOWN, buff=0.5)
        )
        independence_icon = VGroup(
            Star(n=5, outer_radius=0.5, color=mcolors.WHITE, stroke_width=2),
            Text("Independence", font_size=24).next_to(ORIGIN, DOWN, buff=0.5)
        )

        # Arrange icons in a grid
        icons = VGroup(non_violence_icon, mass_mobilization_icon, self_reliance_icon, independence_icon)
        icons.arrange_in_grid(rows=2, cols=2, buff=(1.0, 1.0))
        icons.move_to(get_zone_center("MAIN_CONTENT_AREA"))

        # Use preprocessed voiceover segments (audio files already ready!)
        with self.voiceover(segment_index=0) as tracker:
            self.play(Create(icons), run_time=tracker.duration)
        self.wait(0.5)

        with self.voiceover(segment_index=1) as tracker:
            self.play(Indicate(icons[0]), run_time=tracker.duration)
        self.wait(0.5)

        with self.voiceover(segment_index=2) as tracker:
            self.play(Indicate(icons[1]), run_time=tracker.duration)
        self.wait(0.5)

        with self.voiceover(segment_index=3) as tracker:
            self.play(Indicate(icons[2]), run_time=tracker.duration)
        self.wait(0.5)

        # Final emphasis
        with self.voiceover(segment_index=4) as tracker:
            self.play(Circumscribe(independence_icon), run_time=tracker.duration)

        self.wait(2)


def benchmark_scene5(scene_class, scene_name, is_async=False):
    """
    Benchmark Scene 5 and return the rendering time.
    
    Args:
        scene_class: The scene class to benchmark
        scene_name: Name for output files and logging
        is_async: Whether this scene requires async preprocessing
        
    Returns:
        float: Total time taken to render the scene
    """
    print(f"\n{'='*60}")
    print(f"🎬 Benchmarking Scene 5: {scene_name}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        if is_async:
            # Handle async preprocessing for AsyncScene5Legacy
            print("⏳ Running async preprocessing for Scene 5...")
            preprocessing_start = time.time()
            
            # Create scene instance and run async preprocessing
            scene = scene_class()
            
            # Import the utility function to handle async preprocessing
            from async_voiceover_scene import preprocess_scene_voiceovers
            
            # Set up the speech service first
            scene.set_speech_service(
                AsyncDeepInfraService(
                    voice="af_bella",
                    model="hexgrad/Kokoro-82M",
                    api_key=os.getenv("DEEPINFRA_API_KEY"),
                    max_concurrent_requests=5,
                    max_requests_per_second=3.0,
                    transcription_model=None
                )
            )
            
            # Register all voiceover segments from Scene 5
            scene.register_voiceover("Despite its suspension, the Non-Cooperation Movement left a lasting legacy.")
            scene.register_voiceover("It demonstrated the power of non-violent resistance and mass mobilization, inspiring future movements for Indian independence.")
            scene.register_voiceover("The movement also highlighted the importance of self-reliance and the promotion of Indian culture and industries.")
            scene.register_voiceover("It paved the way for further civil disobedience campaigns, ultimately contributing to India's independence in 1947.")
            scene.register_voiceover("ultimately contributing to India's independence in 1947.")
            
            # Run preprocessing
            preprocess_scene_voiceovers(scene)
            
            preprocessing_time = time.time() - preprocessing_start
            print(f"⚡ Preprocessing completed in {preprocessing_time:.2f} seconds")
            
            # Now render the actual animation
            print("🎥 Rendering Scene 5 animation...")
            render_start = time.time()
            
            # Configure output
            config.output_file = f"scene5_{scene_name.lower().replace(' ', '_')}"
            scene.render()
            
            render_time = time.time() - render_start
            total_time = time.time() - start_time
            
            print(f"📊 Preprocessing time: {preprocessing_time:.2f}s")
            print(f"📊 Rendering time: {render_time:.2f}s")
            print(f"📊 Total time: {total_time:.2f}s")
            
        else:
            # Handle regular synchronous scene
            print("🎥 Rendering Scene 5 with sequential TTS...")
            
            # Configure output
            config.output_file = f"scene5_{scene_name.lower().replace(' ', '_')}"
            
            # Render the scene
            scene = scene_class()
            scene.render()
            
            total_time = time.time() - start_time
            print(f"📊 Total time: {total_time:.2f}s")
        
        print(f"✅ Scene 5 {scene_name} completed successfully!")
        return total_time
        
    except Exception as e:
        print(f"❌ Error rendering Scene 5 {scene_name}: {str(e)}")
        import traceback
        traceback.print_exc()
        return float('inf')  # Return infinity to indicate failure


def run_scene5_performance_comparison():
    """
    Run the complete performance comparison for Scene 5 between sequential and async TTS approaches.
    """
    print("🏁 Scene 5 TTS Performance Benchmark Starting...")
    print("Comparing Sequential vs Async TTS preprocessing approaches for Production Scene 5")
    print("Scene: Legacy of the Non-Cooperation Movement")
    
    # Check for API key
    if not os.getenv("DEEPINFRA_API_KEY"):
        print("❌ DEEPINFRA_API_KEY environment variable not set!")
        print("Please set your DeepInfra API key and try again.")
        return
    
    # Set up manim configuration for consistent comparison
    config.pixel_height = 720
    config.pixel_width = 1280
    config.frame_rate = 30
    config.preview = False  # Don't open preview windows
    config.verbosity = "WARNING"  # Reduce manim log verbosity
    
    # Ensure output directory exists
    output_dir = Path("scene5_benchmark_output")
    output_dir.mkdir(exist_ok=True)
    config.output_dir = str(output_dir)
    
    print(f"📁 Output directory: {output_dir.absolute()}")
    
    # Run benchmarks
    results = {}
    
    # Benchmark 1: Sequential TTS (traditional approach)
    results['sequential'] = benchmark_scene5(
        SequentialScene5Legacy, 
        "Sequential Legacy Scene", 
        is_async=False
    )
    
    # Small pause between benchmarks
    time.sleep(2)
    
    # Benchmark 2: Async TTS (preprocessing approach)
    results['async'] = benchmark_scene5(
        AsyncScene5Legacy, 
        "Async Legacy Scene", 
        is_async=True
    )
    
    # Calculate and display results
    print_scene5_performance_summary(results)


def print_scene5_performance_summary(results):
    """Print a detailed performance comparison summary for Scene 5."""
    
    print(f"\n{'='*80}")
    print(f"🏆 SCENE 5 PERFORMANCE COMPARISON RESULTS")
    print(f"📚 Production Scene: Legacy of the Non-Cooperation Movement")
    print(f"{'='*80}")
    
    sequential_time = results.get('sequential', float('inf'))
    async_time = results.get('async', float('inf'))
    
    if sequential_time == float('inf') or async_time == float('inf'):
        print("❌ One or both benchmarks failed to complete.")
        return
    
    # Calculate speedup
    speedup = sequential_time / async_time if async_time > 0 else 0
    time_saved = sequential_time - async_time
    percent_improvement = ((sequential_time - async_time) / sequential_time) * 100
    
    print(f"📊 Sequential TTS Time:  {sequential_time:.2f} seconds")
    print(f"📊 Async TTS Time:       {async_time:.2f} seconds")
    print(f"📊 Time Saved:          {time_saved:.2f} seconds")
    print(f"📊 Speedup Factor:      {speedup:.2f}x")
    print(f"📊 Performance Gain:    {percent_improvement:.1f}%")
    
    # Scene-specific analysis
    voiceover_count = 5
    avg_time_per_voiceover_sequential = sequential_time / voiceover_count
    avg_time_per_voiceover_async = async_time / voiceover_count
    
    print(f"\n📈 SCENE 5 SPECIFIC METRICS:")
    print(f"📊 Total Voiceover Segments: {voiceover_count}")
    print(f"📊 Avg Time/Segment (Sequential): {avg_time_per_voiceover_sequential:.2f}s")
    print(f"📊 Avg Time/Segment (Async): {avg_time_per_voiceover_async:.2f}s")
    
    print(f"\n💡 PRODUCTION IMPACT ANALYSIS:")
    if speedup > 2.0:
        print(f"🚀 OUTSTANDING! {speedup:.1f}x speedup on production Scene 5!")
        print(f"   This demonstrates significant real-world benefits for complex scenes")
        print(f"   Estimated time savings for full episode: {time_saved * 10:.1f}+ seconds")
    elif speedup > 1.5:
        print(f"✅ EXCELLENT! {speedup:.1f}x speedup on production content")
        print(f"   Clear performance advantage for production workflows")
    elif speedup > 1.2:
        print(f"📈 GOOD! Measurable {speedup:.1f}x improvement on real scene")
        print(f"   Benefits scale with longer episodes and more voiceovers")
    else:
        print(f"⚠️  LIMITED: Only {speedup:.1f}x speedup observed")
        print(f"   Network conditions or scene complexity may affect results")
    
    print(f"\n🎯 PRODUCTION RECOMMENDATIONS:")
    if speedup > 1.3:
        print(f"   ✅ RECOMMENDED: Switch to async preprocessing for production")
        print(f"   ✅ Implement parallel TTS processing in your workflow")
        print(f"   ✅ Expected time savings will increase with episode length")
    else:
        print(f"   ⚠️  Consider async approach for longer episodes only")
        print(f"   ⚠️  Monitor network latency impact on sequential processing")
    
    print(f"\n📁 Output files generated in: scene5_benchmark_output/")
    print(f"   • scene5_sequential_legacy_scene.mp4 (traditional approach)")
    print(f"   • scene5_async_legacy_scene.mp4 (parallel preprocessing approach)")
    
    print(f"\n{'='*80}")


if __name__ == "__main__":
    print("""
    ███████╗ ██████╗███████╗███╗   ██╗███████╗    ███████╗
    ██╔════╝██╔════╝██╔════╝████╗  ██║██╔════╝    ██╔════╝
    ███████╗██║     █████╗  ██╔██╗ ██║█████╗      ███████╗
    ╚════██║██║     ██╔══╝  ██║╚██╗██║██╔══╝      ╚════██║
    ███████║╚██████╗███████╗██║ ╚████║███████╗    ███████║
    ╚══════╝ ╚═════╝╚══════╝╚═╝  ╚═══╝╚══════╝    ╚══════╝
                                                           
    ████████╗████████╗███████╗    ██████╗ ███████╗███╗   ██╗ ██████╗██╗  ██╗
    ╚══██╔══╝╚══██╔══╝██╔════╝    ██╔══██╗██╔════╝████╗  ██║██╔════╝██║  ██║
       ██║      ██║   ███████╗    ██████╔╝█████╗  ██╔██╗ ██║██║     ███████║
       ██║      ██║   ╚════██║    ██╔══██╗██╔══╝  ██║╚██╗██║██║     ██╔══██║
       ██║      ██║   ███████║    ██████╔╝███████╗██║ ╚████║╚██████╗██║  ██║
       ╚═╝      ╚═╝   ╚══════╝    ╚═════╝ ╚══════╝╚═╝  ╚═══╝ ╚═════╝╚═╝  ╚═╝
                                                                              
    Production Scene 5: Legacy of the Movement - TTS Performance Analysis
    """)
    
    run_scene5_performance_comparison() 