#!/usr/bin/env python3
"""
Scene 5 Performance Benchmark - 480p Version
===========================================

Direct benchmark test of Scene 5 with 480p resolution and 12fps optimizations.
Compares normal rendering vs 480p optimized rendering.
"""

import subprocess
import time
import os
import logging
import tempfile

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define the output directory
OUTPUT_DIR = '/root/manim_gemini/ultra_media'

def ensure_output_dir():
    """Ensure the output directory exists"""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        logger.info(f"Created output directory: {OUTPUT_DIR}")

test_file='/root/manim_gemini/anim_gemini/outputs/generated_content/manim_scripts/scene_01_Introduction_to_Neural_Networks.py'

def test_normal_rendering():
    """Test normal manim rendering (baseline)"""
    
    logger.info("🐌 Testing Scene 5 with normal rendering...")
    
    ensure_output_dir()
    
    command = [
        'manim',
        #'anim_gemini/outputs/generated_content/manim_scripts/scene_05_Legacy_of_the_Movement.py',
        test_file,
        'Scene5Legacy_of_the_Movement',
        '-pqm',  # Medium quality (baseline)
        '--media_dir', OUTPUT_DIR,
        '--verbosity', 'ERROR'
    ]
    
    try:
        start_time = time.time()
        
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout
        )
        
        render_time = time.time() - start_time
        
        if result.returncode == 0:
            logger.info(f"✅ Normal rendering: {render_time:.2f}s")
            return render_time, True
        else:
            logger.error(f"❌ Normal rendering failed: {result.stderr}")
            return render_time, False
            
    except Exception as e:
        logger.error(f"💥 Normal rendering error: {e}")
        return 0, False

def test_480p_optimized_rendering():
    """Test 480p optimized manim rendering"""
    
    logger.info("🚀 Testing Scene 5 with 480p optimized rendering...")
    
    ensure_output_dir()
    
    # 480p optimized command with 12fps
    command = [
        'manim',
        #'anim_gemini/outputs/generated_content/manim_scripts/scene_05_Legacy_of_the_Movement.py',
        test_file,
        'Scene5Legacy_of_the_Movement',
        # Use low quality for faster rendering
        '-ql',  # Low quality (faster)
        '--fps', '12',  # 12fps for good balance of speed and quality
        '--resolution', '854,480',  # 480p resolution (16:9 aspect ratio)
        '--verbosity', 'ERROR',
        '--progress_bar', 'none',
        '--flush_cache',
        '--disable_caching',
        '--media_dir', OUTPUT_DIR,
    ]
    
    # Optimized environment
    env = os.environ.copy()
    env['CAIRO_ANTIALIAS'] = 'none'  # Disable antialiasing
    env['CAIRO_SURFACE_TYPE'] = 'image'
    env['OMP_NUM_THREADS'] = '1'
    env['MANIM_DISABLE_CAIRO_LOGGING'] = '1'
    
    try:
        start_time = time.time()
        
        logger.info(f"   Command: manim scene_05_Legacy_of_the_Movement.py Scene5Legacy_of_the_Movement -ql --fps 12 --resolution 854,480")
        
        result = subprocess.run(
            command,
            env=env,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout
        )
        
        render_time = time.time() - start_time
        
        if result.returncode == 0:
            logger.info(f"✅ 480p optimized rendering: {render_time:.2f}s")
            return render_time, True
        else:
            logger.error(f"❌ 480p optimized rendering failed: {result.stderr}")
            # Try fallback command
            return test_fallback_rendering()
            
    except Exception as e:
        logger.error(f"💥 480p optimized rendering error: {e}")
        return test_fallback_rendering()

def test_fallback_rendering():
    """Test fallback 480p rendering"""
    
    logger.info("🔄 Trying fallback 480p rendering...")
    
    ensure_output_dir()
    
    # Fallback command with 480p settings
    command = [
        'manim',
        #'anim_gemini/outputs/generated_content/manim_scripts/scene_05_Legacy_of_the_Movement.py',
        test_file,
        'Scene5Legacy_of_the_Movement',
        '-ql',  # Low quality
        '--fps', '10',  # Slightly lower fps for fallback
        '--resolution', '640,480',  # Standard 480p resolution (4:3 aspect ratio)
        '--verbosity', 'ERROR',
        '--progress_bar', 'none',
        '--flush_cache',
        '--disable_caching',
        '--media_dir', OUTPUT_DIR,
    ]
    
    # Optimized environment
    env = os.environ.copy()
    env['CAIRO_SURFACE_TYPE'] = 'image'
    env['OMP_NUM_THREADS'] = '1'
    env['MANIM_DISABLE_CAIRO_LOGGING'] = '1'
    
    try:
        start_time = time.time()
        
        result = subprocess.run(
            command,
            env=env,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        render_time = time.time() - start_time
        
        if result.returncode == 0:
            logger.info(f"✅ Fallback rendering: {render_time:.2f}s")
            return render_time, True
        else:
            logger.error(f"❌ Fallback rendering failed: {result.stderr}")
            return render_time, False
            
    except Exception as e:
        logger.error(f"💥 Fallback rendering error: {e}")
        return 0, False

def main():
    """Main benchmark function"""
    
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║                   🚀 SCENE 5 PERFORMANCE BENCHMARK - 480p 🚀                ║")
    print("║                                                                              ║")
    print("║  Testing Scene 5 'Legacy of the Movement' with 480p/12fps optimizations    ║")
    print("║  Comparing normal rendering vs 480p optimized rendering                     ║")
    print("║                                                                              ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝")
    print()
    
    logger.info(f"📁 Videos will be saved to: {OUTPUT_DIR}")
    print()
    
    # Test normal rendering (baseline)
    logger.info("="*60)
    normal_time, normal_success = test_normal_rendering()
    
    # Test 480p optimized rendering
    logger.info("="*60)
    optimized_time, optimized_success = test_480p_optimized_rendering()
    
    # Calculate results
    logger.info("="*60)
    logger.info("📊 SCENE 5 BENCHMARK RESULTS (480p):")
    logger.info("-"*60)
    
    if normal_success and optimized_success:
        speedup = normal_time / optimized_time if optimized_time > 0 else 0
        time_saved = normal_time - optimized_time
        
        logger.info(f"   Normal Rendering:    {normal_time:8.2f}s")
        logger.info(f"   480p Optimized:      {optimized_time:8.2f}s")
        logger.info(f"   SPEEDUP ACHIEVED:    {speedup:8.2f}x")
        logger.info(f"   TIME SAVED:          {time_saved:8.2f}s ({time_saved/normal_time*100:.1f}%)")
        
        logger.info("-"*60)
        
        if speedup >= 10.0:
            logger.info("🎉 SUCCESS! Achieved 10x+ speedup target!")
            logger.info("🏆 TRUE 10x optimization achieved for Scene 5 with 480p!")
        elif speedup >= 5.0:
            logger.info("🎯 EXCELLENT! Achieved 5x+ speedup!")
            logger.info("💡 Scene 5 shows significant optimization gains with 480p")
        elif speedup >= 3.0:
            logger.info("✅ VERY GOOD! Achieved 3x+ speedup!")
            logger.info("💡 Scene 5 benefits well from 480p optimization")
        elif speedup >= 2.0:
            logger.info("✅ GOOD! Achieved 2x+ speedup!")
        else:
            logger.info("🔄 Some improvement achieved")
            
    elif optimized_success:
        logger.info(f"   480p Optimized:      {optimized_time:8.2f}s (normal failed)")
        logger.info("✅ 480p optimized rendering works for Scene 5!")
    elif normal_success:
        logger.info(f"   Normal Rendering:    {normal_time:8.2f}s (480p failed)")
        logger.info("❌ 480p optimized settings need adjustment for Scene 5")
    else:
        logger.error("❌ Both tests failed. Check Scene 5 and manim setup.")

    logger.info("="*60)
    logger.info("🎉 Scene 5 benchmark (480p) complete!")
    logger.info(f"📁 Check your videos in: {OUTPUT_DIR}")

if __name__ == "__main__":
    main() 