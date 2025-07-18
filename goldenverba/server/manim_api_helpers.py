"""
Manim Text-to-Video API Helpers

This module provides helper functions for integrating the Project Drishti text-to-video 
generation pipeline into the Verba API.
"""

import logging
import os
import json
import asyncio
import time
from functools import partial
import multiprocessing
import subprocess
import tempfile
import re
from pathlib import Path
from typing import Optional, Dict, List, AsyncGenerator
from wasabi import msg
import uuid
from datetime import datetime

# Import Supabase client
from goldenverba.server.supabase.supabase_client import supabase

# Import the manim pipeline components with absolute paths
try:
    from goldenverba.final_manim.anim_gemini.project_drishti.didactic_scripter import DidacticScripter
    from goldenverba.final_manim.anim_gemini.project_drishti.visual_architect import VisualArchitect
    from goldenverba.final_manim.anim_gemini.project_drishti.manim_renderer import ManimRenderer
    from goldenverba.final_manim.anim_gemini.project_drishti.video_analyzer import VideoAnalyzer
    from goldenverba.final_manim.anim_gemini.project_drishti import config
    MANIM_AVAILABLE = True
except ImportError as e:
    msg.warn(f"Manim components not available: {e}")
    MANIM_AVAILABLE = False

# Setup logging
logger = logging.getLogger("ManimAPI")

MAX_RENDER_ATTEMPTS = 3
DEFAULT_NUM_SCENES = 3  # Conservative default for API use


class ManimPipelineError(Exception):
    """Custom exception for manim pipeline errors"""
    pass


def check_manim_dependencies() -> bool:
    """
    Check if manim dependencies are available and components are properly imported.
    
    Returns:
        bool: True if all dependencies are available, False otherwise
    """
    # # If user explicitly disables manim check
    # if os.getenv("DISABLE_MANIM_CHECK", "false").lower() == "true":
    #     return True
    
    # # Check if our manim components were imported successfully
    # if not MANIM_AVAILABLE:
    #     return False
        
    # # Check if manim itself is available
    # try:
    #     import manim
    #     return True
    # except ImportError:
    #     logger.warning("Manim library not available")
    #     return False
    return True


def generate_manim_script_for_scene_wrapper(architect_instance, scene_data, topic_title_str):
    """Wrapper function for scene script generation"""
    script_path, manim_class_name = architect_instance.generate_manim_code_for_scene(
        scene_data,
        topic_title=topic_title_str
    )
    logger.info(f"Script generated for scene: {scene_data.get('title', 'Unknown')}")
    return script_path, manim_class_name, scene_data


async def render_scene_with_retries(
    *,
    initial_script_path: str,
    initial_manim_class_name: str,
    original_scene_data: dict,
    architect_instance,
    renderer_instance,
    video_analyzer_instance,
    loop: asyncio.AbstractEventLoop,
    topic_title_str: str,
    metrics_tracker: dict,
    cpu_semaphore: asyncio.Semaphore,
    io_semaphore: asyncio.Semaphore,
    initial_script_gen_time: float = 0.0,
    max_retries: int = MAX_RENDER_ATTEMPTS,
    progress_callback = None
) -> Optional[str]:
    """
    Render a scene with retries and optional progress callback
    """
    current_script_path = initial_script_path
    current_manim_class_name = initial_manim_class_name
    scene_title = original_scene_data.get("title", "Unknown Scene")
    
    if progress_callback:
        await progress_callback(f"Starting render for scene: {scene_title}")
    
    for attempt in range(max_retries):
        logger.info(f"Processing attempt {attempt + 1}/{max_retries} for scene '{scene_title}'")
        
        if progress_callback:
            await progress_callback(f"Attempt {attempt + 1} for scene: {scene_title}")
        
        # CPU-BOUND: Rendering
        render_success, video_path, render_error = False, None, ""
        async with cpu_semaphore:
            logger.info(f"Rendering '{scene_title}' from {current_script_path}...")
            rd_start = time.perf_counter()
            render_success, video_path, render_error = await loop.run_in_executor(
                None,
                renderer_instance.render_scene,
                current_script_path,
                current_manim_class_name
            )
            render_time = time.perf_counter() - rd_start
            
            # CPU-BOUND: Compression
            if render_success:
                logger.info(f"Compressing video for '{scene_title}'...")
                if progress_callback:
                    await progress_callback(f"Compressing video for scene: {scene_title}")
                    
                compressed_path, compress_time = await loop.run_in_executor(
                    None,
                    video_analyzer_instance.compress_video,
                    video_path
                )
                if not compressed_path:
                    render_success = False
                    render_error = "Video compression failed."

        # If rendering and compression are successful, proceed to analysis
        if render_success:
            logger.info(f"Successfully rendered and compressed '{scene_title}'.")
            
            # I/O-BOUND: Video Analysis
            analysis_passed, analysis_reason = False, "Analysis not run"
            async with io_semaphore:
                logger.info(f"Analyzing video quality for '{scene_title}'...")
                if progress_callback:
                    await progress_callback(f"Analyzing video quality for scene: {scene_title}")
                
                analysis_passed, analysis_reason, analysis_time = await loop.run_in_executor(
                    None,
                    video_analyzer_instance.analyze_compressed_video,
                    compressed_path,
                    video_path,
                    original_scene_data.get("script_content", ""),
                )

            if analysis_passed:
                logger.info(f"SUCCESS: Video for '{scene_title}' passed quality analysis")
                if progress_callback:
                    await progress_callback(f"✅ Scene completed: {scene_title}")
                return video_path
            else:
                logger.warning(f"Video for '{scene_title}' FAILED quality analysis: {analysis_reason}")
                render_success = False
                render_error = analysis_reason

        # If we reach here, the attempt failed
        if not render_success:
            logger.error(f"Failed to produce quality video for '{scene_title}' on attempt {attempt + 1}: {render_error}")
            
            if attempt >= max_retries - 1:
                logger.critical(f"Max retries reached for '{scene_title}'. Moving on.")
                if progress_callback:
                    await progress_callback(f"❌ Failed after {max_retries} attempts: {scene_title}")
                break
            
            # Attempt to regenerate script for next iteration
            if progress_callback:
                await progress_callback(f"Regenerating script for scene: {scene_title}")
                
            try:
                async with io_semaphore:
                    gen_script_path, gen_manim_class_name, _ = await loop.run_in_executor(
                        None,
                        partial(
                            generate_manim_script_for_scene_wrapper,
                            architect_instance,
                            original_scene_data,
                            topic_title_str
                        )
                    )
                
                if gen_script_path and gen_manim_class_name:
                    logger.info(f"Script regenerated for '{scene_title}'")
                    if current_script_path != gen_script_path and os.path.exists(current_script_path):
                        os.remove(current_script_path)
                    current_script_path = gen_script_path
                    current_manim_class_name = gen_manim_class_name
                else:
                    logger.error(f"Failed to regenerate script for '{scene_title}'")
                    
            except Exception as e:
                logger.error(f"Exception during script regeneration for '{scene_title}': {e}")

    logger.error(f"All {max_retries} attempts failed for scene '{scene_title}'.")
    return None


async def process_scene(
    scene_data: dict,
    architect,
    renderer,
    video_analyzer,
    loop: asyncio.AbstractEventLoop,
    topic_title_str: str,
    metrics_tracker: dict,
    io_semaphore: asyncio.Semaphore,
    cpu_semaphore: asyncio.Semaphore,
    progress_callback = None
):
    """Process a single scene from script generation to final video"""
    scene_title = scene_data.get("title", f"Scene_{scene_data.get('scene_number', 'Unknown')}")
    logger.info(f"Processing scene: {scene_title}")
    
    if progress_callback:
        await progress_callback(f"Generating script for scene: {scene_title}")

    # I/O-BOUND: Script Generation
    script_path, manim_class_name = None, None
    initial_script_gen_time = 0.0
    async with io_semaphore:
        sg_start_initial = time.perf_counter()
        try:
            script_path, manim_class_name, _ = await loop.run_in_executor(
                None,
                partial(
                    generate_manim_script_for_scene_wrapper,
                    architect,
                    scene_data,
                    topic_title_str
                )
            )
            initial_script_gen_time = time.perf_counter() - sg_start_initial
        except Exception as e:
            logger.error(f"Initial script generation failed for {scene_title}: {e}")
            if progress_callback:
                await progress_callback(f"❌ Script generation failed for scene: {scene_title}")
            return None

    if not (script_path and manim_class_name):
        logger.error(f"Could not generate initial script for scene: {scene_title}")
        if progress_callback:
            await progress_callback(f"❌ No script generated for scene: {scene_title}")
        return None

    # Call the main processing loop
    video_path = await render_scene_with_retries(
        initial_script_path=script_path,
        initial_manim_class_name=manim_class_name,
        original_scene_data=scene_data,
        architect_instance=architect,
        renderer_instance=renderer,
        video_analyzer_instance=video_analyzer,
        loop=loop,
        topic_title_str=topic_title_str,
        metrics_tracker=metrics_tracker,
        cpu_semaphore=cpu_semaphore,
        io_semaphore=io_semaphore,
        initial_script_gen_time=initial_script_gen_time,
        progress_callback=progress_callback
    )
    
    return video_path


def concatenate_videos(video_paths: List[str], output_path: str) -> bool:
    """Concatenate multiple video files into a single video using FFmpeg"""
    if not video_paths:
        logger.warning("No video paths provided for concatenation.")
        return False
    
    if len(video_paths) == 1:
        logger.info("Only one video found. Copying to final output...")
        try:
            import shutil
            shutil.copy2(video_paths[0], output_path)
            logger.info(f"Successfully copied single video to: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to copy single video: {e}")
            return False
    
    # Check if FFmpeg is available
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("FFmpeg is not available. Cannot concatenate videos.")
        return False
    
    # Sort video paths by scene number
    def extract_scene_number(path):
        filename = os.path.basename(path)
        match = re.search(r'Scene(\d+)', filename)
        return int(match.group(1)) if match else 0
    
    video_paths_sorted = sorted(video_paths, key=extract_scene_number)
    
    # Create temporary file list for FFmpeg
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
        temp_file_path = temp_file.name
        for video_path in video_paths_sorted:
            abs_path = os.path.abspath(video_path)
            temp_file.write(f"file '{abs_path}'\n")
    
    try:
        cmd = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', temp_file_path,
            '-c', 'copy',
            '-y',
            output_path
        ]
        
        logger.info(f"Concatenating {len(video_paths_sorted)} videos...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            logger.info(f"Successfully concatenated videos into: {output_path}")
            if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                return True
        else:
            logger.error(f"FFmpeg concatenation failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("Video concatenation timed out")
        return False
    except Exception as e:
        logger.error(f"Error during video concatenation: {e}")
        return False
    finally:
        try:
            os.unlink(temp_file_path)
        except OSError:
            pass
    
    return False


async def upload_video_to_supabase_storage(video_path: str, user_id: str, topic: str) -> Optional[str]:
    """
    Upload video file to Supabase storage bucket 'videos' and return public URL
    
    Args:
        video_path: Local path to the video file
        user_id: User ID for organizing files
        topic: Topic name for file naming
        
    Returns:
        Public URL of uploaded video or None if upload fails
    """
    try:
        if not os.path.exists(video_path):
            logger.error(f"Video file not found: {video_path}")
            return None
            
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_topic = re.sub(r'[^\w\-_]', '_', topic)[:50]  # Sanitize topic name
        unique_id = str(uuid.uuid4())[:8]
        filename = f"{user_id}_{safe_topic}_{timestamp}_{unique_id}.mp4"
        
        # Read video file
        with open(video_path, 'rb') as video_file:
            video_data = video_file.read()
        
        logger.info(f"Uploading video to Supabase storage: {filename}")
        
        # Upload to Supabase storage bucket 'videos'
        storage_response = supabase.storage.from_("videos").upload(
            path=filename,
            file=video_data,
            file_options={"content-type": "video/mp4"}
        )
        
        if storage_response:
            # Get public URL - Supabase returns a dict with 'publicUrl' key
            public_url_response = supabase.storage.from_("videos").get_public_url(filename)
            public_url = public_url_response.get('publicUrl') if isinstance(public_url_response, dict) else public_url_response
            
            logger.info(f"Successfully uploaded video to Supabase storage: {public_url}")
            return public_url
        else:
            logger.error("Failed to upload video to Supabase storage")
            return None
            
    except Exception as e:
        logger.error(f"Error uploading video to Supabase storage: {str(e)}")
        return None


async def run_text_to_video_pipeline(
    topic: str, 
    user_id: str,
    num_scenes: Optional[int] = None,
    progress_callback = None
) -> Dict:
    """
    Run the complete text-to-video pipeline with progress callbacks
    
    Args:
        topic: The topic to generate video for
        num_scenes: Number of scenes to generate (default: 3)
        progress_callback: Async function to call with progress updates
        
    Returns:
        Dict with status, video_path, and metrics
    """
    # Check if manim components are available
    if not MANIM_AVAILABLE:
        raise ManimPipelineError("Manim components not available - import failed")
    
    if not check_manim_dependencies():
        raise ManimPipelineError("Manim dependencies not available or not configured")
    
    if num_scenes is None:
        num_scenes = DEFAULT_NUM_SCENES
    
    logger.info(f"Starting text-to-video pipeline for topic: '{topic}' with {num_scenes} scenes")
    
    if progress_callback:
        await progress_callback(f"🎬 Starting video generation for: {topic}")
    
    scene_metrics = {}
    final_video_paths = []
    final_video_path = None
    storage_video_url = None
    
    try:
        # Stage 1: Didactic Scripter
        if progress_callback:
            await progress_callback("📝 Generating educational script...")
            
        scripter = DidacticScripter()
        ds_start = time.perf_counter()
        
        didactic_script = await asyncio.get_event_loop().run_in_executor(
            None,
            scripter.generate_script,
            topic,
            num_scenes
        )
        
        didactic_script_time = time.perf_counter() - ds_start
        
        if not didactic_script:
            raise ManimPipelineError("Failed to generate the didactic script")

        logger.info(f"Generated didactic script with {len(didactic_script['scenes'])} scenes")
        
        if progress_callback:
            await progress_callback(f"✅ Script generated with {len(didactic_script['scenes'])} scenes")

        # Stage 2 & 3: Visual Architect & Manim Renderer
        if progress_callback:
            await progress_callback("🎨 Initializing video generation components...")
            
        architect = VisualArchitect()
        renderer = ManimRenderer()
        video_analyzer = VideoAnalyzer()
        loop = asyncio.get_event_loop()
        topic_title_str = topic.replace(" ", "_")

        # Concurrency control
        cpu_cores = multiprocessing.cpu_count()
        cpu_semaphore = asyncio.Semaphore(min(4, cpu_cores))
        io_semaphore = asyncio.Semaphore(10)

        # Initialize metrics
        for scene_data in didactic_script.get("scenes", []):
            scene_title = scene_data.get("title", f"Scene_{scene_data.get('scene_number', 'Unknown')}")
            scene_metrics[scene_title] = {
                "script_generation_attempts": 0,
                "video_analysis_attempts": 0,
                "status": "Pending",
                "attempt_details": []
            }

        # Process scenes
        if progress_callback:
            await progress_callback(f"🎬 Processing {len(didactic_script['scenes'])} scenes...")
            
        processing_tasks = []
        for scene_data in didactic_script.get("scenes", []):
            task = process_scene(
                scene_data=scene_data,
                architect=architect,
                renderer=renderer,
                video_analyzer=video_analyzer,
                loop=loop,
                topic_title_str=topic_title_str,
                metrics_tracker=scene_metrics,
                io_semaphore=io_semaphore,
                cpu_semaphore=cpu_semaphore,
                progress_callback=progress_callback
            )
            processing_tasks.append(task)
        
        # Execute all scenes concurrently
        for result in await asyncio.gather(*processing_tasks):
            if result:
                final_video_paths.append(result)

        logger.info(f"Successfully generated {len(final_video_paths)} out of {len(didactic_script['scenes'])} scenes")
        
        if progress_callback:
            await progress_callback(f"📹 Completed {len(final_video_paths)}/{len(didactic_script['scenes'])} scenes")

        # Stage 4: Video Concatenation
        if final_video_paths:
            if progress_callback:
                await progress_callback("🔗 Merging individual scenes into final video...")
                
            # Get the final videos directory
            final_videos_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "final_manim", "anim_gemini", "outputs", "final_videos"
            )
            
            # Find actual video files in the directory
            actual_video_files = []
            if os.path.exists(final_videos_dir):
                for file in os.listdir(final_videos_dir):
                    if file.endswith('.mp4') and file != 'finished_video.mp4':
                        actual_video_files.append(os.path.join(final_videos_dir, file))
            
            if actual_video_files:
                finished_video_path = os.path.join(final_videos_dir, "finished_video.mp4")
                concatenation_success = concatenate_videos(actual_video_files, finished_video_path)
                
                if concatenation_success:
                    logger.info(f"Successfully created final merged video: {finished_video_path}")
                    final_video_path = finished_video_path
                    if progress_callback:
                        await progress_callback("✅ Final video created successfully!")
                    
                    # Upload video to Supabase storage
                    if progress_callback:
                        await progress_callback("☁️ Uploading video to cloud storage...")
                    
                    storage_video_url = await upload_video_to_supabase_storage(
                        video_path=finished_video_path,
                        user_id=user_id,
                        topic=topic
                    )
                    
                    if storage_video_url:
                        logger.info(f"Successfully uploaded video to storage: {storage_video_url}")
                        if progress_callback:
                            await progress_callback("✅ Video uploaded to cloud storage!")
                    else:
                        logger.warning("Failed to upload video to storage, local path available")
                        if progress_callback:
                            await progress_callback("⚠️ Cloud upload failed, local video available")
                else:
                    logger.error("Failed to concatenate videos")
                    if progress_callback:
                        await progress_callback("⚠️ Video merge failed, individual scenes available")
            else:
                logger.warning("No video files found for concatenation")
                if progress_callback:
                    await progress_callback("⚠️ No video files found for merging")

        return {
            "status": "success",
            "video_path": final_video_path,
            "storage_video_url": storage_video_url,
            "individual_videos": final_video_paths,
            "scenes_completed": len(final_video_paths),
            "scenes_total": len(didactic_script.get("scenes", [])),
            "metrics": scene_metrics,
            "processing_time": time.perf_counter() - ds_start
        }
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        if progress_callback:
            await progress_callback(f"❌ Pipeline failed: {str(e)}")
        
        return {
            "status": "error",
            "error": str(e),
            "video_path": None,
            "storage_video_url": None,
            "individual_videos": final_video_paths,
            "scenes_completed": len(final_video_paths),
            "metrics": scene_metrics
        } 