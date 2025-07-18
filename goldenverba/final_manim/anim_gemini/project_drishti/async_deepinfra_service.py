import os
import sys
import asyncio
import aiohttp
import aiofiles
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from concurrent.futures import ThreadPoolExecutor
import time
from dataclasses import dataclass

from dotenv import find_dotenv, load_dotenv
from manim import logger

from manim_voiceover.helper import (
    create_dotenv_file,
    prompt_ask_missing_extras,
    remove_bookmarks,
)
from manim_voiceover.services.base import SpeechService

try:
    import openai
except ImportError:
    logger.error(
        "Missing packages. "
        'Run `pip install "manim-voiceover[openai]"` to use AsyncDeepInfraService.'
    )

load_dotenv(find_dotenv(usecwd=True))


@dataclass
class TTSRequest:
    """Data class for TTS request parameters"""
    text: str
    voice: str
    model: str
    speed: float
    cache_dir: Path
    audio_path: str
    input_data: Dict[str, Any]
    original_text: str


@dataclass
class TTSResult:
    """Data class for TTS result"""
    success: bool
    audio_path: str
    input_text: str
    input_data: Dict[str, Any]
    error: Optional[str] = None
    duration: Optional[float] = None


class AsyncRateLimiter:
    """Simple async rate limiter to prevent API overload"""
    
    def __init__(self, max_requests_per_second: float = 5.0):
        self.max_requests_per_second = max_requests_per_second
        self.min_interval = 1.0 / max_requests_per_second
        self.last_request_time = 0.0
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        async with self._lock:
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            
            if time_since_last < self.min_interval:
                sleep_time = self.min_interval - time_since_last
                await asyncio.sleep(sleep_time)
            
            self.last_request_time = time.time()


class AsyncDeepInfraService(SpeechService):
    """
    Async Speech service class for DeepInfra TTS Service using Kokoro TTS model.
    Supports concurrent TTS generation for improved performance.
    """

    def __init__(
        self,
        voice: str = "af_bella",
        model: str = "hexgrad/Kokoro-82M",
        transcription_model=None,
        api_key: str = None,
        base_url: str = "https://api.deepinfra.com/v1/openai",
        max_concurrent_requests: int = 10,
        max_requests_per_second: float = 5.0,
        timeout: float = 30.0,
        max_retries: int = 3,
        **kwargs
    ):
        """
        Args:
            voice (str, optional): The voice to use with Kokoro TTS.
                Defaults to "af_bella".
            model (str, optional): The TTS model to use.
                Defaults to "hexgrad/Kokoro-82M".
            api_key (str, optional): DeepInfra API key. If not provided,
                will look for DEEPINFRA_API_KEY environment variable.
            base_url (str, optional): DeepInfra API base URL.
                Defaults to "https://api.deepinfra.com/v1/openai".
            max_concurrent_requests (int, optional): Maximum number of concurrent requests.
                Defaults to 10.
            max_requests_per_second (float, optional): Rate limit for API requests.
                Defaults to 5.0.
            timeout (float, optional): Request timeout in seconds. Defaults to 30.0.
            max_retries (int, optional): Maximum number of retries for failed requests.
                Defaults to 3.
        """
        prompt_ask_missing_extras("openai", "openai", "AsyncDeepInfraService")
        self.voice = voice
        self.model = model
        self.api_key = api_key or os.getenv("DEEPINFRA_API_KEY")
        self.base_url = base_url
        self.max_concurrent_requests = max_concurrent_requests
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Rate limiter and semaphore for concurrency control
        self.rate_limiter = AsyncRateLimiter(max_requests_per_second)
        self.semaphore = asyncio.Semaphore(max_concurrent_requests)
        
        # Thread pool for CPU-bound operations
        self.thread_pool = ThreadPoolExecutor(max_workers=4)
        
        # Cache for pending requests to avoid duplicate API calls
        self._pending_requests: Dict[str, asyncio.Future] = {}
        
        SpeechService.__init__(self, transcription_model=transcription_model, **kwargs)

    def generate_from_text(
        self, text: str, cache_dir: str = None, path: str = None, **kwargs
    ) -> dict:
        """Synchronous wrapper for async generation - maintains compatibility"""
        return asyncio.run(self.async_generate_from_text(text, cache_dir, path, **kwargs))

    async def async_generate_from_text(
        self, text: str, cache_dir: str = None, path: str = None, **kwargs
    ) -> dict:
        """Generate speech from text using DeepInfra's Kokoro TTS model asynchronously."""
        if cache_dir is None:
            cache_dir = self.cache_dir
        
        # Ensure cache_dir is a Path object
        cache_dir = Path(cache_dir)
        
        # Create cache directory if it doesn't exist
        cache_dir.mkdir(parents=True, exist_ok=True)

        speed = kwargs.get("speed", 1.0)

        if not (0.25 <= speed <= 4.0):
            raise ValueError("The speed must be between 0.25 and 4.0.")

        input_text = remove_bookmarks(text)
        input_data = {
            "input_text": input_text,
            "service": "deepinfra_async",
            "config": {
                "voice": self.voice,
                "model": self.model,
                "speed": speed,
            },
        }

        # Check cache first
        cached_result = self.get_cached_result(input_data, cache_dir)
        if cached_result is not None:
            return cached_result

        if path is None:
            audio_path = self.get_audio_basename(input_data) + ".mp3"
        else:
            audio_path = path

        # Create TTS request
        request = TTSRequest(
            text=input_text,
            voice=self.voice,
            model=self.model,
            speed=speed,
            cache_dir=cache_dir,
            audio_path=audio_path,
            input_data=input_data,
            original_text=text
        )

        # Generate audio
        result = await self._generate_single_tts(request)
        
        if not result.success:
            raise RuntimeError(f"TTS generation failed: {result.error}")

        return {
            "input_text": text,
            "input_data": input_data,
            "original_audio": audio_path,
            "final_audio": audio_path,  # Add final_audio key for compatibility
        }

    async def async_generate_multiple(
        self, 
        texts: List[str], 
        cache_dir: str = None, 
        **kwargs
    ) -> List[dict]:
        """
        Generate multiple TTS audio files concurrently.
        
        Args:
            texts: List of texts to convert to speech
            cache_dir: Cache directory for audio files
            **kwargs: Additional parameters (speed, etc.)
            
        Returns:
            List of result dictionaries in the same order as input texts
        """
        if cache_dir is None:
            cache_dir = self.cache_dir
        
        cache_dir = Path(cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        speed = kwargs.get("speed", 1.0)
        if not (0.25 <= speed <= 4.0):
            raise ValueError("The speed must be between 0.25 and 4.0.")

        # Prepare all requests
        requests = []
        for text in texts:
            input_text = remove_bookmarks(text)
            input_data = {
                "input_text": input_text,
                "service": "deepinfra_async",
                "config": {
                    "voice": self.voice,
                    "model": self.model,
                    "speed": speed,
                },
            }
            
            # Check cache first
            cached_result = self.get_cached_result(input_data, cache_dir)
            if cached_result is not None:
                requests.append(None)  # Placeholder for cached result
                continue
            
            audio_path = self.get_audio_basename(input_data) + ".mp3"
            
            request = TTSRequest(
                text=input_text,
                voice=self.voice,
                model=self.model,
                speed=speed,
                cache_dir=cache_dir,
                audio_path=audio_path,
                input_data=input_data,
                original_text=text
            )
            requests.append(request)

        # Generate all non-cached requests concurrently
        tasks = []
        for i, request in enumerate(requests):
            if request is None:
                # Use cached result
                input_text = remove_bookmarks(texts[i])
                input_data = {
                    "input_text": input_text,
                    "service": "deepinfra_async",
                    "config": {
                        "voice": self.voice,
                        "model": self.model,
                        "speed": speed,
                    },
                }
                cached_result = self.get_cached_result(input_data, cache_dir)
                tasks.append(asyncio.create_task(self._return_cached_result(cached_result, texts[i])))
            else:
                tasks.append(asyncio.create_task(self._generate_single_tts(request)))

        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"TTS generation failed for text {i}: {result}")
                raise result
            
            if isinstance(result, dict):
                # Cached result - ensure it has final_audio key
                if "final_audio" not in result and "original_audio" in result:
                    result["final_audio"] = result["original_audio"]
                final_results.append(result)
            else:
                # TTS result
                if not result.success:
                    raise RuntimeError(f"TTS generation failed for text {i}: {result.error}")
                
                final_results.append({
                    "input_text": result.input_text,
                    "input_data": result.input_data,
                    "original_audio": result.audio_path,
                    "final_audio": result.audio_path,  # Add final_audio key for compatibility
                })
        
        return final_results

    async def _return_cached_result(self, cached_result: dict, original_text: str) -> dict:
        """Helper to return cached result in async context"""
        return cached_result

    async def _generate_single_tts(self, request: TTSRequest) -> TTSResult:
        """Generate a single TTS audio file with retry logic and rate limiting"""
        
        # Check if this request is already pending
        request_key = self.get_audio_basename(request.input_data)
        if request_key in self._pending_requests:
            # Wait for the existing request to complete
            try:
                return await self._pending_requests[request_key]
            except Exception as e:
                # If the pending request failed, we'll try again
                pass
        
        # Create a new future for this request
        future = asyncio.Future()
        self._pending_requests[request_key] = future
        
        try:
            async with self.semaphore:  # Limit concurrent requests
                await self.rate_limiter.acquire()  # Rate limiting
                
                for attempt in range(self.max_retries):
                    try:
                        result = await self._make_tts_request(request)
                        future.set_result(result)
                        return result
                    except Exception as e:
                        if attempt == self.max_retries - 1:
                            error_result = TTSResult(
                                success=False,
                                audio_path=request.audio_path,
                                input_text=request.original_text,
                                input_data=request.input_data,
                                error=str(e)
                            )
                            future.set_result(error_result)
                            return error_result
                        
                        # Exponential backoff
                        wait_time = 2 ** attempt
                        logger.warning(f"TTS request failed (attempt {attempt + 1}), retrying in {wait_time}s: {e}")
                        await asyncio.sleep(wait_time)
        
        finally:
            # Clean up pending request
            self._pending_requests.pop(request_key, None)

    async def _make_tts_request(self, request: TTSRequest) -> TTSResult:
        """Make the actual TTS API request"""
        if self.api_key is None:
            raise ValueError("API key is required for TTS generation")

        # Use aiohttp for async HTTP requests
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": request.model,
                "voice": request.voice,
                "input": request.text,
                "response_format": "mp3",
                "speed": request.speed
            }
            
            url = f"{self.base_url}/audio/speech"
            
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(f"API request failed with status {response.status}: {error_text}")
                
                # Save audio file
                audio_file_path = request.cache_dir / request.audio_path
                async with aiofiles.open(audio_file_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        await f.write(chunk)
                
                return TTSResult(
                    success=True,
                    audio_path=request.audio_path,
                    input_text=request.original_text,
                    input_data=request.input_data
                )

    def __del__(self):
        """Cleanup thread pool on destruction"""
        if hasattr(self, 'thread_pool'):
            self.thread_pool.shutdown(wait=False)


def create_dotenv_deepinfra():
    logger.info(
        "Check out https://deepinfra.com/ "
        "to learn how to create an account and get your API key."
    )
    if not create_dotenv_file(["DEEPINFRA_API_KEY"]):
        raise ValueError(
            "The environment variable DEEPINFRA_API_KEY is not set. Please set it "
            "or create a .env file with the variables."
        )
    logger.info("The .env file has been created. Please run Manim again.")
    sys.exit() 