#!/usr/bin/env python3
"""
Helper script to run the Scene 5 TTS Performance Benchmark

This script sets up the environment and runs the benchmark comparison
between sequential and async TTS approaches for the production Scene 5.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def setup_environment():
    """Set up the environment for running the Scene 5 benchmark."""
    
    print("🔧 Setting up environment for Scene 5 TTS benchmark...")
    
    # Load environment variables from the .env file
    env_path = Path("/root/manim_gemini/.env")
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Loaded environment from: {env_path}")
    else:
        print(f"⚠️  .env file not found at: {env_path}")
        # Try loading from current directory as fallback
        load_dotenv()
    
    # Check if API key is set
    api_key = os.getenv("DEEPINFRA_API_KEY")
    
    if not api_key:
        print("⚠️  DEEPINFRA_API_KEY not found in environment.")
        print("Please check that your API key is properly set in the .env file:")
        print(f"  {env_path}")
        print()
        print("The .env file should contain:")
        print("  DEEPINFRA_API_KEY=your_api_key_here")
        print()
        print("Get your API key from: https://deepinfra.com/")
        return False
    
    print(f"✅ API key found: {api_key[:8]}...")
    
    # Check required dependencies
    try:
        import manim
        import manim_voiceover
        import aiohttp
        import aiofiles
        print("✅ All required dependencies found")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install required packages:")
        print("  pip install manim manim-voiceover aiohttp aiofiles python-dotenv")
        return False
    
    # Check if our custom modules exist
    required_files = [
        "deepinfra_service.py",
        "async_deepinfra_service.py", 
        "async_voiceover_scene.py",
        "benchmark_scene5_tts.py"
    ]
    
    for file in required_files:
        if not Path(file).exists():
            print(f"❌ Required file not found: {file}")
            return False
    
    print("✅ All required files found")
    
    # Check if Scene 5 source file exists
    scene5_path = Path("../outputs/generated_content/manim_scripts/scene_05_Legacy_of_the_Movement.py")
    if scene5_path.exists():
        print(f"✅ Found original Scene 5 script: {scene5_path}")
    else:
        print(f"⚠️  Original Scene 5 script not found at: {scene5_path}")
        print("Benchmark will use embedded Scene 5 structure")
    
    return True

def main():
    """Main function to run the Scene 5 benchmark."""
    
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                     Scene 5 TTS Performance Benchmark                       ║
║              Production Scene: Legacy of the Movement                       ║
║                    Sequential vs Async Preprocessing                        ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Setup environment
    if not setup_environment():
        print("\n❌ Environment setup failed. Please fix the issues above and try again.")
        sys.exit(1)
    
    print("\n🚀 Starting Scene 5 TTS Performance Benchmark...")
    print("This will test your actual production scene with two TTS approaches:")
    print("  1. Sequential TTS: Each voiceover processed one by one (current production)")
    print("  2. Async TTS: All voiceovers processed in parallel upfront (optimized)")
    print()
    print("📚 Scene Details:")
    print("  • Title: Legacy of the Non-Cooperation Movement")
    print("  • Voiceover segments: 5 narration chunks")
    print("  • Visual elements: Icons for historical concepts")
    print("  • Animation complexity: Medium (icons, text, animations)")
    print()
    
    # Import and run the benchmark
    try:
        from benchmark_scene5_tts import run_scene5_performance_comparison
        run_scene5_performance_comparison()
        
    except Exception as e:
        print(f"❌ Scene 5 benchmark failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 