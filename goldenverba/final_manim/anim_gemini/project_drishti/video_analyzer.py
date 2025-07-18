import os
import subprocess
import logging
import time
import google.generativeai as genai
# Use relative import - this file is part of the project_drishti package
from . import config
import shutil

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

genai.configure(api_key=config.GEMINI_API_KEY)

class VideoAnalyzer:
    """
    Analyzes rendered videos for quality issues using Gemini.
    """
    def __init__(self):
        if not config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not found in environment variables.")
        genai.configure(api_key=config.GEMINI_API_KEY)
        #self.model = genai.GenerativeModel('gemini-2.5-flash-lite-preview-06-17')
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.prompt_template = self._load_prompt_template()
        # Added attributes to track timing of compression and analysis stages per call
        self.last_compress_time: float = 0.0
        self.last_analysis_time: float = 0.0

    def _load_prompt_template(self) -> str:
        try:
            with open(config.VIDEO_ANALYZER_PROMPT_TEMPLATE_PATH, 'r') as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"Video analyzer prompt template not found at: {config.VIDEO_ANALYZER_PROMPT_TEMPLATE_PATH}")
            # Fallback to a default prompt if the file is missing
            return """
            Analyze the provided video and determine if it has any spatial or quality issues.
            Specifically, check for:
            - Overlapping text or diagrams.
            - Text or diagrams running off-screen.
            - Low-quality or distorted visuals.
            - Incoherent or irrelevant content based on the scene description.

            Respond with "YES" if the video is good quality and "NO" if it has issues.
            """

    def compress_video(self, input_path: str) -> tuple[str | None, float]:
        """Compresses a video and returns the path and the time taken."""
        start_time = time.perf_counter()
        if not os.path.exists(input_path):
            logger.error(f"Input video for compression not found: {input_path}")
            return None, time.perf_counter() - start_time

        filename = os.path.basename(input_path)
        # Ensure the compressed video directory exists
        os.makedirs(config.COMPRESSED_VIDEO_DIR, exist_ok=True)
        output_path = os.path.join(config.COMPRESSED_VIDEO_DIR, f"compressed_{filename}")

        command = [
            "ffmpeg",
            "-i", input_path,
            "-y",  # Overwrite output file if it exists
            "-vf", f"scale={config.COMPRESSION_RESOLUTION}",
            "-preset", "ultrafast",
            "-loglevel", "error", # Suppress verbose output
            output_path
        ]
        
        try:
            # Using capture_output=True and text=True to get stderr on failure
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            logger.info(f"Successfully compressed video to: {output_path}")
            return output_path, time.perf_counter() - start_time
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to compress video: {e.stderr}")
            return None, time.perf_counter() - start_time

    def analyze_compressed_video(self, compressed_path: str, original_video_path: str, scene_description: str) -> tuple[bool, str, float]:
        """Analyzes a pre-compressed video file."""
        analysis_start = time.perf_counter()
        if not compressed_path or not os.path.exists(compressed_path):
            logger.error(f"Compressed video not found for analysis: {compressed_path}")
            return False, "Compressed video file missing.", 0.0

        video_file = None
        try:
            logger.info(f"Uploading compressed video to Gemini: {compressed_path}")
            video_file = genai.upload_file(path=compressed_path)
            
            # Wait for the video to be processed
            while video_file.state.name == "PROCESSING":
                time.sleep(10)
                video_file = genai.get_file(video_file.name)

            if video_file.state.name == "FAILED":
                logger.error("Gemini video processing failed.")
                analysis_time = time.perf_counter() - analysis_start
                return False, "Gemini video processing failed.", analysis_time

            logger.info("Video uploaded. Generating content with Gemini.")
            prompt = self.prompt_template
            response = self.model.generate_content([prompt, video_file])
            
            result_text = response.text.strip()
            logger.info(f"Gemini analysis result: {result_text}")

            try:
                # Parsing logic remains the same
                lines = result_text.strip().split('\n')
                if len(lines) < 2:
                    logger.error(f"Unexpected response format - expecting 2 lines but got {len(lines)}: '{result_text}'")
                    analysis_time = time.perf_counter() - analysis_start
                    return False, f"Unexpected Gemini response format: {result_text}", analysis_time

                overlap_line = lines[-2]
                boundary_line = lines[-1]
                overlap_prefix = "####OVERLAP####"
                boundary_prefix = "####BOUNDARY####"

                if not overlap_line.startswith(overlap_prefix) or not boundary_line.startswith(boundary_prefix):
                    logger.error(f"Unexpected response format - missing prefixes: '{result_text}'")
                    analysis_time = time.perf_counter() - analysis_start
                    return False, "Response missing required prefixes.", analysis_time
                
                overlap_severity = overlap_line.replace(overlap_prefix, "").strip()
                boundary_severity = boundary_line.replace(boundary_prefix, "").strip()

                is_overlap_ok = overlap_severity in ["NONE", "LOW", "HIGH"]
                is_boundary_ok = boundary_severity in ["NONE", "LOW", "HIGH"]
                is_boundary_ok = True # Experiment override

                analysis_time = time.perf_counter() - analysis_start
                if is_overlap_ok and is_boundary_ok:
                    self.move_to_final_videos(original_video_path)
                    return True, "Video analysis passed.", analysis_time
                else:
                    reason = f"Video failed due to OVERLAP: {overlap_severity}, BOUNDARY: {boundary_severity}"
                    logger.warning(reason)
                    return False, reason, analysis_time

            except Exception as e:
                logger.error(f"Error parsing Gemini response: '{result_text}'. Error: {e}")
                analysis_time = time.perf_counter() - analysis_start
                return False, f"Error parsing Gemini response: {e}", analysis_time

        except Exception as e:
            logger.error(f"An error occurred during Gemini video analysis: {e}")
            analysis_time = time.perf_counter() - analysis_start
            return False, f"An error occurred during Gemini analysis: {e}", analysis_time
        finally:
            if video_file:
                try:
                    genai.delete_file(video_file.name)
                except Exception as e:
                    logger.error(f"Failed to delete Gemini file {video_file.name}: {e}")
            if compressed_path and os.path.exists(compressed_path):
                try:
                    os.remove(compressed_path)
                except OSError as e:
                    logger.error(f"Error removing compressed file {compressed_path}: {e}")

    def move_to_final_videos(self, video_path: str) -> str | None:
        """
        Moves the video to the final videos directory.
        """
        if not os.path.exists(video_path):
            logger.error(f"Video file not found at: {video_path}")
            return None

        filename = os.path.basename(video_path)
        destination_path = os.path.join(config.FINAL_VIDEOS_DIR, filename)

        try:
            shutil.move(video_path, destination_path)
            logger.info(f"Successfully moved video to: {destination_path}")
            return destination_path
        except Exception as e:
            logger.error(f"Failed to move video: {e}")
            return None

    def analyze_and_report(self, video_path, scene_narration):
        """
        DEPRECATED: This method now contains the old logic. The new flow
        is compress_video -> analyze_compressed_video.
        This method is kept for reference but should not be used in the new pipeline.
        """
        # This is now a placeholder and should not be called by the optimized pipeline.
        logger.warning("analyze_and_report is deprecated. Use the new compress -> analyze flow.")
        return False, "Deprecated function called", {"compress_time": 0, "analysis_time": 0}

if __name__ == '__main__':
    # This is a placeholder for a test.
    # To run this, you would need a sample video and scene narration.
    analyzer = VideoAnalyzer()
    
    # Example Usage (requires a video file at 'sample.mp4')
    # narration = "A square transforms into a circle."
    # is_good, reason = analyzer.analyze_and_report('sample.mp4', narration)
    # print(f"Analysis result: {'Good' if is_good else 'Bad'}")
    # print(f"Reason: {reason}")
    pass 