from fastapi import FastAPI, WebSocket, UploadFile, status,HTTPException, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse ,StreamingResponse
from fastapi.staticfiles import StaticFiles
import json
import uuid
import os
from pathlib import Path
from datetime import datetime
import hashlib
import shutil 
import base64
import tempfile

from dotenv import load_dotenv
from starlette.websockets import WebSocketDisconnect
from wasabi import msg  # type: ignore[import]
import time
import random
from goldenverba.components.generation.GPT3Generator import GPT3Generator
from goldenverba.components.generation.GroqGenerator import GroqGenerator
from goldenverba.components.generation.GeminiGenerator import GeminiGenerator
from goldenverba.components.generation.DeepseekGenerator import DeepseekGenerator
#from goldenverba.components.generation.OpenrouterGenerator import OpenrouterGenerator

#from goldenverba.components.generation.GeminiAIStudioGenerator import GeminiGenerator
from goldenverba.server.debug_utils import debug_log, info_log, warn_log, error_log

from goldenverba import verba_manager
from goldenverba.server.types import (
    ResetPayload,
    ConfigPayload,
    QueryPayload,
    GeneratePayload,
    GetDocumentPayload,
    SearchQueryPayload,
    ImportPayload,
)
from goldenverba.server.util import get_config, set_config, setup_managers
from goldenverba.components.types import Question # Add  Question model to types
from pydantic import ValidationError
import goldenverba.server.prompts as prompts
from goldenverba.server.supabase.supabase_client import supabase
import asyncio
import re
from goldenverba.server.api_helpers import (
    fetch_subtopic_content,
    perform_pyqs_search,
    sort_pyqs_by_score,
    filter_top_pyqs_with_llm
)
load_dotenv()

gpt3_generator = GPT3Generator()
groq_generator = GroqGenerator()
gemini_generator = GeminiGenerator()
deepseek_generator = DeepseekGenerator()
#openrouter_generator = OpenrouterGenerator()

async def generate_gpt3_response(prompt: str,context: str) -> str:
    """Helper function to generate LLM response."""
    try:
        full_response = ""
        async for chunk in gpt3_generator.generate_stream([prompt], [context], []):
            if chunk["finish_reason"] == "stop":
                break
            full_response += chunk["message"]
        return full_response
    except Exception as e:
        msg.fail(f"gpt3 API call failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate response: {str(e)}")

async def generate_groq_response(prompt: str,context: str) -> str:
    """Helper function to generate LLM response."""
    try:
        full_response = ""
        async for chunk in groq_generator.generate_stream([prompt], [context], []):
            if chunk["finish_reason"] == "stop":
                break
            full_response += chunk["message"]
        return full_response
    except Exception as e:
        msg.fail(f"groq API call failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate response: {str(e)}")

async def generate_gemini_response(prompt: str, context: str, model_name: str = None) -> str:
    """Helper function to generate LLM response.
    
    Args:
        prompt (str): The prompt to send to the model
        context (str): The context to provide
        model_name (str, optional): Optional model name to override default. Defaults to None.
    """
    try:
        full_response = ""
        async for chunk in gemini_generator.generate_stream([prompt], [context], [], model_name):
            if chunk["finish_reason"] == "stop":
                break
            full_response += chunk["message"]
        return full_response
    except Exception as e:
        msg.fail(f"Gemini API call failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate response: {str(e)}")


async def generate_pdf_nostream_response(prompt: str, pdf_data: bytes, model_name: str = None) -> str:
    """Helper function to generate LLM response for PDF content.
    
    Args:
        prompt (str): The prompt to send to the model
        pdf_data (bytes): The PDF file data in bytes
        model_name (str, optional): Override default model name. Defaults to None.
    
    Returns:
        str: The complete response from the model
        
    Raises:
        HTTPException: If the API call fails
    """
    try:
        full_response = ""
        async for chunk in gemini_generator.generate_pdf_nostream(prompt, pdf_data, model_name=model_name):
            if chunk["finish_reason"] == "stop":
                break
            full_response += chunk["message"]
        return full_response
    except Exception as e:
        msg.fail(f"Gemini PDF API call failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF response: {str(e)}")


async def generate_deepseek_response(prompt: str, context: str, model_name: str = None) -> str:
    """Helper function to generate LLM response.
    
    Args:
        prompt (str): The prompt to send to the model
        context (str): The context to provide
        model_name (str, optional): Optional model name to override default. Defaults to None.
    """
    try:
        full_response = ""
        async for chunk in deepseek_generator.generate_stream([prompt], [context], [], model_name):
            if chunk["finish_reason"] == "stop":
                break
            full_response += chunk["message"]
        return full_response
    except Exception as e:
        msg.fail(f"deepseek API call failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate response: {str(e)}")


# async def generate_gemini_response(prompt, context):
#     try:
#         full_response = ""
#         async for chunk in openrouter_generator.generate_stream([prompt], [context], []):
#             msg.info(f"Chunk received: {chunk}")  # Log the chunk
#             if chunk.get("finish_reason") == "stop":
#                 msg.info("Finish reason: stop")
#                 break
#             message = chunk.get("message", "")
#             msg.info(f"Message received: {message}")  # Log the message extracted from the chunk
#             full_response += message
#         msg.info(f"Full response: {full_response}")  # Log the full response

#         return full_response
#     except Exception as e:
#         msg.fail(f"Error in generate_gemini_response: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Failed to generate Gemini response: {str(e)}")

# Check if runs in production
production_key = os.environ.get("VERBA_PRODUCTION", "")
tag = os.environ.get("VERBA_GOOGLE_TAG", "")
if production_key == "True":
    msg.info("API runs in Production Mode")
    production = True
else:
    production = False

manager = verba_manager.VerbaManager()
setup_managers(manager)

# FastAPI App
app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "https://verba-golden-ragtriever.onrender.com",
    "http://localhost:8000",
    "http://localhost:8080",
    "http://3.83.67.48:8000",
    "http://3.89.115.184:8000",
    "http://3.84.81.112:8000",
    "https://gkiri-vercel-deploy.vercel.app",
    "https://*.vercel.app",
    "http://54.224.217.30:8000",
    "http://54.224.217.30:8080",
    "http://3.84.172.214:8080",
    "https://*.lovable.app",
    "https://preview--conversational-insight-panel.lovable.app",
    "https://preview--lovable-connectify.lovable.app",
]

# Add middleware for handling Cross Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"^https?://(3|5)\..*|^https://preview-[a-zA-Z0-9-]+--.*\.lovable\.app$",  # Updated regex pattern
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent

# Serve the assets (JS, CSS, images, etc.)
app.mount(
    "/static/_next",
    StaticFiles(directory=BASE_DIR / "frontend/out/_next"),
    name="next-assets",
)

# Serve the main page and other static files
app.mount("/static", StaticFiles(directory=BASE_DIR / "frontend/out"), name="app")


@app.get("/")
@app.head("/")
async def serve_frontend():
    return FileResponse(os.path.join(BASE_DIR, "frontend/out/index.html"))

### GET

# Define health check endpoint
@app.get("/api/health")
async def health_check():
    try:
        if manager.client.is_ready():
            return JSONResponse(
                content={"message": "Alive!", "production": production, "gtag": tag}
            )
        else:
            return JSONResponse(
                content={
                    "message": "Database not ready!",
                    "production": production,
                    "gtag": tag,
                },
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
    except Exception as e:
        msg.fail(f"Healthcheck failed with {str(e)}")
        return JSONResponse(
            content={
                "message": f"Healthcheck failed with {str(e)}",
                "production": production,
                "gtag": tag,
            },
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

# Get Status meta data
@app.get("/api/get_status")
async def get_status():
    try:
        schemas = manager.get_schemas()
        sorted_schemas = dict(
            sorted(schemas.items(), key=lambda item: item[1], reverse=True)
        )

        sorted_libraries = dict(
            sorted(
                manager.installed_libraries.items(),
                key=lambda item: (not item[1], item[0]),
            )
        )
        sorted_variables = dict(
            sorted(
                manager.environment_variables.items(),
                key=lambda item: (not item[1], item[0]),
            )
        )

        data = {
            "type": manager.weaviate_type,
            "libraries": sorted_libraries,
            "variables": sorted_variables,
            "schemas": sorted_schemas,
            "error": "",
        }

        msg.info("Status Retrieved")
        return JSONResponse(content=data)
    except Exception as e:
        data = {
            "type": "",
            "libraries": {},
            "variables": {},
            "schemas": {},
            "error": f"Status retrieval failed: {str(e)}",
        }
        msg.fail(f"Status retrieval failed: {str(e)}")
        return JSONResponse(content=data)

# Get Configuration
@app.get("/api/config")
async def retrieve_config():
    try:
        config = get_config(manager)
        msg.info("Config Retrieved")
        return JSONResponse(status_code=200, content={"data": config, "error": ""})

    except Exception as e:
        msg.warn(f"Could not retrieve configuration: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "data": {},
                "error": f"Could not retrieve configuration: {str(e)}",
            },
        )

### WEBSOCKETS

@app.websocket("/ws/generate_stream")
async def websocket_generate_stream(websocket: WebSocket):
    await websocket.accept()
    while True:  # Start a loop to keep the connection alive.
        try:
            data = await websocket.receive_text()
            # Parse and validate the JSON string using Pydantic model
            payload = GeneratePayload.model_validate_json(data)
            msg.good(f"Received generate stream call for {payload.query}")
            full_text = ""
            async for chunk in manager.generate_stream_answer(
                [payload.query], [payload.context], payload.conversation
            ):
                full_text += chunk["message"]
                if chunk["finish_reason"] == "stop":
                    chunk["full_text"] = full_text
                await websocket.send_json(chunk)

        except WebSocketDisconnect:
            msg.warn("WebSocket connection closed by client.")
            break  # Break out of the loop when the client disconnects

        except Exception as e:
            msg.fail(f"WebSocket Error: {str(e)}")
            await websocket.send_json(
                {"message": e, "finish_reason": "stop", "full_text": str(e)}
            )
        msg.good("Succesfully streamed answer")

### POST

# Reset Verba
@app.post("/api/reset")
async def reset_verba(payload: ResetPayload):
    if production:
        return JSONResponse(status_code=200, content={})

    try:
        if payload.resetMode == "VERBA":
            manager.reset()
        elif payload.resetMode == "DOCUMENTS":
            manager.reset_documents()
        elif payload.resetMode == "CACHE":
            manager.reset_cache()
        elif payload.resetMode == "SUGGESTIONS":
            manager.reset_suggestion()
        elif payload.resetMode == "CONFIG":
            manager.reset_config()

        msg.info(f"Resetting Verba ({payload.resetMode})")

    except Exception as e:
        msg.warn(f"Failed to reset Verba {str(e)}")

    return JSONResponse(status_code=200, content={})

# Receive query and return chunks and query answer
@app.post("/api/import")
async def import_data(payload: ImportPayload):

    logging = []

    if production:
        logging.append(
            {"type": "ERROR", "message": "Can't import when in production mode"}
        )
        return JSONResponse(
            content={
                "logging": logging,
            }
        )

    try:
        set_config(manager, payload.config)
        documents, logging = manager.import_data(
            payload.data, payload.textValues, logging
        )

        return JSONResponse(
            content={
                "logging": logging,
            }
        )

    except Exception as e:
        logging.append({"type": "ERROR", "message": str(e)})
        return JSONResponse(
            content={
                "logging": logging,
            }
        )

@app.post("/api/set_config")
async def update_config(payload: ConfigPayload):

    if production:
        return JSONResponse(
            content={
                "status": "200",
                "status_msg": "Config can't be updated in Production Mode",
            }
        )

    try:
        set_config(manager, payload.config)
    except Exception as e:
        msg.warn(f"Failed to set new Config {str(e)}")

    return JSONResponse(
        content={
            "status": "200",
            "status_msg": "Config Updated",
        }
    )

# Receive query and return chunks and query answer
@app.post("/api/query")
async def query(payload: QueryPayload):
    msg.good(f"Received query: {payload.query}")
    start_time = time.time()  # Start timing
    try:
        chunks, context = manager.retrieve_chunks([payload.query])

        retrieved_chunks = [
            {
                "text": chunk.text,
                "doc_name": chunk.doc_name,
                "chunk_id": chunk.chunk_id,
                "doc_uuid": chunk.doc_uuid,
                "doc_type": chunk.doc_type,
                "score": chunk.score,
            }
            for chunk in chunks
        ]

        elapsed_time = round(time.time() - start_time, 2)  # Calculate elapsed time
        msg.good(f"Succesfully processed query: {payload.query} in {elapsed_time}s")

        if len(chunks) == 0:
            return JSONResponse(
                content={
                    "chunks": [],
                    "took": 0,
                    "context": "",
                    "error": "No Chunks Available",
                }
            )

        return JSONResponse(
            content={
                "error": "",
                "chunks": retrieved_chunks,
                "context": context,
                "took": elapsed_time,
            }
        )

    except Exception as e:
        msg.warn(f"Query failed: {str(e)}")
        return JSONResponse(
            content={
                    "chunks": [],
                    "took": 0,
                    "context": "",
                    "error": f"Something went wrong: {str(e)}",
            }
        )

# Retrieve auto complete suggestions based on user input
@app.post("/api/suggestions")
async def suggestions(payload: QueryPayload):
    try:
        suggestions = manager.get_suggestions(payload.query)

        return JSONResponse(
            content={
                "suggestions": suggestions,
            }
        )
    except Exception:
        return JSONResponse(
            content={
                "suggestions": [],
            }
        )

# Retrieve specific document based on UUID
@app.post("/api/get_document")
async def get_document(payload: GetDocumentPayload):
    # TODO Standarize Document Creation
    msg.info(f"Document ID received: {payload.document_id}")

    try:
        document = manager.retrieve_document(payload.document_id)
        document_properties = document.get("properties", {})
        document_obj = {
            "class": document.get("class", "No Class"),
            "id": document.get("id", payload.document_id),
            "chunks": document_properties.get("chunk_count", 0),
            "link": document_properties.get("doc_link", ""),
            "name": document_properties.get("doc_name", "No name"),
            "type": document_properties.get("doc_type", "No type"),
            "text": document_properties.get("text", "No text"),
            "timestamp": document_properties.get("timestamp", ""),
        }

        msg.good(f"Succesfully retrieved document: {payload.document_id}")
        return JSONResponse(
            content={
                "error": "",
                "document": document_obj,
            }
        )
    except Exception as e:
        msg.fail(f"Document retrieval failed: {str(e)}")
        return JSONResponse(
            content={
                "error": str(e),
                "document": None,
            }
        )

## Retrieve and search documents imported to Weaviate
@app.post("/api/get_all_documents")
async def get_all_documents(payload: SearchQueryPayload):
    # TODO Standarize Document Creation
    msg.info("Get all documents request received")
    start_time = time.time()  # Start timing

    try:
        if payload.query == "":
            documents = manager.retrieve_all_documents(
                payload.doc_type, payload.page, payload.pageSize
            )
        else:
            documents = manager.search_documents(
                payload.query, payload.doc_type, payload.page, payload.pageSize
            )

        if not documents:
            return JSONResponse(
                content={
                    "documents": [],
                    "doc_types": [],
                    "current_embedder": manager.embedder_manager.selected_embedder,
                    "error": f"No Results found!",
                    "took": 0,
                }
            )

        documents_obj = []
        for document in documents:

            _additional = document["_additional"]

            documents_obj.append(
                {
                    "class": "No Class",
                    "uuid": _additional.get("id", "none"),
                    "chunks": document.get("chunk_count", 0),
                    "link": document.get("doc_link", ""),
                    "name": document.get("doc_name", "No name"),
                    "type": document.get("doc_type", "No type"),
                    "text": document.get("text", "No text"),
                    "timestamp": document.get("timestamp", ""),
                }
            )

        elapsed_time = round(time.time() - start_time, 2)  # Calculate elapsed time
        msg.good(
            f"Succesfully retrieved document: {len(documents)} documents in {elapsed_time}s"
        )

        doc_types = manager.retrieve_all_document_types()

        return JSONResponse(
            content={
                "documents": documents_obj,
                "doc_types": list(doc_types),
                "current_embedder": manager.embedder_manager.selected_embedder,
                "error": "",
                "took": elapsed_time,
            }
        )
    except Exception as e:
        msg.fail(f"All Document retrieval failed: {str(e)}")
        return JSONResponse(
            content={
                "documents": [],
                "doc_types": [],
                "current_embedder": manager.embedder_manager.selected_embedder,
                "error": f"All Document retrieval failed: {str(e)}",
                "took": 0,
            }
        )

# Delete specific document based on UUID
@app.post("/api/delete_document")
async def delete_document(payload: GetDocumentPayload):
    if production:
        msg.warn("Can't delete documents when in Production Mode")
        return JSONResponse(status_code=200, content={})

    msg.info(f"Document ID received: {payload.document_id}")

    manager.delete_document_by_id(payload.document_id)
    return JSONResponse(content={})

###########################################Gkiri
@app.post("/api/upload_mock_exam")
async def upload_mock_exam(file: UploadFile):
    if production:
        raise HTTPException(status_code=403, detail="Uploading mocks is disabled in production mode.")

    try:
        content = await file.read()
        data = json.loads(content.decode("utf-8"))  # Decode bytes to string then to JSON
        
        if not isinstance(data, list):
            raise ValueError("Invalid JSON format. Expected a list of questions.")
        
        # Validate question structure within the list
        for question_data in data:
            try:
                Question(**question_data)  # Attempt to create a Question object
            except ValidationError as e: 
                raise ValueError(f"Invalid question data: {e}")

        with manager.client.batch as batch:
            batch.batch_size = 100  # Set batch size
            for question_data in data:
                question_data['global_questionID'] = int(question_data['global_questionID'])
                #question_data['year'] = int(question_data['year'])
                question = Question(**question_data)
                properties = question.model_dump() 
                manager.client.batch.add_data_object(properties, "MockExamQuestion")
        msg.good(f"Successfully uploaded and imported {len(data)} mock exam questions.")
        return JSONResponse(content={"message": "Success"})
    except Exception as e:
        msg.fail(f"Error uploading or importing mock exam data: {e}")
        raise HTTPException(status_code=500, detail=str(e))  # Return detailed errors

# Gkiri new api
# @app.get("/api/mock_exam")
# async def get_mock_exam_data():
#     # Retrieve random 30 questions from Weaviate
#     try:
#         results = (
#             manager.client.query.get(
#                 "MockExamQuestion",
#                 ["question", "options", "answer_key", "year", "topic", "description", "question_number","global_questionID"],
#             )
#             .with_limit(100)
#             .do()
#         )
#         print("Results Format:", results)
#         if "data" in results and "Get" in results["data"] and "MockExamQuestion" in results["data"]["Get"]:
#             questions = [Question(**question_data).dict() for question_data in results["data"]["Get"]["MockExamQuestion"]]
#             mock_exam_data = {"questions": questions}
#             return JSONResponse(content=mock_exam_data)
#         else:
#             return JSONResponse(status_code=500, content={"error": "Unexpected data structure in results"})
#     except Exception as e:
#         msg.fail(f"Error retrieving mock exam questions: {e}")
#         return JSONResponse(status_code=500, content={"error": str(e)})

import random
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from wasabi import msg

@app.get("/api/mock_exam")
async def get_mock_exam_data():
    try:
        QUESTIONS_TO_RETRIEVE = 100

        # Get total count of questions
        count_result = (
            manager.client.query
            .aggregate("MockExamQuestion")
            .with_meta_count()
            .do()
        )
        
        total_questions = count_result['data']['Aggregate']['MockExamQuestion'][0]['meta']['count']

        # Retrieve all global_questionIDs
        id_results = (
            manager.client.query
            .get("MockExamQuestion", ["global_questionID"])
            .with_additional(["id"])
            .with_limit(total_questions)
            .do()
        )
        
        all_question_ids = [q["global_questionID"] for q in id_results["data"]["Get"]["MockExamQuestion"]]
        
        # Randomly select 100 unique question IDs
        selected_ids = random.sample(all_question_ids, min(QUESTIONS_TO_RETRIEVE, len(all_question_ids)))
        

        # Retrieve the selected questions
        results = (
            manager.client.query.get(
                "MockExamQuestion",
                ["question", "options", "answer_key", "year", "topic", "description", "question_number", "global_questionID"]
            )
            .with_where({
                "path": ["global_questionID"],
                "operator": "ContainsAny",
                "valueNumber": selected_ids
            })
            .with_limit(QUESTIONS_TO_RETRIEVE)
            .do()
        )
        
        if "data" in results and "Get" in results["data"] and "MockExamQuestion" in results["data"]["Get"]:
            questions = [Question(**question_data).dict() for question_data in results["data"]["Get"]["MockExamQuestion"]]
            mock_exam_data = {"questions": questions}
            #print("mock_exam_data Format:", mock_exam_data)
            return JSONResponse(content=mock_exam_data)
        else:
            return JSONResponse(status_code=500, content={"error": "Unexpected data structure in results"})
    except Exception as e:
        msg.fail(f"Error retrieving mock exam questions: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})
    
# New routes for bullet points, summarize, and visualize (without chunk retrieval)
# @app.post("/api/bullet_points")
# async def bullet_points(payload: QueryPayload):
#     print("Gkiri:bullet_points Format:", payload.query)
#     msg.good(f"Received bullet points request: {payload.query}")
#     try:
#         # Construct prompt directly with user input
#         prompt = f"Generate bullet points for the following: {payload.query}"

#         # Generate bullet points (no context needed)
#         bullet_points_response = await manager.generate_answer([prompt], [], []) 

#         return JSONResponse(content={"bullet_points": bullet_points_response})

#     except Exception as e:
#         msg.warn(f"Bullet points generation failed: {str(e)}")
#         return JSONResponse(
#             content={"error": f"Bullet points generation failed: {str(e)}"}
#         )


# @app.post("/api/summarize")
# async def summarize(payload: QueryPayload):
#     print("Gkiri:summarize Format:", payload.query)
#     msg.good(f"Received summarize request: {payload.query}")
#     try:
#         # Construct prompt directly with user input
#         prompt = f"Summarize the following: {payload.query}"

#         # Generate summary (no context needed)
#         summary_response = await manager.generate_answer([prompt], [], [])

#         return JSONResponse(content={"summary": summary_response})

#     except Exception as e:
#         msg.warn(f"Summarization failed: {str(e)}")
#         return JSONResponse(content={"error": f"Summarization failed: {str(e)}"})


# @app.post("/api/visualize")
# async def visualize(payload: QueryPayload):
#     print("Gkiri:visualize Format:", payload.query)
#     msg.good(f"Received visualize request: {payload.query}")
#     try:
#         # Construct prompt directly with user input
#         prompt = f"Generate a Mermaid code block to visualize the following: {payload.query}. Provide only the Mermaid code without any explanations."

#         # Generate Mermaid code (no context needed)
#         mermaid_response = await manager.generate_answer([prompt], [], [])

#         return JSONResponse(content={"mermaid_code": mermaid_response})

#     except Exception as e:
#         msg.warn(f"Visualization failed: {str(e)}")
#         return JSONResponse(content={"error": f"Visualization failed: {str(e)}"})
    
    
    
@app.post("/api/bullet_points")
async def bullet_points(payload: QueryPayload):
    
    debug_log(f"Received bullet points request: {payload.query}")
    
    try:
        #prompt = f"you will be given topic/text/ ,please generate concise bullet points for the following topic: {payload.query}"
        prompt = "you will be given topic/text/ ,please generate concise bullet points for the following topic:"

        #bullet_points_response = await generate_groq_response(prompt,payload.query)
        bullet_points_response = await generate_gemini_response(prompt, payload.query)
        debug_log("Gkiri:LLM output:", bullet_points_response)
        return JSONResponse(content={"bullet_points": bullet_points_response})
    except HTTPException as e:
        raise e
    except Exception as e:
        msg.warn(f"Bullet points generation failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Bullet points generation failed: {str(e)}"}
        )

@app.post("/api/summarize")
async def summarize(payload: QueryPayload):
    
    debug_log(f"Received summarize request: {payload.query}")
    
    try:
        #prompt = f"Provide a concise summary of the following: {payload.query}"
        prompt = "You are AI Mentor for UPSC Exam preparing students , who helps in providing a concise summary of the below given content: "
        #summary_response = await generate_groq_response(prompt,payload.query)
        summary_response = await generate_gemini_response(prompt, payload.query)

        debug_log("Gkiri:LLM output:", summary_response)
        return JSONResponse(content={"summary": summary_response})
    except HTTPException as e:
        raise e
    except Exception as e:
        msg.warn(f"Summarization failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Summarization failed: {str(e)}"}
        )

@app.post("/api/visualize")
async def visualize(payload: QueryPayload):
    
    debug_log(f"Received visualize request: {payload.query}")
    
    try:
        #prompt = f"Generate a Mermaid diagram code to visualize the following concept: {payload.query}. Provide only the Mermaid code without any explanations."
        #prompt = "Generate a Mermaid diagram code to visualize the following concept: Provide only the Mermaid code without any explanations."

        #prompt = "You are an assistant to help user build diagram with Mermaid.You only need to return the output Mermaid code block.Do not include any description, do not include the Code (no ```).";
        
        summary_prompt = prompts.get_prompt("VISUALIZE", topic=payload.query)

        #mermaid_response = await generate_gpt3_response(summary_prompt,payload.query)
        #mermaid_response = await generate_groq_response(summary_prompt,payload.query)
        mermaid_response = await generate_deepseek_response(summary_prompt,payload.query)
        debug_log("Gkiri:LLM output:", mermaid_response)
        return JSONResponse(content={"mermaid_code": mermaid_response})
    except HTTPException as e:
        raise e
    except Exception as e:
        msg.warn(f"Visualization failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Visualization failed: {str(e)}"}
        )

########################################AI Mentor ########################################
# New API Endpoint: Get Syllabus Chapter with User Status

from typing import Optional
from pydantic import BaseModel

class GetSyllabusChapterRequest(BaseModel):
    user_id: str
    chapter_id: str
    
class GetSyllabusChapterQueryRequest(BaseModel):
    user_id: str
    chapter_id: str
    query: str

class SyllabusChapterResponse(BaseModel):
    user_progress: dict
    llm_response: str

### SUbtopic section
class GetSyllabusSubtopicRequest(BaseModel):
    user_id: str
    subtopic_id: str
    
class GetSyllabusSubtopicQueryRequest(BaseModel):
    user_id: str
    subtopic_id: str
    query: str

class SyllabusSubtopicResponse(BaseModel):
    llm_response: str

class GetVisualizeContentRequest(BaseModel):
    user_id: str
    subtopic_id: str
    content: str

# use this for multi diagram one shot
class GetVisualizeContentComboRequest(BaseModel):
    user_id: str
    subtopic_id: str
    content: str
    model_id: int 

class GetVisualizeSubtopicComboRequest(BaseModel):
    user_id: str
    subtopic_id: str
    model_id: int 

class GetSummarizeContentRequest(BaseModel):
    user_id: str
    subtopic_id: str
    content: str
    model_id: int 

class GetPYQSContentRequest(BaseModel):
    user_id: str
    subtopic_id: str
    content: str

class GetPYQSsubtopicContentRequest(BaseModel):
    user_id: str
    subtopic_id: str
    count: int

class GetQuizSubtopicRequest(BaseModel):
    user_id: str
    subtopic_id: str
    count: int
    model_id: int 

class GetSuggestContentRequest(BaseModel):
    user_id: str
    subtopic_id: str
    content: str
    count: int
    model_id: int 


# @app.post("/api/get_syllabus_chapter_with_userstatus")
# async def get_syllabus_chapter_with_userstatus(request: GetSyllabusChapterRequest):
#     debug_log(f"Received get_syllabus_chapter_with_userstatus request: {request}")
#     try:
#         # 1. Fetch chapter content from Weaviate
#         chapter_id = request.chapter_id
#         user_id = request.user_id

#         msg.info(f"Fetching content for Chapter ID: {chapter_id} for User ID: {user_id}")

#         # Assuming manager.weaviate_client is the Weaviate client
#         # chapter_query = {
#         #     "class_name": "VERBA_Syllabus_Chapters",
#         #     "where": {
#         #         "path": ["ch_id"],
#         #         "operator": "Equal",
#         #         "valueText": chapter_id
#         #     }
#         # }
#         chapter_query = (
#             manager.client.query
#             .get("VERBA_Syllabus_Chapters", ["chapter_content"])  # Class name and fields to retrieve
#             .with_where({
#                 "path": ["ch_id"],
#                 "operator": "Equal",
#                 "valueString": chapter_id
#             })
#             .with_limit(1)
#             .do()
#         )

#         #print("Gkiri:chapter_query Format:", chapter_query)
#         #msg.info(f"Gkiri: chapter_query: {chapter_query} ")
#         # Check for the result
#         if not chapter_query["data"]["Get"]["VERBA_Syllabus_Chapters"]:
#             raise HTTPException(status_code=404, detail="Chapter not found")

#         #chapter_result = manager.client.query.get(**chapter_query).with_limit(1).do()

#         chapter_content = chapter_query["data"]["Get"]["VERBA_Syllabus_Chapters"][0].get("chapter_content", "")

#         # 2. Fetch user progress from Supabase
#         user_progress = await get_user_chapter_progress(user_id, chapter_id)

#         #msg.info(f"Gkiri: user_progress: {user_progress} ")
#         # 3. Get relevant prompt
#         #prompt_template = "Provide a personalized learning plan based on the user's progress and the chapter content."

#         # You can customize the prompt as needed, possibly using predefined prompts
#         #prompt = f"{prompt_template}\n\nChapter Content:\n{chapter_content}\n\nUser Progress:\n{json.dumps(user_progress)}"
        
#         conversation_history ="No previous conversation history."
#         # 4. Generate the prompt using the function
#         prompt = prompts.generate_prompt_chapter_user(
#             chapter_id=chapter_id,
#             user_id=user_id,
#             chapter_content=chapter_content,
#             user_progress_data=user_progress,
#             conversation_history=conversation_history
#         )

#         # 4. Call LLM API
#         llm_response = await generate_gemini_response(prompt, chapter_content)
        
#         # Test chapter
#         #llm_response = await generate_gemini_response(prompt, test_chapter)


#         msg.info(f"Gkiri: Gemini llm_response: {llm_response} ")

#         return SyllabusChapterResponse(
#             user_progress=user_progress,
#             llm_response=llm_response
#         )

#     except HTTPException as he:
#         raise he
#     except Exception as e:
#         msg.fail(f"Error in get_syllabus_chapter_with_userstatus: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# async def get_user_chapter_progress(user_id: str, chapter_id: str) -> dict:
#     debug_log(f"Fetching user progress for Chapter ID: {chapter_id} for User ID: {user_id}")
#     try:
#         response = await asyncio.get_event_loop().run_in_executor(
#             None, lambda: supabase.table("gs1_progress").select("*").eq("user_id", user_id).single().execute()
#         )
#         if response.data:
#             user_progress = response.data
#             chapter_progress = user_progress.get(chapter_id, {})
#             return chapter_progress
#         else:
#             msg.warn(f"No progress found for user_id: {user_id}, chapter_id: {chapter_id}")
#             return {}
#     except Exception as e:
#         msg.warn(f"Failed to retrieve user progress for Chapter ID {chapter_id}: {e}")
#         return {}


# @app.post("/api/get_syllabus_chapter_with_userstatus_query")
# async def get_syllabus_chapter_with_userstatus_query(request: GetSyllabusChapterQueryRequest):
#     debug_log(f"Received get_syllabus_chapter_with_userstatus_query request: {request}")
#     try:
#         chapter_id = request.chapter_id
#         user_id = request.user_id
#         query = request.query

#         msg.info(f"Fetching content for Chapter ID: {chapter_id} for User ID: {user_id} with query: {query}")

#         # Fetch chapter content from Weaviate
#         chapter_query = (
#             manager.client.query
#             .get("VERBA_Syllabus_Chapters", ["chapter_content"])
#             .with_where({
#                 "path": ["ch_id"],
#                 "operator": "Equal",
#                 "valueString": chapter_id
#             })
#             .with_limit(1)
#             .do()
#         )

#         if not chapter_query["data"]["Get"]["VERBA_Syllabus_Chapters"]:
#             raise HTTPException(status_code=404, detail="Chapter not found")

#         chapter_content = chapter_query["data"]["Get"]["VERBA_Syllabus_Chapters"][0].get("chapter_content", "")

#         # Fetch user progress from Supabase
#         user_progress = await get_user_chapter_progress(user_id, chapter_id)

#         conversation_history = "No previous conversation history."
        
#         # Generate the prompt using the function
#         prompt = prompts.generate_prompt_chapter_user_query(
#             chapter_id=chapter_id,
#             user_id=user_id,
#             chapter_content=chapter_content,
#             user_progress_data=user_progress,
#             conversation_history=conversation_history,
#             user_query=query
#         )

#         # Call LLM API
#         llm_response = await generate_gemini_response(prompt, chapter_content)

#         return SyllabusChapterResponse(
#             user_progress=user_progress,
#             llm_response=llm_response
#         )
#     except Exception as e:
#         msg.error(f"Error in get_syllabus_chapter_with_userstatus_query: {str(e)}")
#         raise HTTPException(status_code=500, detail=str(e))



"""
Get Syllabus Subtopic API Endpoint

This endpoint retrieves a subtopic's content and generates an AI mentor response based on the subtopic content.

Parameters:
    request (GetSyllabusSubtopicRequest): Request object containing:
        - user_id (str): ID of the user making the request
        - subtopic_id (str): ID of the subtopic to retrieve

Returns:
    SyllabusSubtopicResponse: Response object containing:
        - llm_response (str): AI mentor's response based on the subtopic content

Raises:
    HTTPException: 
        - 404 if subtopic not found
        - 500 for other server errors

Flow:
1. Extracts chapter_id from subtopic_id
2. Fetches chapter name from Weaviate
3. Fetches subtopic content from Weaviate
4. Generates AI mentor prompt
5. Gets LLM response
6. Returns formatted response
"""


## Default retrieve subtopic based on subtopic_id
# @app.post("/api/get_syllabus_subtopic")
# async def get_syllabus_subtopic(request: GetSyllabusSubtopicRequest):
#     debug_log(f"Received get_syllabus_subtopic request: {request}")
#     try:
#         subtopic_id = request.subtopic_id
#         user_id = request.user_id

#         msg.info(f"Fetching content for Subtopic ID: {subtopic_id} for User ID: {user_id}")

#         # Extract chapter_id from subtopic_id
#         chapter_id = subtopic_id.split('_')[0]
#         msg.info(f"Extracted chapter_id: {chapter_id} from subtopic_id: {subtopic_id}")

#         # Fetch chapter name from Weaviate
#         # Verify chapter exists and get chapter name
#         chapter_query = (
#             manager.client.query
#             .get("VERBA_Syllabus_Chapters", ["chapter_name"])
#             .with_where({
#                 "path": ["ch_id"],
#                 "operator": "Equal",
#                 "valueString": chapter_id
#             })
#             .with_limit(1)
#             .do()
#         )

#         chapter_name = chapter_query["data"]["Get"]["VERBA_Syllabus_Chapters"][0]["chapter_name"]
        
#         # Fetch chapter content from Weaviate
#         subtopic_query = (
#             manager.client.query
#             .get("VERBA_Syllabus_Subtopics", ["subtopic_content"])
#             .with_where({
#                 "path": ["subtopic_id"],
#                 "operator": "Equal",
#                 "valueString": subtopic_id
#             })
#             .with_limit(1)
#             .do()
#         )

#         if not subtopic_query["data"]["Get"]["VERBA_Syllabus_Subtopics"]:
#             raise HTTPException(status_code=404, detail="subtopic not found")

#         subtopic_content = subtopic_query["data"]["Get"]["VERBA_Syllabus_Subtopics"][0].get("subtopic_content", "")

#         conversation_history = "No previous conversation history."
        
#         subtopic_name= ''
#         # Generate the prompt using the function
#         prompt = prompts.create_subtopic_mentor_prompt(
#             subtopic_content=subtopic_content,
#             chapter_name=chapter_name,
#             subtopic_name=subtopic_name,
#             #conversation_history=conversation_history,
#         )

#         # Call LLM API
#         llm_response = await generate_gemini_response(prompt, "") #2nd arg is context which is alread injected in prompt

#         return SyllabusSubtopicResponse(
#             llm_response=llm_response
#         )
#     except Exception as e:
#         msg.error(f"Error in get_syllabus_subtopic: {str(e)}")
#         raise HTTPException(status_code=500, detail=str(e))


# @app.post("/api/get_syllabus_subtopic_with_query")
# async def get_syllabus_subtopic_with_query(request: GetSyllabusSubtopicQueryRequest):
#     debug_log(f"Received get_syllabus_subtopic_with_query request: {request}")
#     try:
#         subtopic_id = request.subtopic_id
#         user_id = request.user_id
#         query = request.query

#         msg.info(f"Fetching content for Subtopic ID: {subtopic_id} for User ID: {user_id} with query: {query}")

#         # Extract chapter_id from subtopic_id
#         chapter_id = subtopic_id.split('_')[0]
#         msg.info(f"Extracted chapter_id: {chapter_id} from subtopic_id: {subtopic_id}")

#         # Fetch chapter name from Weaviate
#         # Verify chapter exists and get chapter name
#         chapter_query = (
#             manager.client.query
#             .get("VERBA_Syllabus_Chapters", ["chapter_name"])
#             .with_where({
#                 "path": ["ch_id"],
#                 "operator": "Equal",
#                 "valueString": chapter_id
#             })
#             .with_limit(1)
#             .do()
#         )

#         chapter_name = chapter_query["data"]["Get"]["VERBA_Syllabus_Chapters"][0]["chapter_name"]
        
#         # Fetch chapter content from Weaviate
#         subtopic_query = (
#             manager.client.query
#             .get("VERBA_Syllabus_Subtopics", ["subtopic_content"])
#             .with_where({
#                 "path": ["subtopic_id"],
#                 "operator": "Equal",
#                 "valueString": subtopic_id
#             })
#             .with_limit(1)
#             .do()
#         )

#         if not subtopic_query["data"]["Get"]["VERBA_Syllabus_Subtopics"]:
#             raise HTTPException(status_code=404, detail="subtopic not found")

#         subtopic_content = subtopic_query["data"]["Get"]["VERBA_Syllabus_Subtopics"][0].get("subtopic_content", "")

#         conversation_history = "No previous conversation history."
        
#         subtopic_name=''
#         # Generate the prompt using the function
#         prompt = prompts.create_subtopic_mentor_prompt_followup(
#             subtopic_content=subtopic_content,
#             chapter_name=chapter_name,
#             subtopic_name=subtopic_name,
#             #conversation_history=conversation_history,
#             user_query=query
#         )

#         # Call LLM API
#         llm_response = await generate_gemini_response(prompt, "") #2nd arg is context which is alread injected in prompt

#         return SyllabusSubtopicResponse(
#             llm_response=llm_response
#         )
#     except Exception as e:
#         msg.error(f"Error in get_syllabus_subtopic_with_query: {str(e)}")
#         raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/get_chapter/{ch_id}")
async def get_chapter(ch_id: str):
    try:
        #Note: Condition to test ch_id is part of syllabus tree and its valid
        chapter_query = (
            manager.client.query
            .get("VERBA_Syllabus_Chapters", ["chapter_content"])
            .with_where({
                "path": ["ch_id"],
                "operator": "Equal",
                "valueString": ch_id
            })
            .with_limit(1)
            .do()
        )

        if not chapter_query["data"]["Get"]["VERBA_Syllabus_Chapters"]:
            raise HTTPException(status_code=404, detail="Chapter not found")

        chapter_data = chapter_query["data"]["Get"]["VERBA_Syllabus_Chapters"][0]
        
        return JSONResponse(content=chapter_data)

    except Exception as e:
        msg.fail(f"Error retrieving chapter: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/get_subtopic/{subtopic_id}")
async def get_subtopic(subtopic_id: str):
    try:

        #Note: Condition to test subtopic_id is part of syllabus tree and its valid
        subtopic_query = (
            manager.client.query
            .get("VERBA_Syllabus_Subtopics", ["subtopic_content"])
            .with_where({
                "path": ["subtopic_id"],
                "operator": "Equal",
                "valueString": subtopic_id
            })
            .with_limit(1)
            .do()
        )

        if not subtopic_query["data"]["Get"]["VERBA_Syllabus_Subtopics"]:
            raise HTTPException(status_code=404, detail="Subtopic not found")

        subtopic_data = subtopic_query["data"]["Get"]["VERBA_Syllabus_Subtopics"][0]
        
        return JSONResponse(content=subtopic_data)

    except Exception as e:
        msg.fail(f"Error retrieving subtopic: {e}")
        raise HTTPException(status_code=500, detail=str(e))



## Streaming Subtopic api
@app.post("/api/get_syllabus_subtopic_stream", response_class=StreamingResponse)
async def get_syllabus_subtopic_stream(request: GetSyllabusSubtopicRequest):
    """
    Modified route to stream the LLM response back to the client using SSE.
    """
    try:
        # 1. Parse the incoming request body
        subtopic_id = request.subtopic_id
        user_id = request.user_id

        msg.info(f"Fetching content for Subtopic ID: {subtopic_id} for User ID: {user_id}")

        # 2. Extract chapter_id from subtopic_id
        chapter_id = subtopic_id.split('_')[0]
        msg.info(f"Extracted chapter_id: {chapter_id} from subtopic_id: {subtopic_id}")

        # 3. Fetch chapter name
        chapter_query = (
            manager.client.query
            .get("VERBA_Syllabus_Chapters", ["chapter_name"])
            .with_where({
                "path": ["ch_id"],
                "operator": "Equal",
                "valueString": chapter_id
            })
            .with_limit(1)
            .do()
        )

        if not chapter_query["data"]["Get"]["VERBA_Syllabus_Chapters"]:
            raise HTTPException(status_code=404, detail="Chapter not found")

        chapter_name = chapter_query["data"]["Get"]["VERBA_Syllabus_Chapters"][0]["chapter_name"]

        # 4. Fetch subtopic content
        subtopic_query = (
            manager.client.query
            .get("VERBA_Syllabus_Subtopics", ["subtopic_content"])
            .with_where({
                "path": ["subtopic_id"],
                "operator": "Equal",
                "valueString": subtopic_id
            })
            .with_limit(1)
            .do()
        )

        if not subtopic_query["data"]["Get"]["VERBA_Syllabus_Subtopics"]:
            raise HTTPException(status_code=404, detail="Subtopic not found")

        subtopic_content = subtopic_query["data"]["Get"]["VERBA_Syllabus_Subtopics"][0].get("subtopic_content", "")

        # For demonstration, we won't handle conversation history here.
        subtopic_name = ""

        # 5. Create the prompt (as before)
        prompt = prompts.create_subtopic_mentor_prompt(
            subtopic_content=subtopic_content,
            chapter_name=chapter_name,
            subtopic_name=subtopic_name,
        )

        # 6. Build an async generator that yields each chunk in SSE format
        async def event_stream():
            try:
                # gemini_generator is your streaming method
                # generate_stream returns an async generator of chunks
                async for chunk in gemini_generator.generate_stream([prompt], [""], []):
                    finish_reason = chunk.get("finish_reason")
                    message = chunk.get("message", "")

                    # If the model signals "stop", break out
                    if finish_reason == "stop":
                        break

                    # Stream partial text as JSON with type='text-delta'
                    # SSE format: data: <json>\n\n
                    yield (
                        "data: " + json.dumps({
                            "type": "text-delta",
                            "content": message
                        }) + "\n\n"
                    )

                    # optional small sleep to reduce CPU usage or control chunk rate
                    await asyncio.sleep(0.02)

                # After we're done, tell the client "finish"
                yield (
                    "data: " + json.dumps({
                        "type": "finish",
                        "content": ""
                    }) + "\n\n"
                )

            except Exception as e:
                msg.fail(f"Gemini API call failed: {str(e)}")
                # Return an SSE "error" message
                yield (
                    "data: " + json.dumps({
                        "type": "error",
                        "content": str(e)
                    }) + "\n\n"
                )

        # 7. Return a StreamingResponse with text/event-stream
        return StreamingResponse(event_stream(), media_type="text/event-stream")

    except Exception as e:
        msg.fail(f"Error in get_syllabus_subtopic_stream: {str(e)}")
        # If we fail before streaming starts, raise an HTTPException
        raise HTTPException(status_code=500, detail=str(e))




#####
@app.post("/api/get_syllabus_subtopic_with_query_stream", response_class=StreamingResponse)
async def get_syllabus_subtopic_with_query_stream(request: GetSyllabusSubtopicQueryRequest):
    debug_log(f"Received get_syllabus_subtopic_with_query request: {request}")
    try:
        subtopic_id = request.subtopic_id
        user_id = request.user_id
        query = request.query

        msg.info(f"Fetching content for Subtopic ID: {subtopic_id} for User ID: {user_id} with query: {query}")

        # Extract chapter_id from subtopic_id
        chapter_id = subtopic_id.split('_')[0]
        msg.info(f"Extracted chapter_id: {chapter_id} from subtopic_id: {subtopic_id}")

        # Fetch chapter name from Weaviate
        chapter_query = (
            manager.client.query
            .get("VERBA_Syllabus_Chapters", ["chapter_name"])
            .with_where({
                "path": ["ch_id"],
                "operator": "Equal",
                "valueString": chapter_id
            })
            .with_limit(1)
            .do()
        )

        if not chapter_query["data"]["Get"]["VERBA_Syllabus_Chapters"]:
            raise HTTPException(status_code=404, detail="Chapter not found")

        chapter_name = chapter_query["data"]["Get"]["VERBA_Syllabus_Chapters"][0]["chapter_name"]

        # Fetch subtopic content from Weaviate
        subtopic_data = (
            manager.client.query
            .get("VERBA_Syllabus_Subtopics", ["subtopic_content"])
            .with_where({
                "path": ["subtopic_id"],
                "operator": "Equal",
                "valueString": subtopic_id
            })
            .with_limit(1)
            .do()
        )

        if not subtopic_data["data"]["Get"]["VERBA_Syllabus_Subtopics"]:
            raise HTTPException(status_code=404, detail="Subtopic not found")

        subtopic_content = subtopic_data["data"]["Get"]["VERBA_Syllabus_Subtopics"][0].get("subtopic_content", "")

        # For demonstration, we won't handle any conversation history here
        conversation_history = "No previous conversation history."
        subtopic_name = ""

        # 1) Generate the prompt
        prompt = prompts.create_subtopic_mentor_prompt_followup(
            subtopic_content=subtopic_content,
            chapter_name=chapter_name,
            subtopic_name=subtopic_name,
            user_query=query
        )

        # 2) Define an async generator to yield streamed chunks
        async def event_stream():
            try:
                # gemini_generator.generate_stream(...) returns an async generator
                async for chunk in gemini_generator.generate_stream([prompt], [""], []):
                    finish_reason = chunk.get("finish_reason")
                    message = chunk.get("message", "")

                    # If the model signals "stop", break out
                    if finish_reason == "stop":
                        break

                    # Stream partial text as JSON with type='text-delta'
                    # SSE format: data: <json>\n\n
                    yield (
                        "data: " + json.dumps({
                            "type": "text-delta",
                            "content": message
                        }) + "\n\n"
                    )

                    # optional small sleep to reduce CPU usage or control chunk rate
                    await asyncio.sleep(0.02)

                # After we're done, tell the client "finish"
                yield (
                    "data: " + json.dumps({
                        "type": "finish",
                        "content": ""
                    }) + "\n\n"
                )

            except Exception as e:
                msg.fail(f"Gemini API call failed: {str(e)}")
                # Return an SSE "error" message
                yield (
                    "data: " + json.dumps({
                        "type": "error",
                        "content": str(e)
                    }) + "\n\n"
                )

        # 3) Return a StreamingResponse
        return StreamingResponse(event_stream(), media_type="text/event-stream")

    except Exception as e:
        msg.fail(f"Error in get_syllabus_subtopic_with_query_stream: {str(e)}")
        # If we haven't started streaming yet, we can raise directly.
        raise HTTPException(status_code=500, detail=str(e))



##############visualize subtopic

@app.post("/api/visualize_subtopic")
async def visualize(request: GetSyllabusSubtopicRequest):
    debug_log(f"Received visualize_subtopic request: {request}")
    try:
        subtopic_id = request.subtopic_id
        user_id = request.user_id

        # Fetch subtopic content from Weaviate
        subtopic_query = (
            manager.client.query
            .get("VERBA_Syllabus_Subtopics", ["subtopic_content"])
            .with_where({
                "path": ["subtopic_id"],
                "operator": "Equal",
                "valueString": subtopic_id
            })
            .with_limit(1)
            .do()
        )

        if not subtopic_query["data"]["Get"]["VERBA_Syllabus_Subtopics"]:
            raise HTTPException(status_code=404, detail="Subtopic not found")

        subtopic_content = subtopic_query["data"]["Get"]["VERBA_Syllabus_Subtopics"][0].get("subtopic_content", "")

        # Get visualization prompt from prompts module
        visualize_prompt = prompts.get_prompt("VISUALIZE", topic=subtopic_content)

        # Call deepseek LLM
        mermaid_response = await generate_deepseek_response(visualize_prompt, subtopic_content)
        debug_log("Generated mermaid diagram:", mermaid_response)

        return JSONResponse(content={"mermaid_code": mermaid_response})

    except HTTPException as e:
        raise e
    except Exception as e:
        msg.fail(f"Visualization failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Visualization failed: {str(e)}"}
        )


@app.post("/api/visualize_content")
async def visualize(request: GetVisualizeContentRequest):
    debug_log(f"Received visualize_content request: {request}")
    try:
        subtopic_id = request.subtopic_id
        user_id = request.user_id
        content = request.content

        # Get visualization prompt from prompts module
        visualize_prompt = prompts.get_prompt("VISUALIZE", topic=content)

        # Call deepseek LLM
        mermaid_response = await generate_deepseek_response(visualize_prompt, content)
        debug_log("Generated mermaid diagram:", mermaid_response)

        return JSONResponse(content={"mermaid_code": mermaid_response})

    except HTTPException as e:
        raise e
    except Exception as e:
        msg.fail(f"Visualization failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Visualization failed: {str(e)}"}
        )


@app.post("/api/visualize_content_combo")
async def visualize_content_combo(request: GetVisualizeContentComboRequest):
    debug_log(f"Received visualize_content_combo request: {request}")
    #msg.info(f"visualize_prompt1::: {request}")
    try:
        subtopic_id = request.subtopic_id
        user_id = request.user_id
        content = request.content
        model_id = request.model_id 

        # Get visualization prompts from prompts module
        visualize_prompt1 = prompts.get_prompt("VISUALIZE_MERMAID", topic=content)
        visualize_prompt2 = prompts.get_prompt("VISUALIZE_MARKMAP", topic=content)

        #msg.info(f"visualize_prompt1::: {visualize_prompt1}")
        #msg.info(f"visualize_prompt2::: {visualize_prompt2}")
        
        # Generate both responses based on model_id
        if model_id == 0:
            mermaid_response = await generate_gemini_response(visualize_prompt1, "", "gemini-1.5-flash-002")
            markmap_response = await generate_gemini_response(visualize_prompt2, "", "gemini-1.5-flash-002")
        elif model_id == 1:
            mermaid_response = await generate_gemini_response(visualize_prompt1, "", "gemini-2.0-flash-exp")
            markmap_response = await generate_gemini_response(visualize_prompt2, "", "gemini-2.0-flash-exp")
        elif model_id == 2:
            mermaid_response = await generate_deepseek_response(visualize_prompt1, "", "deepseek-r1")
            markmap_response = await generate_deepseek_response(visualize_prompt2, "", "deepseek-r1")
        elif model_id == 3:
            mermaid_response = await generate_deepseek_response(visualize_prompt1, "", "deepseek-chat")
            markmap_response = await generate_deepseek_response(visualize_prompt2, "", "deepseek-chat")
        else:
            mermaid_response = await generate_gemini_response(visualize_prompt1, "", "gemini-1.5-flash-002")
            markmap_response = await generate_gemini_response(visualize_prompt2, "", "gemini-1.5-flash-002")
        
        #msg.info(f"Generated mermaid diagram::: {mermaid_response}")
        #msg.info(f"Generated markmap diagram::: {markmap_response}")

        # Return both responses in the JSON
        return JSONResponse(content={
            "mermaid_code": mermaid_response,
            "markmap_code": markmap_response
        })

    except HTTPException as e:
        raise e
    except Exception as e:
        msg.fail(f"Visualization failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Visualization failed: {str(e)}"}
        )


@app.post("/api/visualize_subtopic_combo")
async def visualize_subtopic_combo(request: GetVisualizeSubtopicComboRequest):
    debug_log(f"Received visualize_content_combo request: {request}")
    #msg.info(f"visualize_prompt1::: {request}")
    try:
        subtopic_id = request.subtopic_id
        user_id = request.user_id
        model_id = request.model_id 

        # Fetch subtopic content using helper
        subtopic_content = fetch_subtopic_content(manager, subtopic_id)
        
        if not subtopic_content:
            msg.warn(f"Empty content received for subtopic_id: {subtopic_id}")
            return JSONResponse(
                status_code=400,
                content={"error": f"No content found for subtopic {subtopic_id}"}
            )

        # Get visualization prompts from prompts module
        visualize_prompt1 = prompts.get_prompt("VISUALIZE_MERMAID", topic=subtopic_content)
        visualize_prompt2 = prompts.get_prompt("VISUALIZE_MARKMAP", topic=subtopic_content)
        #msg.info(f"visualize_prompt1::: {visualize_prompt1}")
        #msg.info(f"visualize_prompt2::: {visualize_prompt2}")
        
        # Generate both responses based on model_id
        if model_id == 0:
            mermaid_response = await generate_gemini_response(visualize_prompt1, "", "gemini-1.5-flash-002")
            markmap_response = await generate_gemini_response(visualize_prompt2, "", "gemini-1.5-flash-002")
        elif model_id == 1:
            mermaid_response = await generate_gemini_response(visualize_prompt1, "", "gemini-2.0-flash-exp")
            markmap_response = await generate_gemini_response(visualize_prompt2, "", "gemini-2.0-flash-exp")
        elif model_id == 2:
            mermaid_response = await generate_deepseek_response(visualize_prompt1, "", "deepseek-r1")
            markmap_response = await generate_deepseek_response(visualize_prompt2, "", "deepseek-r1")
        elif model_id == 3:
            mermaid_response = await generate_deepseek_response(visualize_prompt1, "", "deepseek-chat")
            markmap_response = await generate_deepseek_response(visualize_prompt2, "", "deepseek-chat")
        else:
            mermaid_response = await generate_gemini_response(visualize_prompt1, "", "gemini-1.5-flash-002")
            markmap_response = await generate_gemini_response(visualize_prompt2, "", "gemini-1.5-flash-002")
        
        #msg.info(f"Generated mermaid diagram::: {mermaid_response}")
        #msg.info(f"Generated markmap diagram::: {markmap_response}")

        # Return both responses in the JSON
        return JSONResponse(content={
            "mermaid_code": mermaid_response,
            "markmap_code": markmap_response
        })

    except HTTPException as e:
        raise e
    except Exception as e:
        msg.fail(f"Visualization failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Visualization failed: {str(e)}"}
        )



@app.post("/api/summarize_content")
async def visualize(request: GetSummarizeContentRequest):
    debug_log(f"Received summarize_content request: {request}")
    try:
        subtopic_id = request.subtopic_id
        user_id = request.user_id
        content = request.content
        model_id = request.model_id
        
        # Get visualization prompt from prompts module
        summarize_prompt = prompts.get_prompt("SUMMARIZE", topic=content)

        # Call deepseek LLM
        # Generate response based on model_id
        if model_id == 0:
            summarize_response = await generate_gemini_response(summarize_prompt, "", "gemini-1.5-flash-002")
        elif model_id == 1:
            summarize_response = await generate_gemini_response(summarize_prompt, "", "gemini-2.0-flash-exp")
        elif model_id == 2:
            summarize_response = await generate_deepseek_response(summarize_prompt, "", "deepseek-r1")
        elif model_id == 3:
            summarize_response = await generate_deepseek_response(summarize_prompt, "", "deepseek-chat")
        else:
            summarize_response = await generate_gemini_response(summarize_prompt, "", "gemini-1.5-flash-002")
        debug_log("Summarize:", summarize_response)

        return JSONResponse(content={"Summarize": summarize_response})

    except HTTPException as e:
        raise e
    except Exception as e:
        msg.fail(f"Summarize failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Summarize failed: {str(e)}"}
        )


# retrieve pyqs relvant for given topic content
@app.post("/api/pyqs_content")
async def post_pyqs_content(request: GetPYQSContentRequest):
    debug_log(f"Received pyqs_content request: {request}")
    try:
        subtopic_id = request.subtopic_id
        user_id = request.user_id
        content = request.content
        
        # Get visualization prompt from prompts module
        pyqs_prompt = prompts.get_prompt("PYQS", topic=content)

        # Call deepseek LLM
        pyqs_response = await generate_deepseek_response(pyqs_prompt, content)
        debug_log("PYQS:", pyqs_response)

        return JSONResponse(content={"PYQS": pyqs_response})

    except HTTPException as e:
        raise e
    except Exception as e:
        msg.fail(f"PYQS failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"PYQS failed: {str(e)}"}
        )

# Retrieve pyqs from subtopic content
@app.post("/api/pyqs_subtopic")
async def post_pyqs_subtopic(request: GetPYQSsubtopicContentRequest):
    debug_log(f"Received pyqs_content request: {request}")
    try:
        subtopic_id = request.subtopic_id
        count = request.count

        # Fetch subtopic content using helper
        subtopic_content = fetch_subtopic_content(manager, subtopic_id)
        
        if not subtopic_content:
            msg.warn(f"Empty content received for subtopic_id: {subtopic_id}")
            return JSONResponse(
                status_code=400,
                content={"error": f"No content found for subtopic {subtopic_id}"}
            )

        # Perform search and processing using helpers
        pyqs_data = perform_pyqs_search(manager, subtopic_content, count + 15)
        
        if not pyqs_data:
            msg.warn(f"No PYQS results for subtopic_id: {subtopic_id}")
            return JSONResponse(
                content={"PYQS": [], "warning": "No relevant questions found"}
            )

        sorted_results = sorted(pyqs_data, key=lambda x: x["hybrid_score"], reverse=True)
        final_results = await filter_top_pyqs_with_llm(sorted_results, subtopic_content)
        
        return JSONResponse(content={
            "PYQS": final_results,
            "total_found": len(pyqs_data),
            "filtered_count": len(final_results)
        })

    except Exception as e:
        msg.fail(f"PYQS search failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"PYQS search failed: {str(e)}"}
        )



# Retrieve pyqs from subtopic content
@app.post("/api/quiz_subtopic")
async def quiz_subtopic(request: GetQuizSubtopicRequest):
    debug_log(f"Received quiz_subtopic request: {request}")
    try:
        subtopic_id = request.subtopic_id
        count = request.count  # Total number of questions requested
        model_id = request.model_id 

        # Fetch subtopic content using helper
        subtopic_content = fetch_subtopic_content(manager, subtopic_id)
        
        if not subtopic_content:
            msg.warn(f"Empty content received for subtopic_id: {subtopic_id}")
            return JSONResponse(
                status_code=400,
                content={"error": f"No content found for subtopic {subtopic_id}"}
            )

        # Calculate number of each type of question
        num_statement_questions = count // 3  # 1/3 of total questions should be statement-based
        num_regular_questions = count - num_statement_questions

        # Get quiz prompt with specified question counts
        quiz_prompt = prompts.get_prompt(
            "QUIZ_SUBTOPIC", 
            topic=subtopic_content,
            num_questions=count,
            num_statement_questions=num_statement_questions
        )

        # Generate response based on model_id
        if model_id == 0:
            quiz_response = await generate_gemini_response(quiz_prompt, "", "gemini-1.5-flash-002")
        elif model_id == 1:
            quiz_response = await generate_gemini_response(quiz_prompt, "", "gemini-2.0-flash-exp")
        elif model_id == 2:
            quiz_response = await generate_deepseek_response(quiz_prompt, "", "deepseek-r1")
        elif model_id == 3:
            quiz_response = await generate_deepseek_response(quiz_prompt, "", "deepseek-chat")
        else:
            quiz_response = await generate_gemini_response(quiz_prompt, "", "gemini-1.5-flash-002")
        
        debug_log("Quiz response generated")

        return JSONResponse(content={"Quiz": quiz_response})

    except HTTPException as e:
        raise e
    except Exception as e:
        msg.fail(f"Quiz failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Quiz failed: {str(e)}"}
        )



# retrieve pyqs relvant for given topic content
@app.post("/api/suggest_content")
async def suggest_content(request: GetSuggestContentRequest):
    debug_log(f"Received suggest_content request: {request}")
    #msg.info(f"Generated suggest_content .content diagram::: {request.content}")
    try:
        subtopic_id = request.subtopic_id
        user_id = request.user_id
        content = request.content
        count = request.count  # Total number of questions requested
        model_id = request.model_id
        
        # Get visualization prompt from prompts module
        suggest_prompt = prompts.get_prompt("SUGGEST_CONTENT", topic=content,num_questions=count)

        # Generate response based on model_id
        if model_id == 0:
            suggest_response = await generate_gemini_response(suggest_prompt, "", "gemini-1.5-flash-002")
        elif model_id == 1:
            suggest_response = await generate_gemini_response(suggest_prompt, "", "gemini-2.0-flash-exp")
        elif model_id == 2:
            suggest_response = await generate_deepseek_response(suggest_prompt, "", "deepseek-r1")
        elif model_id == 3:
            suggest_response = await generate_deepseek_response(suggest_prompt, "", "deepseek-chat")
        else:
            suggest_response = await generate_gemini_response(suggest_prompt, "", "gemini-1.5-flash-002")

        return JSONResponse(content={"suggest": suggest_response})

    except HTTPException as e:
        raise e
    except Exception as e:
        msg.fail(f"suggest failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"suggest failed: {str(e)}"}
        )



###################################################### PDF UPLOAD

# Add these constants near the top of the file
MAX_FILE_SIZE = 15 * 1024 * 1024  # 15MB limit
ALLOWED_MIME_TYPES = {'application/pdf'}
UPLOAD_DIR = Path("temp_uploads")

# Create upload directory if it doesn't exist
UPLOAD_DIR.mkdir(exist_ok=True)

async def validate_pdf_file(file: UploadFile) -> None:
    """Validate PDF file before processing."""
    if not file.content_type in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Only PDF files are allowed. Got: {file.content_type}"
        )
    
    # Check file size (first chunk)
    chunk = await file.read(MAX_FILE_SIZE + 1)
    await file.seek(0)  # Reset file pointer
    
    if len(chunk) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE/1024/1024}MB"
        )
    
    # Verify PDF header
    header = (await file.read(4)).decode(errors='ignore')
    await file.seek(0)
    if header != "%PDF":
        raise HTTPException(
            status_code=400, 
            detail="Invalid PDF file format"
        )

# async def process_pdf_content(file_path: Path) -> str:
#     """Extract and process PDF content."""
#     try:
#         with open(file_path, 'rb') as file:
#             reader = PyPDF2.PdfReader(file)
#             text = ""
#             for page in reader.pages:
#                 text += page.extract_text() + "\n"
#         return text.strip()
#     except Exception as e:
#         msg.fail(f"Error processing PDF: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

# async def get_gemini_analysis(text: str) -> str:
#     """Get Gemini API analysis of the text."""
#     try:
#         prompt = prompts.get_prompt("ANALYZE_PDF", content=text)
#         response = await generate_gemini_response(prompt, text)
#         return response
#     except Exception as e:
#         msg.fail(f"Error in Gemini analysis: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Error in Gemini analysis: {str(e)}")

@app.post("/api/upload_pdf")
async def upload_pdf(file: UploadFile = File(...)):
    try:
        # Validate the file
        await validate_pdf_file(file)
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_hash = hashlib.md5(f"{file.filename}{timestamp}".encode()).hexdigest()[:10]
        safe_filename = f"upload_{timestamp}_{file_hash}.pdf"
        file_path = UPLOAD_DIR / safe_filename
        
        # Save file
        try:
            with tempfile.NamedTemporaryFile(delete=False, dir=UPLOAD_DIR) as temp_file:
                shutil.copyfileobj(file.file, temp_file)
                file_path = Path(temp_file.name)
            # File automatically cleaned up by context manager
        finally:
            await file.close()
        
        # Process PDF
        try:
            msg.info(f"Processing PDF: {safe_filename}")
            
            # Read PDF content as bytes
            with file_path.open("rb") as f:
                pdf_bytes = f.read()
            
            # Create base64 encoded string
            doc_data = base64.standard_b64encode(pdf_bytes).decode("utf-8")
            
            # Get analysis from Gemini
            prompt = "Here is the UPSC exam mains answer sheet, please give me Question and its answer in json format :"
            #analysis = await generate_pdf_nostream_response(prompt, doc_data , "gemini-1.5-flash-002")
            analysis = await GeminiGenerator.generate_pdf_nostream(prompt, doc_data , "gemini-1.5-flash-002")
            msg.info(f"Gemini analysis completed successfully. Response: {analysis}")

            return JSONResponse(
                content={
                    "status": "success",
                    "filename": file.filename,
                    "analysis": analysis,
                    "error": None
                }
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
            
        finally:
            # Cleanup: Remove temporary file
            try:
                file_path.unlink()
            except Exception as e:
                msg.warn(f"Error removing temporary file {file_path}: {e}")
                
    except HTTPException as he:
        raise he
    except Exception as e:
        msg.fail(f"Error processing upload: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Add cleanup task to remove old temporary files
@app.on_event("startup")
async def startup_event():
    """Clean up any old temporary files on startup."""
    try:
        for file in UPLOAD_DIR.glob("upload_*.pdf"):
            try:
                file.unlink()
            except Exception as e:
                msg.warn(f"Error removing old temporary file {file}: {e}")
    except Exception as e:
        msg.warn(f"Error in startup cleanup: {e}")

