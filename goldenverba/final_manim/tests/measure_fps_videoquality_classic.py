#!/usr/bin/env python3
"""
FPS & Video Quality Performance Benchmark
=========================================

Comprehensive benchmark for educational content rendering optimization.
Tests different resolution and frame rate combinations to find the optimal
balance between quality and rendering speed for MVP demonstrations.

Configurations tested:
- 480p @ 12fps (Ultra Fast)
- 480p @ 24fps (Fast)  
- 720p @ 12fps (Balanced)
- 720p @ 24fps (Quality)
- 720p @ 30fps (Premium)
"""

import subprocess
import time
import os
import logging
import json
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
OUTPUT_DIR = '/root/manim_gemini/ultra_media'
RESULTS_FILE = 'benchmark_results.json'

# Test file - you can change this to any scene you want to benchmark
TEST_FILE = '/root/manim_gemini/anim_gemini/outputs/generated_content/manim_scripts/scene_01_Introduction_to_Neural_Networks.py'
SCENE_CLASS = 'Scene5Legacy_of_the_Movement'  # Update this based on your test scene

# Benchmark configurations
CONFIGS = [
    {
        'name': '480p_12fps_ultra_fast',
        'description': '480p @ 12fps (Ultra Fast - MVP Demo)',
        'resolution': '854,480',
        'fps': '12',
        'quality': '-ql',
        'target_use': 'Live demos, quick previews'
    },
    {
        'name': '480p_15fps_fast',
        'description': '480p @ 15fps (Fast - Student Review)',
        'resolution': '854,480', 
        'fps': '15',
        'quality': '-ql',
        'target_use': 'Student practice sessions'
    },
    {
        'name': '720p_12fps_balanced',
        'description': '720p @ 12fps (Balanced - Class Presentation)',
        'resolution': '1280,720',
        'fps': '12', 
        'quality': '-qm',
        'target_use': 'Classroom presentations'
    },
    {
        'name': '720p_15fps_quality',
        'description': '720p @ 15fps (Quality - Course Content)',
        'resolution': '1280,720',
        'fps': '15',
        'quality': '-qm', 
        'target_use': 'Published course materials'
    },
    {
        'name': '720p_30fps_premium',
        'description': '720p @ 30fps (Premium - Final Export)',
        'resolution': '1280,720',
        'fps': '30',
        'quality': '-qh',
        'target_use': 'Professional course delivery'
    }
]

def ensure_output_dir():
    """Ensure the output directory exists"""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        logger.info(f"Created output directory: {OUTPUT_DIR}")

def render_with_config(config):
    """Render video with specific configuration"""
    
    logger.info(f"🎬 Testing: {config['description']}")
    
    ensure_output_dir()
    
    # Build manim command
    command = [
        'manim',
        TEST_FILE,
        SCENE_CLASS,
        config['quality'],
        '--fps', config['fps'],
        '--resolution', config['resolution'],
        '--verbosity', 'ERROR',
        '--progress_bar', 'none',
        '--flush_cache',
        '--disable_caching',
        '--media_dir', OUTPUT_DIR,
    ]
    
    # Optimized environment for faster rendering
    env = os.environ.copy()
    env['CAIRO_ANTIALIAS'] = 'none'
    env['CAIRO_SURFACE_TYPE'] = 'image'
    env['OMP_NUM_THREADS'] = '2'  # Use 2 threads for balance
    env['MANIM_DISABLE_CAIRO_LOGGING'] = '1'
    
    try:
        start_time = time.time()
        
        logger.info(f"   Command: manim {SCENE_CLASS} {config['quality']} --fps {config['fps']} --resolution {config['resolution']}")
        
        result = subprocess.run(
            command,
            env=env,
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes timeout
        )
        
        render_time = time.time() - start_time
        
        if result.returncode == 0:
            logger.info(f"✅ {config['name']}: {render_time:.2f}s")
            
            # Get file size for quality metrics
            output_pattern = f"{OUTPUT_DIR}/videos/{config['quality'][1:]}/*{SCENE_CLASS}*.mp4"
            import glob
            files = glob.glob(output_pattern)
            file_size_mb = 0
            if files:
                file_size_mb = os.path.getsize(files[0]) / (1024 * 1024)
            
            return {
                'success': True,
                'render_time': render_time,
                'file_size_mb': file_size_mb,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
        else:
            logger.error(f"❌ {config['name']} failed: {result.stderr}")
            return {
                'success': False,
                'render_time': render_time,
                'error': result.stderr
            }
            
    except subprocess.TimeoutExpired:
        logger.error(f"⏰ {config['name']} timed out after 10 minutes")
        return {
            'success': False,
            'render_time': 600,
            'error': 'Timeout after 10 minutes'
        }
    except Exception as e:
        logger.error(f"💥 {config['name']} error: {e}")
        return {
            'success': False,
            'render_time': 0,
            'error': str(e)
        }

def calculate_metrics(results):
    """Calculate performance metrics and recommendations"""
    
    successful_results = {k: v for k, v in results.items() if v['success']}
    
    if not successful_results:
        return None
    
    # Find fastest and best quality options
    fastest = min(successful_results.items(), key=lambda x: x[1]['render_time'])
    
    # Calculate quality score (resolution * fps / render_time)
    quality_scores = {}
    for name, result in successful_results.items():
        config = next(c for c in CONFIGS if c['name'] == name)
        res_width = int(config['resolution'].split(',')[0])
        fps = int(config['fps'])
        quality_score = (res_width * fps) / result['render_time']
        quality_scores[name] = quality_score
    
    best_value = max(quality_scores.items(), key=lambda x: x[1])
    
    return {
        'fastest_config': fastest[0],
        'fastest_time': fastest[1]['render_time'],
        'best_value_config': best_value[0],
        'best_value_score': best_value[1],
        'total_successful': len(successful_results),
        'quality_scores': quality_scores
    }

def generate_recommendations(results, metrics):
    """Generate recommendations for different use cases"""
    
    recommendations = {
        'mvp_demo': None,
        'student_content': None, 
        'classroom_presentation': None,
        'course_publishing': None
    }
    
    successful_results = {k: v for k, v in results.items() if v['success']}
    
    # MVP Demo: Fastest rendering under 30 seconds
    mvp_candidates = [(k, v) for k, v in successful_results.items() 
                     if v['render_time'] < 30]
    if mvp_candidates:
        recommendations['mvp_demo'] = min(mvp_candidates, key=lambda x: x[1]['render_time'])[0]
    
    # Student Content: Good balance under 60 seconds
    student_candidates = [(k, v) for k, v in successful_results.items() 
                         if v['render_time'] < 60 and '480p' in k]
    if student_candidates:
        recommendations['student_content'] = max(student_candidates, 
                                               key=lambda x: int(next(c for c in CONFIGS if c['name'] == x[0])['fps']))[0]
    
    # Classroom: Best 720p under 90 seconds  
    classroom_candidates = [(k, v) for k, v in successful_results.items() 
                           if v['render_time'] < 90 and '720p' in k]
    if classroom_candidates:
        recommendations['classroom_presentation'] = min(classroom_candidates, key=lambda x: x[1]['render_time'])[0]
    
    # Publishing: Best quality regardless of time
    if successful_results:
        recommendations['course_publishing'] = max(successful_results.items(),
                                                  key=lambda x: metrics['quality_scores'].get(x[0], 0))[0]
    
    return recommendations

def save_results(results, metrics, recommendations):
    """Save detailed results to JSON file"""
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'test_file': TEST_FILE,
        'scene_class': SCENE_CLASS,
        'configurations_tested': len(CONFIGS),
        'results': results,
        'metrics': metrics,
        'recommendations': recommendations,
        'summary': {
            'fastest_render': f"{metrics['fastest_config']} ({metrics['fastest_time']:.2f}s)" if metrics else "N/A",
            'best_value': f"{metrics['best_value_config']}" if metrics else "N/A",
            'mvp_recommendation': recommendations['mvp_demo'] if recommendations else "N/A"
        }
    }
    
    with open(RESULTS_FILE, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"📊 Detailed results saved to: {RESULTS_FILE}")

def print_mvp_summary(results, recommendations):
    """Print a beautiful summary for MVP presentation"""
    
    print("\n" + "="*80)
    print("🎯 MVP EDUCATIONAL CONTENT PERFORMANCE SUMMARY")
    print("="*80)
    
    if recommendations['mvp_demo']:
        mvp_config = next(c for c in CONFIGS if c['name'] == recommendations['mvp_demo'])
        mvp_result = results[recommendations['mvp_demo']]
        
        print(f"\n🚀 RECOMMENDED FOR MVP DEMOS:")
        print(f"   Configuration: {mvp_config['description']}")
        print(f"   Render Time:   {mvp_result['render_time']:.2f} seconds")
        print(f"   File Size:     {mvp_result.get('file_size_mb', 0):.1f} MB")
        print(f"   Use Case:      {mvp_config['target_use']}")
        print(f"   ✨ Perfect for live demonstrations and quick content iteration!")
    
    print(f"\n📚 STUDENT LEARNING RECOMMENDATIONS:")
    for use_case, config_name in recommendations.items():
        if config_name and use_case != 'mvp_demo':
            config = next(c for c in CONFIGS if c['name'] == config_name)
            result = results[config_name]
            
            use_case_display = use_case.replace('_', ' ').title()
            print(f"\n   {use_case_display}:")
            print(f"     • {config['description']}")
            print(f"     • Renders in {result['render_time']:.2f}s")
            print(f"     • Ideal for: {config['target_use']}")
    
    print(f"\n💡 KEY INSIGHTS FOR INVESTORS/USERS:")
    successful_count = sum(1 for r in results.values() if r['success'])
    print(f"   ✅ {successful_count}/{len(CONFIGS)} configurations work perfectly")
    print(f"   ⚡ Fastest render: {min(r['render_time'] for r in results.values() if r['success']):.1f}s")
    print(f"   🎬 Ready for real-time educational content generation")
    print(f"   📱 Optimized for different device capabilities and network speeds")
    
    print("\n" + "="*80)

def main():
    """Main benchmark function"""
    
    print("╔════════════════════════════════════════════════════════════════════════════════╗")
    print("║                  🎓 EDUCATIONAL CONTENT PERFORMANCE BENCHMARK 🎓               ║")
    print("║                                                                                ║")
    print("║  Testing optimal video quality settings for educational content delivery      ║")
    print("║  Perfect for MVP demonstrations and user experience optimization             ║")
    print("║                                                                                ║")
    print("╚════════════════════════════════════════════════════════════════════════════════╝")
    print()
    
    logger.info(f"📁 Videos will be saved to: {OUTPUT_DIR}")
    logger.info(f"🎬 Testing scene: {SCENE_CLASS}")
    print()
    
    # Run all benchmark configurations
    results = {}
    total_configs = len(CONFIGS)
    
    for i, config in enumerate(CONFIGS, 1):
        logger.info(f"📊 Progress: {i}/{total_configs} - {config['name']}")
        logger.info("="*70)
        
        result = render_with_config(config)
        results[config['name']] = result
        
        print()  # Add spacing between tests
    
    # Calculate metrics and recommendations
    logger.info("="*70)
    logger.info("🧮 Calculating performance metrics...")
    
    metrics = calculate_metrics(results)
    recommendations = generate_recommendations(results, metrics)
    
    # Save detailed results
    save_results(results, metrics, recommendations)
    
    # Print beautiful MVP summary
    print_mvp_summary(results, recommendations)
    
    # Print detailed technical results
    print("\n" + "="*80)
    print("🔧 DETAILED TECHNICAL RESULTS")
    print("="*80)
    
    for config in CONFIGS:
        result = results[config['name']]
        print(f"\n📹 {config['description']}")
        print(f"   Resolution: {config['resolution']} | FPS: {config['fps']} | Quality: {config['quality']}")
        
        if result['success']:
            print(f"   ✅ Render Time: {result['render_time']:.2f}s")
            print(f"   📁 File Size: {result.get('file_size_mb', 0):.1f} MB")
            print(f"   🎯 Target Use: {config['target_use']}")
        else:
            print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")
    
    logger.info("="*70)
    logger.info("🎉 Educational content benchmark complete!")
    logger.info(f"📊 Check detailed results in: {RESULTS_FILE}")
    logger.info(f"📁 Check your videos in: {OUTPUT_DIR}")

if __name__ == "__main__":
    main() 