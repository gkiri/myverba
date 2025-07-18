import os
import sys
from pathlib import Path

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
        'Run `pip install "manim-voiceover[openai]"` to use DeepInfraService.'
    )


load_dotenv(find_dotenv(usecwd=True))


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


class DeepInfraService(SpeechService):
    """
    Speech service class for DeepInfra TTS Service using Kokoro TTS model.
    Uses OpenAI-compatible API with DeepInfra's base URL.
    """

    def __init__(
        self,
        voice: str = "af_bella",
        model: str = "hexgrad/Kokoro-82M",
        transcription_model=None,
        api_key: str = None,
        base_url: str = "https://api.deepinfra.com/v1/openai",
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
        """
        prompt_ask_missing_extras("openai", "openai", "DeepInfraService")
        self.voice = voice
        self.model = model
        self.api_key = api_key or os.getenv("DEEPINFRA_API_KEY")
        self.base_url = base_url

        SpeechService.__init__(self, transcription_model=transcription_model, **kwargs)

    def generate_from_text(
        self, text: str, cache_dir: str = None, path: str = None, **kwargs
    ) -> dict:
        """Generate speech from text using DeepInfra's Kokoro TTS model."""
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
            "service": "deepinfra",
            "config": {
                "voice": self.voice,
                "model": self.model,
                "speed": speed,
            },
        }

        cached_result = self.get_cached_result(input_data, cache_dir)
        if cached_result is not None:
            return cached_result

        if path is None:
            audio_path = self.get_audio_basename(input_data) + ".mp3"
        else:
            audio_path = path

        if self.api_key is None:
            create_dotenv_deepinfra()

        # Create OpenAI client with DeepInfra configuration
        client = openai.OpenAI(
            base_url=self.base_url,
            api_key=self.api_key
        )

        # Use streaming response as shown in the DeepInfra example
        with client.audio.speech.with_streaming_response.create(
            model=self.model,
            voice=self.voice,
            input=input_text,
            response_format="mp3",
            speed=speed,
        ) as response:
            response.stream_to_file(str(cache_dir / audio_path))

        json_dict = {
            "input_text": text,
            "input_data": input_data,
            "original_audio": audio_path,
        }

        return json_dict 