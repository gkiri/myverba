import unittest
import os
import subprocess
from pathlib import Path
from dotenv import load_dotenv

from manim import *
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.openai import OpenAIService

load_dotenv()


class OpenAIExample(VoiceoverScene):
    def construct(self):
        # Disable transcription to avoid unrelated prompts
        self.set_speech_service(
            OpenAIService(
                voice="fable",
                model="tts-1-hd",
                transcription_model=None,
            )
        )

        circle = Circle()
        square = Square().shift(2 * RIGHT)

        with self.voiceover(text="This circle is drawn as I speak.") as tracker:
            self.play(Create(circle), run_time=tracker.duration)

        with self.voiceover(text="Let's shift it to the left 2 units.") as tracker:
            self.play(circle.animate.shift(2 * LEFT), run_time=tracker.duration)

        with self.voiceover(text="Now, let's transform it into a square.") as tracker:
            self.play(Transform(circle, square), run_time=tracker.duration)

        with self.voiceover(
            text="Thank you for watching.", speed=0.75
        ):
            self.play(Uncreate(circle))

        self.wait()


class TestOpenAIIntegration(unittest.TestCase):
    @unittest.skipIf(not os.environ.get("OPENAI_API_KEY"), "OPENAI_API_KEY environment variable not set. Skipping integration test.")
    def test_render_openai_scene(self):
        """
        This is an integration test that renders a Manim scene with a real
        OpenAI TTS API call. It requires the OPENAI_API_KEY to be set.
        """
        script_path = Path(__file__)
        # Manim's default output path for -pql is media/videos/<script_name>/480p15/
        output_file = Path("media/videos") / script_path.stem / "480p15" / "OpenAIExample.mp4"

        # Clean up previous renders to ensure a fresh run
        if output_file.exists():
            output_file.unlink()

        command = [
            "manim",
            "-pql",
            str(script_path),
            "OpenAIExample",
            "--disable_caching",
        ]

        result = subprocess.run(command, capture_output=True, text=True)

        self.assertEqual(result.returncode, 0, f"Manim failed to render scene. Stderr:\\n{result.stderr}")
        self.assertTrue(output_file.exists(), f"Output video file not found after render: {output_file}")


if __name__ == '__main__':
    unittest.main() 