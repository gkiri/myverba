import asyncio
import re
from contextlib import contextmanager
from pathlib import Path
from typing import List, Dict, Optional, Generator, Any
from dataclasses import dataclass
from math import ceil

from manim import Scene, config, logger
from manim_voiceover.services.base import SpeechService
from manim_voiceover.tracker import VoiceoverTracker
from manim_voiceover.helper import chunks
from async_deepinfra_service import AsyncDeepInfraService


@dataclass
class VoiceoverSegment:
    """Data class for a voiceover segment"""
    text: str
    kwargs: Dict[str, Any]
    subcaption: Optional[str] = None
    max_subcaption_len: int = 70
    subcaption_buff: float = 0.1


class AsyncVoiceoverScene(Scene):
    """
    An async-enabled voiceover scene that can pre-process and generate
    all TTS audio files concurrently for maximum performance.
    """

    speech_service: SpeechService
    current_tracker: Optional[VoiceoverTracker]
    create_subcaption: bool
    _voiceover_segments: List[VoiceoverSegment]
    _generated_audio: Dict[str, dict]
    _is_preprocessed: bool

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._voiceover_segments = []
        self._generated_audio = {}
        self._is_preprocessed = False

    def set_speech_service(
        self,
        speech_service: SpeechService,
        create_subcaption: bool = True,
    ) -> None:
        """Sets the speech service to be used for the voiceover.

        Args:
            speech_service (SpeechService): The speech service to be used.
            create_subcaption (bool, optional): Whether to create subcaptions. Defaults to True.
        """
        self.speech_service = speech_service
        self.current_tracker = None
        self.create_subcaption = create_subcaption

    def register_voiceover(
        self,
        text: str,
        subcaption: Optional[str] = None,
        max_subcaption_len: int = 70,
        subcaption_buff: float = 0.1,
        **kwargs,
    ) -> int:
        """
        Register a voiceover segment for later batch processing.
        
        Args:
            text (str): The text to be spoken.
            subcaption (Optional[str], optional): Alternative subcaption text.
            max_subcaption_len (int, optional): Maximum subcaption length.
            subcaption_buff (float, optional): Duration between subcaption chunks.
            **kwargs: Additional parameters for TTS generation.
            
        Returns:
            int: Index of the registered segment.
        """
        segment = VoiceoverSegment(
            text=text,
            kwargs=kwargs,
            subcaption=subcaption,
            max_subcaption_len=max_subcaption_len,
            subcaption_buff=subcaption_buff
        )
        self._voiceover_segments.append(segment)
        return len(self._voiceover_segments) - 1

    async def preprocess_voiceovers(self) -> None:
        """
        Pre-process all registered voiceover segments concurrently.
        This should be called before starting the animation.
        """
        if not self._voiceover_segments:
            logger.info("No voiceover segments to preprocess.")
            return

        if not hasattr(self, "speech_service"):
            raise Exception("You need to call set_speech_service() before preprocessing voiceovers.")

        logger.info(f"Preprocessing {len(self._voiceover_segments)} voiceover segments...")

        # Extract all texts for batch processing
        texts = [segment.text for segment in self._voiceover_segments]
        
        # If using async service, use batch generation
        if isinstance(self.speech_service, AsyncDeepInfraService):
            # Collect all unique kwargs combinations
            kwargs_groups = {}
            for i, segment in enumerate(self._voiceover_segments):
                kwargs_key = str(sorted(segment.kwargs.items()))
                if kwargs_key not in kwargs_groups:
                    kwargs_groups[kwargs_key] = {
                        'kwargs': segment.kwargs,
                        'indices': [],
                        'texts': []
                    }
                kwargs_groups[kwargs_key]['indices'].append(i)
                kwargs_groups[kwargs_key]['texts'].append(segment.text)
            
            # Process each group concurrently
            all_results = [None] * len(self._voiceover_segments)
            
            async def process_group(group_data):
                results = await self.speech_service.async_generate_multiple(
                    group_data['texts'], 
                    **group_data['kwargs']
                )
                return group_data['indices'], results
            
            # Run all groups concurrently
            group_tasks = [process_group(group_data) for group_data in kwargs_groups.values()]
            group_results = await asyncio.gather(*group_tasks)
            
            # Reassemble results in original order
            for indices, results in group_results:
                for idx, result in zip(indices, results):
                    # Ensure the result has the expected "final_audio" key
                    if "final_audio" not in result and "original_audio" in result:
                        result["final_audio"] = result["original_audio"]
                    all_results[idx] = result
        else:
            # Fallback for non-async services - still concurrent but using thread pool
            async def generate_single(segment):
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(
                    None, 
                    lambda: self.speech_service._wrap_generate_from_text(segment.text, **segment.kwargs)
                )
            
            tasks = [generate_single(segment) for segment in self._voiceover_segments]
            all_results = await asyncio.gather(*tasks)

        # Store results
        for i, result in enumerate(all_results):
            segment_key = f"segment_{i}"
            self._generated_audio[segment_key] = result

        self._is_preprocessed = True
        logger.info(f"Successfully preprocessed {len(self._voiceover_segments)} voiceover segments.")

    def add_voiceover_text(
        self,
        text: str,
        subcaption: Optional[str] = None,
        max_subcaption_len: int = 70,
        subcaption_buff: float = 0.1,
        segment_index: Optional[int] = None,
        **kwargs,
    ) -> VoiceoverTracker:
        """
        Add voiceover to the scene using pre-processed audio or generating on-demand.

        Args:
            text (str): The text to be spoken.
            subcaption (Optional[str], optional): Alternative subcaption text.
            max_subcaption_len (int, optional): Maximum subcaption length.
            subcaption_buff (float, optional): Duration between subcaption chunks.
            segment_index (Optional[int], optional): Index of pre-registered segment.
            **kwargs: Additional parameters for TTS generation.

        Returns:
            VoiceoverTracker: The tracker object for the voiceover.
        """
        if not hasattr(self, "speech_service"):
            raise Exception("You need to call set_speech_service() before adding a voiceover.")

        # Check if we have pre-processed audio for this segment
        if segment_index is not None and self._is_preprocessed:
            segment_key = f"segment_{segment_index}"
            if segment_key in self._generated_audio:
                dict_ = self._generated_audio[segment_key]
                segment = self._voiceover_segments[segment_index]
                subcaption = subcaption or segment.subcaption
                max_subcaption_len = max_subcaption_len or segment.max_subcaption_len
                subcaption_buff = subcaption_buff or segment.subcaption_buff
                
                # Ensure the dict has the expected "final_audio" key
                if "final_audio" not in dict_ and "original_audio" in dict_:
                    dict_["final_audio"] = dict_["original_audio"]
            else:
                raise ValueError(f"No pre-processed audio found for segment {segment_index}")
        else:
            # Generate on-demand (fallback)
            dict_ = self.speech_service._wrap_generate_from_text(text, **kwargs)

        # Create tracker and add audio
        tracker = VoiceoverTracker(self, dict_, self.speech_service.cache_dir)
        self.add_sound(str(Path(self.speech_service.cache_dir) / dict_["final_audio"]))
        self.current_tracker = tracker

        # Add subcaptions if enabled
        if self.create_subcaption:
            if subcaption is None:
                # Remove placeholders
                subcaption = re.sub(r"<[^<>]+/>", "", text)

            self.add_wrapped_subcaption(
                subcaption,
                tracker.duration,
                subcaption_buff=subcaption_buff,
                max_subcaption_len=max_subcaption_len,
            )

        return tracker

    def add_wrapped_subcaption(
        self,
        subcaption: str,
        duration: float,
        subcaption_buff: float = 0.1,
        max_subcaption_len: int = 70,
    ) -> None:
        """Add wrapped subcaptions to the scene."""
        subcaption = " ".join(subcaption.split())
        n_chunk = ceil(len(subcaption) / max_subcaption_len)
        tokens = subcaption.split(" ")
        chunk_len = ceil(len(tokens) / n_chunk)
        chunks_ = list(chunks(tokens, chunk_len))

        subcaptions = [" ".join(i) for i in chunks_]
        subcaption_weights = [
            len(subcaption) / len("".join(subcaptions)) for subcaption in subcaptions
        ]

        current_offset = 0
        for idx, subcaption in enumerate(subcaptions):
            chunk_duration = duration * subcaption_weights[idx]
            self.add_subcaption(
                subcaption,
                duration=max(chunk_duration - subcaption_buff, 0),
                offset=current_offset,
            )
            current_offset += chunk_duration

    def wait_for_voiceover(self) -> None:
        """Wait for the current voiceover to finish."""
        if not hasattr(self, "current_tracker"):
            return
        if self.current_tracker is None:
            return

        self.safe_wait(self.current_tracker.get_remaining_duration())

    def safe_wait(self, duration: float) -> None:
        """Wait for a given duration, ensuring at least one frame."""
        if duration > 1 / config["frame_rate"]:
            self.wait(duration)

    def wait_until_bookmark(self, mark: str) -> None:
        """Wait until a bookmark is reached."""
        self.safe_wait(self.current_tracker.time_until_bookmark(mark))

    @contextmanager
    def voiceover(
        self, 
        text: str = None, 
        segment_index: Optional[int] = None,
        **kwargs
    ) -> Generator[VoiceoverTracker, None, None]:
        """
        Context manager for adding voiceover to a scene.

        Args:
            text (str, optional): The text to be spoken.
            segment_index (Optional[int], optional): Index of pre-registered segment.
            **kwargs: Additional parameters.

        Yields:
            VoiceoverTracker: The voiceover tracker object.
        """
        if text is None and segment_index is None:
            raise ValueError("Please specify either text or segment_index.")

        # If segment_index is provided, use the pre-registered text
        if segment_index is not None:
            if segment_index >= len(self._voiceover_segments):
                raise ValueError(f"Invalid segment_index: {segment_index}")
            text = self._voiceover_segments[segment_index].text

        try:
            yield self.add_voiceover_text(text, segment_index=segment_index, **kwargs)
        finally:
            self.wait_for_voiceover()

    @contextmanager
    def batch_voiceover(self, segment_indices: List[int], **kwargs) -> Generator[List[VoiceoverTracker], None, None]:
        """
        Context manager for adding multiple voiceovers in sequence.
        
        Args:
            segment_indices: List of segment indices to play in sequence.
            **kwargs: Additional parameters.
            
        Yields:
            List[VoiceoverTracker]: List of voiceover tracker objects.
        """
        trackers = []
        
        try:
            for segment_index in segment_indices:
                tracker = self.add_voiceover_text(
                    text=self._voiceover_segments[segment_index].text,
                    segment_index=segment_index,
                    **kwargs
                )
                trackers.append(tracker)
                self.wait_for_voiceover()
            
            yield trackers
        finally:
            # All voiceovers have already been waited for in the loop
            pass


# Utility function to run async preprocessing
def preprocess_scene_voiceovers(scene: AsyncVoiceoverScene) -> None:
    """
    Utility function to run async voiceover preprocessing.
    
    Args:
        scene: The AsyncVoiceoverScene instance to preprocess.
    """
    asyncio.run(scene.preprocess_voiceovers()) 