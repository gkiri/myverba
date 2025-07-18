import unittest
from unittest.mock import patch, MagicMock
import os
from pathlib import Path
from manim import *
from manim_voiceover.services.openai import OpenAIService

class TestOpenAIService(unittest.TestCase):
    @patch("manim_voiceover.services.openai.OpenAI")
    @patch("manim_voiceover.services.base.get_cache_dir")
    def test_generate_from_text_with_mock_api(self, mock_get_cache_dir, mock_openai):
        # Setup mock for cache directory
        mock_cache_path = Path("/tmp/mock_cache")
        mock_get_cache_dir.return_value = mock_cache_path

        # Create a mock for the client instance
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        # Create a mock for the response object which has a `stream_to_file` method
        mock_response = MagicMock()
        mock_client.audio.speech.create.return_value = mock_response

        # Instantiate the service, disabling transcription
        service = OpenAIService(voice="alloy", model="tts-1", transcription_model=None)
        
        text = "Hello, world!"
        
        # Call the method to be tested
        result = service.generate_from_text(text)
        
        # 1. Assert that the OpenAI API was called correctly
        mock_client.audio.speech.create.assert_called_once_with(
            model="tts-1",
            voice="alloy",
            input=text,
            response_format="mp3"
        )

        # 2. Assert that the `stream_to_file` method was called on the response
        # This confirms the downloaded audio is being saved.
        self.assertTrue(mock_response.stream_to_file.called)
        
        # 3. Assert that the returned dictionary has the correct structure
        self.assertIn("original_audio", result)
        # The value of "original_audio" should be the path to the cached file
        self.assertIsInstance(result["original_audio"], Path)
        self.assertTrue(str(result["original_audio"]).startswith(str(mock_cache_path)))

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_api_key(self):
        service = OpenAIService(transcription_model=None)
        with self.assertRaises(ValueError) as context:
            # The client is lazy-loaded, so we need to access it to trigger the check.
            _ = service.client
        self.assertTrue("OPENAI_API_KEY environment variable not set" in str(context.exception))


if __name__ == '__main__':
    unittest.main() 