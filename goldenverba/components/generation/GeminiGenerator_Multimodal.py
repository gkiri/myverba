import os
import base64
from wasabi import msg

try:
    import vertexai.preview
    from vertexai.preview.generative_models import GenerativeModel, Content, Part
except ImportError as e:  # Catch the specific ImportError
    msg.fail(f"Could not import necessary Vertex AI libraries: {e}")
    raise  # Re-raise the error so it's not ignored


from dotenv import load_dotenv

from goldenverba.components.interfaces import Generator

load_dotenv()


class GeminiGenerator_Multimodal(Generator):
    """
    Gemini Generator.
    """

    def __init__(self):
        super().__init__()
        self.name = "Gemini"
        self.description = "Generator using Google's Gemini 1.5 Pro model"
        self.requires_library = ["vertexai"]
        self.requires_env = [
            "GOOGLE_APPLICATION_CREDENTIALS",
            "GOOGLE_CLOUD_PROJECT",
        ]
        self.streamable = True
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash-002")
        self.context_window = 100000

    async def generate_pdf(
        self,
        prompt: str,
        context: str,
        pdf_data: bytes,
        model_name: str = None,
    ) -> str:
        """Generate analysis from PDF content"""
        try:
            project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
            REGION = "us-central1"
            
            # Initialize Vertex AI
            credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            if credentials_path:
                import google.auth
                credentials, _ = google.auth.load_credentials_from_file(credentials_path)
                vertexai.init(project=project_id, location=REGION, credentials=credentials)
            else:
                vertexai.init(project=project_id, location=REGION)

            # Get model name
            model_name_to_use = model_name if model_name else self.model_name

            # Create model instance
            model = GenerativeModel(model_name_to_use)


            msg.info(f"Before gemini call: ")
            # Generate content
            response = await model.generate_content_async(
                [{'mime_type': 'application/pdf', 'data': pdf_data}, prompt],
                stream=False
            )

            # Return text response directly
            msg.info(f"After gemini call:. Response: {response.text}")
            return response.text

        except Exception as e:
            msg.fail(f"PDF generation failed: {str(e)}")
            raise


