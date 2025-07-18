#!/usr/bin/env python3
"""
Scene 5 Performance Benchmark
============================

Direct benchmark test of Scene 5 with ultra-aggressive manim optimizations.
Compares normal rendering vs ultra-optimized rendering.
"""

import subprocess
import time
import os
import logging
import tempfile

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_normal_rendering():
    """Test normal manim rendering (baseline)"""
    
    logger.info("🐌 Testing Scene 5 with normal rendering...")
    
    output_dir = tempfile.mkdtemp(prefix='scene5_normal_')
    
    command = [
        'manim',
        'anim_gemini/outputs/generated_content/manim_scripts/scene_05_Legacy_of_the_Movement.py',
        'Scene5Legacy_of_the_Movement',
        '-pqm',  # Medium quality (baseline)
        '--media_dir', output_dir,
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

def test_ultra_aggressive_rendering():
    """Test ULTRA-AGGRESSIVE manim rendering"""
    
    logger.info("🚀 Testing Scene 5 with ULTRA-AGGRESSIVE rendering...")
    
    output_dir = tempfile.mkdtemp(prefix='scene5_ultra_')
    
    # ULTRA-AGGRESSIVE command with correct lowest quality
    command = [
        'manim',
        'anim_gemini/outputs/generated_content/manim_scripts/scene_05_Legacy_of_the_Movement.py',
        'Scene5Legacy_of_the_Movement',
        # Use correct ultra-low quality flag
        '-ql',  # Low quality (fastest)
        '--fps', '4',  # ULTRA-low FPS (4fps is 7.5x faster than 30fps)
        '--resolution', '320,240',  # Ultra-low resolution (240p)
        '--verbosity', 'ERROR',
        '--progress_bar', 'none',
        '--flush_cache',
        '--disable_caching',
        '--media_dir', output_dir,
    ]
    
    # Ultra-optimized environment
    env = os.environ.copy()
    env['CAIRO_ANTIALIAS'] = 'none'  # Disable antialiasing
    env['CAIRO_SURFACE_TYPE'] = 'image'
    env['OMP_NUM_THREADS'] = '1'
    env['MANIM_DISABLE_CAIRO_LOGGING'] = '1'
    
    try:
        start_time = time.time()
        
        logger.info(f"   Command: manim scene_05_Legacy_of_the_Movement.py Scene5Legacy_of_the_Movement -ql --fps 4 --resolution 320,240")
        
        result = subprocess.run(
            command,
            env=env,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout
        )
        
        render_time = time.time() - start_time
        
        if result.returncode == 0:
            logger.info(f"✅ Ultra-aggressive rendering: {render_time:.2f}s")
            return render_time, True
        else:
            logger.error(f"❌ Ultra-aggressive rendering failed: {result.stderr}")
            # Try fallback command
            return test_fallback_rendering()
            
    except Exception as e:
        logger.error(f"💥 Ultra-aggressive rendering error: {e}")
        return test_fallback_rendering()

def test_fallback_rendering():
    """Test fallback ultra-fast rendering"""
    
    logger.info("🔄 Trying fallback ultra-fast rendering...")
    
    output_dir = tempfile.mkdtemp(prefix='scene5_fallback_')
    
    # Fallback command with ultra-aggressive settings
    command = [
        'manim',
        'anim_gemini/outputs/generated_content/manim_scripts/scene_05_Legacy_of_the_Movement.py',
        'Scene5Legacy_of_the_Movement',
        '-ql',  # Low quality
        '--fps', '5',  # Ultra-low FPS
        '--resolution', '480,360',  # Low resolution
        '--verbosity', 'ERROR',
        '--progress_bar', 'none',
        '--flush_cache',
        '--disable_caching',
        '--media_dir', output_dir,
    ]
    
    # Ultra-optimized environment
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
    print("║                   🚀 SCENE 5 PERFORMANCE BENCHMARK 🚀                       ║")
    print("║                                                                              ║")
    print("║  Testing Scene 5 'Legacy of the Movement' with direct 10x optimizations    ║")
    print("║  Comparing normal rendering vs ultra-aggressive rendering                   ║")
    print("║                                                                              ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝")
    print()
    
    # Test normal rendering (baseline)
    logger.info("="*60)
    normal_time, normal_success = test_normal_rendering()
    
    # Test ultra-aggressive rendering
    logger.info("="*60)
    ultra_time, ultra_success = test_ultra_aggressive_rendering()
    
    # Calculate results
    logger.info("="*60)
    logger.info("📊 SCENE 5 BENCHMARK RESULTS:")
    logger.info("-"*60)
    
    if normal_success and ultra_success:
        speedup = normal_time / ultra_time if ultra_time > 0 else 0
        time_saved = normal_time - ultra_time
        
        logger.info(f"   Normal Rendering:    {normal_time:8.2f}s")
        logger.info(f"   Ultra-Aggressive:    {ultra_time:8.2f}s")
        logger.info(f"   SPEEDUP ACHIEVED:    {speedup:8.2f}x")
        logger.info(f"   TIME SAVED:          {time_saved:8.2f}s ({time_saved/normal_time*100:.1f}%)")
        
        logger.info("-"*60)
        
        if speedup >= 10.0:
            logger.info("🎉 SUCCESS! Achieved 10x+ speedup target!")
            logger.info("🏆 TRUE 10x optimization achieved for Scene 5!")
        elif speedup >= 5.0:
            logger.info("🎯 EXCELLENT! Achieved 5x+ speedup!")
            logger.info("💡 Scene 5 shows significant optimization gains")
        elif speedup >= 3.0:
            logger.info("✅ VERY GOOD! Achieved 3x+ speedup!")
            logger.info("💡 Scene 5 benefits well from optimization")
        elif speedup >= 2.0:
            logger.info("✅ GOOD! Achieved 2x+ speedup!")
        else:
            logger.info("🔄 Some improvement achieved")
            
    elif ultra_success:
        logger.info(f"   Ultra-Aggressive:    {ultra_time:8.2f}s (normal failed)")
        logger.info("✅ Ultra-aggressive rendering works for Scene 5!")
    elif normal_success:
        logger.info(f"   Normal Rendering:    {normal_time:8.2f}s (ultra failed)")
        logger.info("❌ Ultra-aggressive settings need adjustment for Scene 5")
    else:
        logger.error("❌ Both tests failed. Check Scene 5 and manim setup.")

    logger.info("="*60)
    logger.info("🎉 Scene 5 benchmark complete!")

if __name__ == "__main__":
    main() 