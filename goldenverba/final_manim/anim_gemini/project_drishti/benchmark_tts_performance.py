#!/usr/bin/env python3
"""
TTS Performance Benchmark: Sequential vs Async Preprocessing

This script demonstrates the performance difference between:
1. Sequential TTS calls scattered throughout animation code (traditional approach)
2. Async preprocessing where all TTS calls are made upfront in parallel

Usage:
    python benchmark_tts_performance.py

The script will render both versions and show the time difference.
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


class SequentialTTSScene(VoiceoverScene):
    """
    Traditional approach: TTS calls made sequentially during animation rendering.
    Each voiceover text is processed one by one as the animation progresses.
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
        
        # Create some visual elements
        title = Text("Sequential TTS Demo", font_size=48, color=BLUE)
        self.play(Write(title))
        
        # Sequential voiceover calls - each one blocks until TTS is complete
        with self.voiceover(text="Welcome to our sequential TTS demonstration.") as tracker:
            self.play(title.animate.scale(0.8).to_edge(UP))
        
        # Create and animate some geometric shapes
        circle = Circle(radius=1, color=RED)
        self.play(Create(circle))
        
        with self.voiceover(text="Here we see a red circle being created on screen.") as tracker:
            self.play(circle.animate.set_color(GREEN))
        
        # Add a square
        square = Square(side_length=1.5, color=YELLOW).next_to(circle, RIGHT, buff=1)
        self.play(Create(square))
        
        with self.voiceover(text="Now we add a yellow square next to our circle.") as tracker:
            self.play(square.animate.rotate(PI/4))
        
        # Add mathematical content
        equation = MathTex(r"E = mc^2", font_size=72).next_to(square, RIGHT, buff=1)
        self.play(Write(equation))
        
        with self.voiceover(text="Einstein's famous mass-energy equivalence formula represents one of the most important discoveries in physics.") as tracker:
            self.play(equation.animate.set_color(PURPLE))
        
        # Final transformation
        group = VGroup(circle, square, equation)
        
        with self.voiceover(text="Let's arrange all our elements in a beautiful final composition.") as tracker:
            self.play(group.animate.arrange(RIGHT, buff=0.5).center())
            self.play(group.animate.scale(0.7))
        
        # Conclusion
        conclusion = Text("Sequential Processing Complete!", font_size=36, color=GREEN)
        conclusion.to_edge(DOWN)
        
        with self.voiceover(text="This concludes our sequential TTS demonstration. Each voiceover was processed one at a time.") as tracker:
            self.play(Write(conclusion))
            self.play(FadeOut(group), FadeOut(title))


class AsyncTTSScene(AsyncVoiceoverScene):
    """
    Async preprocessing approach: All TTS calls made upfront in parallel,
    then audio files are reused during animation rendering.
    """
    
    def construct(self):
        """Regular construct method - audio files are already generated and cached"""
        # Create some visual elements (identical to sequential version)
        title = Text("Async TTS Demo", font_size=48, color=BLUE)
        self.play(Write(title))
        
        # Use preprocessed voiceover - audio file is already ready!
        with self.voiceover(segment_index=0) as tracker:
            self.play(title.animate.scale(0.8).to_edge(UP))
        
        # Create and animate some geometric shapes
        circle = Circle(radius=1, color=RED)
        self.play(Create(circle))
        
        with self.voiceover(segment_index=1) as tracker:
            self.play(circle.animate.set_color(GREEN))
        
        # Add a square
        square = Square(side_length=1.5, color=YELLOW).next_to(circle, RIGHT, buff=1)
        self.play(Create(square))
        
        with self.voiceover(segment_index=2) as tracker:
            self.play(square.animate.rotate(PI/4))
        
        # Add mathematical content
        equation = MathTex(r"E = mc^2", font_size=72).next_to(square, RIGHT, buff=1)
        self.play(Write(equation))
        
        with self.voiceover(segment_index=3) as tracker:
            self.play(equation.animate.set_color(PURPLE))
        
        # Final transformation
        group = VGroup(circle, square, equation)
        
        with self.voiceover(segment_index=4) as tracker:
            self.play(group.animate.arrange(RIGHT, buff=0.5).center())
            self.play(group.animate.scale(0.7))
        
        # Conclusion
        conclusion = Text("Async Processing Complete!", font_size=36, color=GREEN)
        conclusion.to_edge(DOWN)
        
        with self.voiceover(segment_index=5) as tracker:
            self.play(Write(conclusion))
            self.play(FadeOut(group), FadeOut(title))


def benchmark_scene(scene_class, scene_name, is_async=False):
    """
    Benchmark a single scene and return the rendering time.
    
    Args:
        scene_class: The scene class to benchmark
        scene_name: Name for output files and logging
        is_async: Whether this scene requires async preprocessing
        
    Returns:
        float: Total time taken to render the scene
    """
    print(f"\n{'='*60}")
    print(f"🎬 Benchmarking: {scene_name}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        if is_async:
            # Handle async preprocessing for AsyncTTSScene
            print("⏳ Running async preprocessing...")
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
            
            # Register all voiceover segments
            scene.register_voiceover("Welcome to our asynchronous TTS demonstration.")
            scene.register_voiceover("Here we see a red circle being created on screen.")
            scene.register_voiceover("Now we add a yellow square next to our circle.")
            scene.register_voiceover("Einstein's famous mass-energy equivalence formula represents one of the most important discoveries in physics.")
            scene.register_voiceover("Let's arrange all our elements in a beautiful final composition.")
            scene.register_voiceover("This concludes our async TTS demonstration. All voiceovers were processed in parallel at the beginning.")
            
            # Run preprocessing
            preprocess_scene_voiceovers(scene)
            
            preprocessing_time = time.time() - preprocessing_start
            print(f"⚡ Preprocessing completed in {preprocessing_time:.2f} seconds")
            
            # Now render the actual animation
            print("🎥 Rendering animation...")
            render_start = time.time()
            
            # Configure output
            config.output_file = f"{scene_name.lower().replace(' ', '_')}"
            scene.render()
            
            render_time = time.time() - render_start
            total_time = time.time() - start_time
            
            print(f"📊 Preprocessing time: {preprocessing_time:.2f}s")
            print(f"📊 Rendering time: {render_time:.2f}s")
            print(f"📊 Total time: {total_time:.2f}s")
            
        else:
            # Handle regular synchronous scene
            print("🎥 Rendering with sequential TTS...")
            
            # Configure output
            config.output_file = f"{scene_name.lower().replace(' ', '_')}"
            
            # Render the scene
            scene = scene_class()
            scene.render()
            
            total_time = time.time() - start_time
            print(f"📊 Total time: {total_time:.2f}s")
        
        print(f"✅ {scene_name} completed successfully!")
        return total_time
        
    except Exception as e:
        print(f"❌ Error rendering {scene_name}: {str(e)}")
        return float('inf')  # Return infinity to indicate failure


def run_performance_comparison():
    """
    Run the complete performance comparison between sequential and async TTS approaches.
    """
    print("🏁 TTS Performance Benchmark Starting...")
    print("This benchmark compares Sequential vs Async TTS preprocessing approaches")
    
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
    output_dir = Path("benchmark_output")
    output_dir.mkdir(exist_ok=True)
    config.output_dir = str(output_dir)
    
    print(f"📁 Output directory: {output_dir.absolute()}")
    
    # Run benchmarks
    results = {}
    
    # Benchmark 1: Sequential TTS (traditional approach)
    results['sequential'] = benchmark_scene(
        SequentialTTSScene, 
        "Sequential TTS Scene", 
        is_async=False
    )
    
    # Small pause between benchmarks
    time.sleep(2)
    
    # Benchmark 2: Async TTS (preprocessing approach)
    results['async'] = benchmark_scene(
        AsyncTTSScene, 
        "Async TTS Scene", 
        is_async=True
    )
    
    # Calculate and display results
    print_performance_summary(results)


def print_performance_summary(results):
    """Print a detailed performance comparison summary."""
    
    print(f"\n{'='*80}")
    print(f"🏆 PERFORMANCE COMPARISON RESULTS")
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
    
    print(f"\n💡 ANALYSIS:")
    if speedup > 1.5:
        print(f"🚀 EXCELLENT! Async preprocessing is {speedup:.1f}x faster!")
        print(f"   The async approach saved {time_saved:.1f} seconds ({percent_improvement:.1f}% improvement)")
    elif speedup > 1.2:
        print(f"✅ GOOD! Async preprocessing provides a {speedup:.1f}x speedup")
        print(f"   You saved {time_saved:.1f} seconds with parallel TTS processing")
    elif speedup > 1.0:
        print(f"📈 MARGINAL: Small improvement of {speedup:.1f}x speedup")
        print(f"   Benefits will be more significant with more voiceover segments")
    else:
        print(f"⚠️  UNEXPECTED: Sequential was faster or equal performance")
        print(f"   This might indicate network issues or very fast sequential processing")
    
    print(f"\n🎯 KEY INSIGHTS:")
    print(f"   • Sequential approach: TTS calls block animation rendering")
    print(f"   • Async approach: All TTS processed in parallel upfront")
    print(f"   • Speedup increases with more voiceover segments")
    print(f"   • Network latency has major impact on sequential approach")
    
    print(f"\n📁 Output files generated in: benchmark_output/")
    print(f"   • sequential_tts_scene.mp4 (traditional approach)")
    print(f"   • async_tts_scene.mp4 (parallel preprocessing approach)")
    
    print(f"\n{'='*80}")


if __name__ == "__main__":
    print("""
    ████████╗████████╗███████╗    ██████╗ ███████╗███╗   ██╗ ██████╗██╗  ██╗
    ╚══██╔══╝╚══██╔══╝██╔════╝    ██╔══██╗██╔════╝████╗  ██║██╔════╝██║  ██║
       ██║      ██║   ███████╗    ██████╔╝█████╗  ██╔██╗ ██║██║     ███████║
       ██║      ██║   ╚════██║    ██╔══██╗██╔══╝  ██║╚██╗██║██║     ██╔══██║
       ██║      ██║   ███████║    ██████╔╝███████╗██║ ╚████║╚██████╗██║  ██║
       ╚═╝      ╚═╝   ╚══════╝    ╚═════╝ ╚══════╝╚═╝  ╚═══╝ ╚═════╝╚═╝  ╚═╝
                                                                              
    Sequential vs Async TTS Performance Comparison
    """)
    
    run_performance_comparison() 