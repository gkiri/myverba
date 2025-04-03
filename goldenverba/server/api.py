from fastapi import FastAPI, WebSocket, UploadFile, status,HTTPException, File, Depends
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
from goldenverba.components.generation.GeminiGenerator_Multimodal import GeminiGenerator_Multimodal
from goldenverba.components.generation.GeminiGenerator_pdf_processor import GeminiGenerator_pdf_processor

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
from goldenverba.components.types import Question,MockQuestion # Add  Question model to types
from pydantic import ValidationError
import goldenverba.server.prompts as prompts
from goldenverba.server.supabase.supabase_client import supabase
import asyncio
import re
from goldenverba.server.api_helpers import (
    fetch_subtopic_content,
    perform_pyqs_search,
    sort_pyqs_by_score,
    filter_top_pyqs_with_llm,
    get_random_mock_questions
)
from fastapi.concurrency import run_in_threadpool
from starlette.requests import Request
from typing import List,AsyncGenerator, Dict, Optional
import aiofiles
from goldenverba.server.api_helpers import split_pdf_into_subpdfs

load_dotenv()

gpt3_generator = GPT3Generator()
groq_generator = GroqGenerator()
gemini_generator = GeminiGenerator()
deepseek_generator = DeepseekGenerator()
gemini_multimodal_generator = GeminiGenerator_Multimodal()
gemini_pdf_processor = GeminiGenerator_pdf_processor()
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
        async for chunk in gemini_generator.generate_pdf_nostream([prompt], [""], pdf_bytes, "gemini-1.5-flash-002"):
            if chunk.get["finish_reason"] == "error":
                raise HTTPException(status_code=500, detail=chunk.get("message", "Unknown error"))
            full_response += chunk.get("message", "")
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
    "http://3.86.59.21:8000",
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

# @app.get("/api/mock_exam")
# async def get_mock_exam_data(request: GetMOCKSRequest):
#     try:
#         questions = await get_random_mock_questions(manager, request.count)
#         formatted_questions = [Question(**question_data).model_dump() 
#                              for question_data in questions]
#         return JSONResponse(content={"questions": formatted_questions})
#     except HTTPException as e:
#         raise e
#     except Exception as e:
#         msg.fail(f"Error in mock exam endpoint: {str(e)}")
#         return JSONResponse(
#             status_code=500, 
#             content={"error": str(e)}
#         )
    
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

class GetMOCKSRequest(BaseModel):
    user_id: str
    count: int


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

from contextlib import asynccontextmanager

# Constants
MAX_FILE_SIZE = 15 * 1024 * 1024  # 15MB
ALLOWED_MIME_TYPES = {'application/pdf'}
UPLOAD_DIR = Path("temp_uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Custom exceptions
class PDFValidationError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=400, detail=detail)

class PDFProcessingError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=500, detail=detail)

# File handling context manager
@asynccontextmanager
async def handle_upload_file(file: UploadFile) -> AsyncGenerator[Path, None]:
    """Safely handle file upload with automatic cleanup."""
    temp_file_path = None
    try:
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_hash = hashlib.md5(f"{file.filename}{timestamp}".encode()).hexdigest()[:10]
        safe_filename = f"upload_{timestamp}_{file_hash}.pdf"
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, dir=UPLOAD_DIR, suffix='.pdf')
        temp_file_path = Path(temp_file.name)
        
        # Stream file content
        async with aiofiles.open(temp_file_path, 'wb') as out_file:
            while content := await file.read(1024 * 1024):  # Read in 1MB chunks
                if temp_file_path.stat().st_size > MAX_FILE_SIZE:
                    raise PDFValidationError("File too large")
                await out_file.write(content)
        
        yield temp_file_path
        
    finally:
        if temp_file_path and temp_file_path.exists():
            temp_file_path.unlink(missing_ok=True)
            msg.info(f"Cleaned up temporary file: {temp_file_path}")

# Validation functions
async def validate_pdf_file(file: UploadFile) -> None:
    """Validate PDF file metadata."""
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise PDFValidationError(f"Invalid file type: {file.content_type}")
    
    # Check PDF header
    header = await file.read(4)
    await file.seek(0)
    if header.decode(errors='ignore') != "%PDF":
        raise PDFValidationError("Invalid PDF format")

# Rate limiting dependency
async def check_rate_limit(request: Request):
    """Implement rate limiting logic here."""
    # Add your rate limiting logic
    pass


def parse_multiple_qna(raw_text: str) -> list:
    """
    Parse a delimiter-based output from an LLM that contains multiple
    question–answer pairs with numbering.

    The expected format is:
        ###QUESTION 1### <question_text> ###ANSWER### <answer_text>
        ###QUESTION 2### <question_text> ###ANSWER### <answer_text>
        ###QUESTION 3### <question_text> ###ANSWER### <answer_text>

    This function extracts the question number, question text, and answer text,
    and returns a list of dictionaries, one for each QnA pair.

    Args:
        raw_text (str): The raw response text from the LLM.

    Returns:
        list: A list of dictionaries, each with keys 'number', 'question', and 'answer'.

    Raises:
        ValueError: If the expected delimiters or QnA pairs cannot be found.
    """
    import re
    from wasabi import msg

    msg.info("parse_multiple_qna: Starting to parse multiple QnA pairs.")

    # The regular expression pattern explanation:
    # - "###QUESTION\s*(\d+)###" captures the question number (one or more digits).
    # - "\s*(.*?)\s*###ANSWER###\s*" captures the question text (non-greedy) up to the answer delimiter.
    # - "(.*?)(?=###QUESTION\s*\d+###|$)" captures the answer text until the next question delimiter or the end of the string.
    pattern = r"###QUESTION\s*(\d+)###\s*(.*?)\s*###ANSWER###\s*(.*?)(?=###QUESTION\s*\d+###|$)"
    matches = re.findall(pattern, raw_text, re.DOTALL)
    
    if not matches:
        msg.info("parse_multiple_qna: No valid QnA pairs were found with expected delimiters.")
        raise ValueError("Invalid format: Expected at least one numbered QnA pair.")

    result = []
    for num, question, answer in matches:
        result.append({
            "number": int(num),
            "question": question.strip(),
            "answer": answer.strip()
        })
    
    msg.info(f"parse_multiple_qna: Found {len(result)} QnA pairs.")
    return result

def parse_multiple_evals(raw_text: str) -> list:
    """
    Parse a delimiter-based output from an LLM that contains multiple
    question–evaluation pairs with numbering.

    The expected format is:
        ###QUESTION <number>### <Question text> ###EVALUATION### <Evaluation text>
        ###QUESTION <number>### <Question text> ###EVALUATION### <Evaluation text>
        ...

    This function extracts the question number, question text, and evaluation text,
    and returns a list of dictionaries, one for each QnA pair.

    Args:
        raw_text (str): The raw response text from the LLM.

    Returns:
        list: A list of dictionaries, each with keys 'number', 'question', and 'evaluation'.

    Raises:
        ValueError: If the expected delimiters or pairs cannot be found.
    """
    import re
    from wasabi import msg

    msg.info("parse_multiple_evals: Starting to parse multiple question-evaluation pairs.")

    # Regular expression pattern:
    # - "###QUESTION\s*(\d+)###": captures the question number.
    # - "\s*(.*?)\s*###EVALUATION###\s*": captures the question text (non-greedy) until the evaluation delimiter.
    # - "(.*?)(?=###QUESTION\s*\d+###|$)": captures the evaluation text until the next question or end-of-string.
    pattern = r"###QUESTION\s*(\d+)###\s*(.*?)\s*###EVALUATION###\s*(.*?)(?=###QUESTION\s*\d+###|$)"
    matches = re.findall(pattern, raw_text, re.DOTALL)

    if not matches:
        msg.info("parse_multiple_evals: No valid question-evaluation pairs were found with expected delimiters.")
        raise ValueError("Invalid format: Expected at least one numbered question-evaluation pair.")

    result = []
    for num, question, evaluation in matches:
        result.append({
            "number": int(num),
            "question": question.strip(),
            "evaluation": evaluation.strip()
        })

    msg.info(f"parse_multiple_evals: Found {len(result)} question-evaluation pairs.")
    return result

@app.post("/api/upload_pdf")
async def upload_pdf(
    request: Request,
    file: UploadFile = File(...),
    rate_limit: None = Depends(check_rate_limit)
) -> JSONResponse:
    """
    Handle PDF upload and processing.
    
    Args:
        request: FastAPI request object
        file: Uploaded PDF file
        rate_limit: Rate limiting dependency
        
    Returns:
        JSONResponse with processing results
        
    Raises:
        PDFValidationError: For invalid files
        PDFProcessingError: For processing errors
    """
    # Generate request ID for tracking
    request_id = str(uuid.uuid4())
    msg.info(f"Processing upload request {request_id} for file: {file.filename}")
    
    try:
        # Validate file
        await validate_pdf_file(file)
        
        # Handle file upload and processing
        async with handle_upload_file(file) as temp_path:
            # approach-1 Read PDF content
            #pdf_bytes = await run_in_threadpool(lambda: temp_path.read_bytes())

            # approach-2
            # Instead of using run_in_threadpool with temp_path.read_bytes(),
            # we now read the PDF file asynchronously for better efficiency.
            async with aiofiles.open(temp_path, 'rb') as f:
                pdf_bytes = await f.read()

            # Process with Gemini
            # prompt = """Here is the UPSC exam mains answer sheet, please give me Question and its answer in json format:
            # Pay high attention and Please extract complete answer without fail.

            # Rules to follow:
            # 1.Extract the Question and answer as it is present in document with very high quality and precision
            # 2.Maintain the structure of answer as it is present in the document.
            # 3.Questions with unattempted or no answer ,exract question and add answer as 'Not Answered'
            # 4.Please think carefully before every word generation
            # 5.Please dont hallucinate
            

            prompt = """Below is a UPSC exam mains answer sheet. Your task is to extract every Question and its Answer in the document with high quality and precision. 

            Rules:
            1. For questions with no answer, output "Not Answered" as the answer.
            2. Do not add any extra explanations, commentary, or markdown formatting.
            3. If there are any diagrams/maps/tables or any diagram please indicate it type of diagram in Bold letters(eg: Figure : , Table: , Map:, etc) and explain the information it captured and conveys in text and dont miss any information .
            4. If there are tables , use stick diagram and represent table and its content
            5. Return the results using the following exact text format for each question–answer pair:
            "###QUESTION <number>### <Question text> ###ANSWER### <Answer text>"
            Example for three pairs:
            ###QUESTION 1### What is the capital of France? ###ANSWER### Paris is the capital of France.
            ###QUESTION 2### What is the largest planet? ###ANSWER### Not Answered.
            ###QUESTION 3### Explain the process of photosynthesis. ###ANSWER### [Answer text].
            6. Think carefully before every word generation and do not hallucinate.

            Attention: Output must contain exactly the above delimiters in the specified structure with no additional text.
            """
            full_response = await gemini_multimodal_generator.generate_pdf(
                prompt=prompt,
                context='',
                pdf_data=pdf_bytes,
                model_name="gemini-2.0-flash-exp"
            )
            
            msg.good(f"Successfully processed upload {request_id}")

            # 4) Attempt to parse and fix the JSON from the model
            #cleaned_json = fix_json_on_backend(full_response)
            
            qna_pairs = parse_multiple_qna(full_response)
            msg.good(f"Successfully processed qna_pairs {qna_pairs}")
            return JSONResponse(content={
                "status": "success",
                "request_id": request_id,
                "filename": file.filename,
                "qna_pairs": qna_pairs,
                "error": None
            })
            
    except PDFValidationError as ve:
        msg.fail(f"Validation error for request {request_id}: {str(ve)}")
        raise
        
    except Exception as e:
        msg.fail(f"Processing error for request {request_id}: {str(e)}")
        raise PDFProcessingError(f"Failed to process PDF: {str(e)}")
    
    finally:
        await file.close()

@app.post("/api/evaluate_pdf_answers")
async def evaluate_pdf_answers(
    request: Request,
    file: UploadFile = File(...),
    rate_limit: None = Depends(check_rate_limit)
) -> JSONResponse:
    """
    Handle PDF upload and processing, evaluating the answer sheet for 10 questions concurrently.
    For each question number (1 to 10), this endpoint calls the Gemini multimodal generator API concurrently
    and collects all responses into a final JSON response.

    Args:
        request: FastAPI request object
        file: Uploaded PDF file
        rate_limit: Rate limiting dependency

    Returns:
        JSONResponse with processing results:
            - request_id: Unique ID of the request.
            - filename: Original file name.
            - evaluations: List containing evaluation responses for each question numbered 1 to 10.
            - error: Any error message captured (if applicable).

    Raises:
        PDFValidationError: For invalid files.
        PDFProcessingError: For processing errors.
    """
    request_id = str(uuid.uuid4())
    msg.info(f"Processing evaluate_pdf_answers request {request_id} for file: {file.filename}")
    
    try:
        # Validate file metadata and format
        await validate_pdf_file(file)
        
        async with handle_upload_file(file) as temp_path:
            # Read the PDF file asynchronously for efficiency
            async with aiofiles.open(temp_path, 'rb') as f:
                pdf_bytes = await f.read()
            
            mains_evaluation_prompt = prompts.get_prompt("MAINS_EVALUATION")
            # Create a coroutine to call the generate_pdf endpoint with the generated prompt
            full_response = await gemini_multimodal_generator.generate_pdf(
                prompt=mains_evaluation_prompt,
                context='',
                pdf_data=pdf_bytes,
                model_name="gemini-2.0-flash-exp"
            )
            
            # Process the responses: if an exception occurred, record its message.
            qna_evals = parse_multiple_evals(full_response)
            msg.good(f"Successfully processed qna_evals {qna_evals}")
            return JSONResponse(content={
                "status": "success",
                "request_id": request_id,
                "filename": file.filename,
                "qna_evals": qna_evals,
                "error": None
            })
            
    
    except PDFValidationError as ve:
        msg.fail(f"Validation error for request {request_id}: {str(ve)}")
        raise
        
    except Exception as e:
        msg.fail(f"Processing error for request {request_id}: {str(e)}")
        raise PDFProcessingError(f"Failed to process PDF: {str(e)}")
    
    finally:
        await file.close()


@app.post("/api/evaluate_pdf_answers_multi")
async def evaluate_pdf_answers(
    request: Request,
    file: UploadFile = File(...),
    rate_limit: None = Depends(check_rate_limit)
) -> JSONResponse:
    """
    Handle PDF upload and processing, evaluating the answer sheet for 10 questions concurrently.
    For each question number (1 to 10), this endpoint calls the Gemini multimodal generator API concurrently
    and collects all responses into a final JSON response.

    Args:
        request: FastAPI request object
        file: Uploaded PDF file
        rate_limit: Rate limiting dependency

    Returns:
        JSONResponse with processing results:
            - request_id: Unique ID of the request.
            - filename: Original file name.
            - evaluations: List containing evaluation responses for each question numbered 1 to 10.
            - error: Any error message captured (if applicable).

    Raises:
        PDFValidationError: For invalid files.
        PDFProcessingError: For processing errors.
    """
    request_id = str(uuid.uuid4())
    msg.info(f"Processing evaluate_pdf_answers request {request_id} for file: {file.filename}")
    
    try:
        # Validate file metadata and format
        await validate_pdf_file(file)
        
        async with handle_upload_file(file) as temp_path:
            # Read the PDF file asynchronously for efficiency
            async with aiofiles.open(temp_path, 'rb') as f:
                pdf_bytes = await f.read()
            
            # Prepare tasks for evaluating questions 1 to 10 concurrently.
            tasks = []
            for question_num in range(1, 3):
                # Get a prompt for this question evaluation 
                mains_evaluation_prompt = prompts.get_prompt("MAINS_EVALUATION", question_num=question_num)
                # Create a coroutine to call the generate_pdf endpoint with the generated prompt
                tasks.append(
                    gemini_multimodal_generator.generate_pdf(
                        prompt=mains_evaluation_prompt,
                        context='',
                        pdf_data=pdf_bytes,
                        model_name="gemini-1.5-flash-002"
                    )
                )
            
            # Run all tasks concurrently. return_exceptions=True to handle individual call failures gracefully.
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process the responses: if an exception occurred, record its message.
            evaluations = []
            for idx, result in enumerate(responses, start=1):
                if isinstance(result, Exception):
                    msg.fail(f"Evaluation failed for question {idx}: {str(result)}")
                    evaluations.append({
                        "question_num": idx,
                        "evaluation": None,
                        "error": str(result)
                    })
                else:
                    evaluations.append({
                        "question_num": idx,
                        "evaluation": result,
                        "error": None
                    })
            
            msg.good(f"Successfully processed evaluate_pdf_answers request {evaluations}")
            return JSONResponse(content={
                "status": "success",
                "request_id": request_id,
                "filename": file.filename,
                "evaluations": evaluations,
                "error": None
            })
    
    except PDFValidationError as ve:
        msg.fail(f"Validation error for request {request_id}: {str(ve)}")
        raise
        
    except Exception as e:
        msg.fail(f"Processing error for request {request_id}: {str(e)}")
        raise PDFProcessingError(f"Failed to process PDF: {str(e)}")
    
    finally:
        await file.close()


# Cleanup task
@app.on_event("startup")
async def startup_event():
    """Clean up any old temporary files on startup."""
    try:
        for file in UPLOAD_DIR.glob("upload_*.pdf"):
            try:
                file.unlink()
                msg.info(f"Cleaned up old file: {file}")
            except Exception as e:
                msg.warn(f"Error removing old file {file}: {e}")
    except Exception as e:
        msg.warn(f"Error in startup cleanup: {e}")
        msg.warn(f"Error in startup cleanup: {e}")


############################################ Mock Exam

# @app.get("/api/get_mock_exam2")
# async def get_mock_exam_data(request: GetMOCKSRequest):
#     # Retrieve random 30 questions from Weaviate
#     try:

#         count = request.count  # Total number of questions requested

#         results = (
#             manager.client.query.get(
#                 "MOCKS",
#                 ["question", "options", "answer_key", "year", "topic", "description", "question_number","global_questionID"],
#             )
#             .with_limit(count)
#             .do()
#         )
#         print("Results Format:", results)
#         if "data" in results and "Get" in results["data"] and "MOCKS" in results["data"]["Get"]:
#             questions = [Question(**question_data).dict() for question_data in results["data"]["Get"]["MOCKS"]]
#             mock_exam_data = {"questions": questions}
#             return JSONResponse(content=mock_exam_data)
#         else:
#             return JSONResponse(status_code=500, content={"error": "Unexpected data structure in results"})
#     except Exception as e:
#         msg.fail(f"Error retrieving mock exam questions: {e}")
#         return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/api/get_mock_exam")
async def get_mock_exam_data(request: GetMOCKSRequest):
    try:
        questions = await get_random_mock_questions(manager, request.count)
        formatted_questions = [MockQuestion(**question_data).model_dump() 
                             for question_data in questions]
        return JSONResponse(content={"questions": formatted_questions})
    except HTTPException as e:
        raise e
    except Exception as e:
        msg.fail(f"Error in mock exam endpoint: {str(e)}")
        return JSONResponse(
            status_code=500, 
            content={"error": str(e)}
        )


###############################################################################
# 5. Endpoint: Upload a PDF + get Markdown
###############################################################################
@app.post("/process-pdf")
async def process_pdf_endpoint(pdf_file: UploadFile = File(...)) -> JSONResponse:
    """
    - Accept a PDF file
    - Create a unique temp directory for this request
    - Split the PDF into 8-page sub-PDFs
    - Call Gemini for each chunk asynchronously
    - Cleanup (remove all files) before returning
    """
    # 1) Create a unique directory for this request
    request_id = uuid.uuid4().hex
    #temp_root = f"temp_{request_id}"
    temp_root = os.path.join("/tmp", f"pdf_process_{request_id}")
    os.makedirs(temp_root, exist_ok=True)
    
    # Path to store the user's uploaded PDF
    input_pdf_path = os.path.join(temp_root, "uploaded.pdf")
    
    # 2) Save the uploaded PDF to that folder
    file_bytes = await pdf_file.read()
    with open(input_pdf_path, "wb") as f:
        f.write(file_bytes)
    
    # Directory for sub-PDF chunks
    chunk_dir = os.path.join(temp_root, "chunks")
    
    # 3) Split into multiple 8-page PDFs
    chunk_paths = split_pdf_into_subpdfs(
        pdf_path=input_pdf_path, 
        chunk_size=8,
        output_dir=chunk_dir
    )
    
    try:
        # 4) Process chunks with Gemini asynchronously
        gemini_results = await gemini_pdf_processor.process_pdf_chunks(chunk_paths)
        
        # 5) Concatenate Gemini text outputs into final Markdown
        final_markdown = "\n\n".join([res.text for res in gemini_results])
        #final_markdown = "\n\n".join(gemini_results)
        
    finally:
        # 6) Clean up: remove the unique folder and all its contents
        if os.path.exists(temp_root):
            shutil.rmtree(temp_root, ignore_errors=True)
    
    # 7) Return final Markdown
    return JSONResponse(content={"markdown": final_markdown})


###############################################################################
# 5. Endpoint: Upload a PDF + get Markdown + chunkify + vectorize + upload to supabase 
###############################################################################
from langchain_text_splitters import RecursiveCharacterTextSplitter
import tiktoken

def load_and_split_markdown(markdown_content, chunk_size=8000, chunk_overlap=2000):
    """
    Loads a Markdown file, splits it into chunks, and returns the chunks.

    Args:
        markdown_file_path (str): Path to the Markdown file.
        chunk_size (int, optional): Desired chunk size in tokens. Defaults to 8000.
        chunk_overlap (int, optional): Desired chunk overlap in tokens. Defaults to 2000.

    Returns:
        list: List of text chunks.
    """


    # Initialize the splitter
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        model_name="gpt-4",
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""]
    )

    # Split the text
    chunks = text_splitter.split_text(markdown_content)

    return chunks



import voyageai
voyage_client = voyageai.Client(api_key=os.getenv("VOYAGEAI_API_KEY"))


# Note: input_type = query for search related embeddings , input_type = document for documents embedding

def generate_embedding(text, model="voyage-3", input_type="query", **kwargs):
    result = voyage_client.embed([text], model=model, input_type=input_type, **kwargs)
    return result.embeddings[0]

# # Helper function to generate embeddings
# async def generate_embeddings(chunks: List[str]) -> List[List[float]]:
#     """Generate embeddings for text chunks using Voyage AI."""
#     response = voyage_client.embed(chunks, model="voyage-3", input_type="document")
#     return [embedding.embedding for embedding in response.embeddings]


async def vectorize_chunks(chunks: List[str],
                           batch_size: int = 10,
                           concurrency: int = 5) -> List[List[float]]:
    """
    Vectorize text chunks using Voyage AI in batches, running up to `concurrency`
    requests in parallel. Each request handles `batch_size` chunks.
    """
    
    # If voyage_client.embed is synchronous, wrap in to_thread
    async def embed_batch(batch: List[str]) -> List[List[float]]:
        # Synchronous call in a thread (non-blocking for the event loop)
        response = await asyncio.to_thread(
            voyage_client.embed,
            batch,
            model="voyage-3"
        )
        return response.embeddings

    # Semaphore to limit concurrency
    semaphore = asyncio.Semaphore(concurrency)
    tasks = []

    # Create a task for each batch of chunks
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]

        async def run_embedding(b=batch):
            async with semaphore:
                return await embed_batch(b)

        tasks.append(asyncio.create_task(run_embedding()))

    # Run all tasks concurrently (up to `concurrency`)
    results = await asyncio.gather(*tasks)

    # Flatten the list of embeddings
    embeddings = [emb for batch_embeddings in results for emb in batch_embeddings]
    return embeddings


async def upload_file_chunks(user_id: str, file_name: str, file_size:int , chunks: List[str], embeddings: List[List[float]]) -> int:
    """
    1. Creates a new record in `files` to track the uploaded file.
    2. For each chunk of text:
       - Generate embedding
       - Insert a record into `text_chunks` with `file_id` & `user_id`.
    3. Returns the newly created file_id to the client.
    """
    msg.info("Gkiri:: upload_file_chunks: ENTER.....!")

    try:
        # -- 1) Insert metadata into `files` table --
        file_insert_resp = supabase.table("files").insert({
            "user_id": user_id,
            "file_name": file_name,
            "file_size": file_size,
            "file_type": 'pdf'
        }).execute()

        if not file_insert_resp.data:
            raise HTTPException(status_code=400, detail="Failed to create file record.")

        # Table: files , entry: id --> metadata of pdf file used for search 
        # Note: Frontend uploads same pdf in to storage 
        # (Table: user_files : external_file_id which is above files table : id returned by process_pdf_endtoend)
        file_id = file_insert_resp.data[0]["id"]  # The newly created file's UUID
        msg.info(f"Gkiri2:: upload_file_chunks: files inseretd file_id ={file_id}")

        # -- 2) Prepare the data for bulk insertion into `text_chunks` --
        # For large files, generating embeddings chunk-by-chunk can be expensive.
        # You might do it asynchronously or in batches.
        chunks_to_insert = []
        for i in range(len(chunks)):
            chunk_record = {
                "user_id": user_id,
                "file_id": file_id,
                "text": chunks[i],
                "embedding": embeddings[i]
            }
            chunks_to_insert.append(chunk_record)

        # -- 3) Bulk insert text chunks --
        #Note: Revisist and check error status for db insert
        if chunks_to_insert:
            supabase.table("text_chunks").insert(chunks_to_insert).execute()


        msg.info(f"Gkiri3:: upload_file_chunks: text_chunks inserted =.....")
        # return {
        #     "status": "success",
        #     "file_id": file_id,
        #     "message": f"File '{request.file_name}' uploaded successfully with {len(request.text_chunks)} chunks."
        # }

        return file_id

    except Exception as e:
        msg.fail(f"Error in upload_file_chunks: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/process-pdf-endtoend")
async def process_pdf_endtoend(user_id: str, pdf_file: UploadFile = File(...)) -> JSONResponse:
    """
    - Accept a PDF file
    - Create a unique temp directory for this request
    - Split the PDF into 8-page sub-PDFs
    - Call Gemini for each chunk asynchronously
    - Cleanup (remove all files) before returning
    """

    # 1) Create a unique directory for this request
    request_id = uuid.uuid4().hex
    #temp_root = f"temp_{request_id}"
    temp_root = os.path.join("/tmp", f"pdf_process_{request_id}")
    os.makedirs(temp_root, exist_ok=True)
    
    # Path to store the user's uploaded PDF
    input_pdf_path = os.path.join(temp_root, "uploaded.pdf")
    
    # 2) Save the uploaded PDF to that folder
    file_bytes = await pdf_file.read()
    with open(input_pdf_path, "wb") as f:
        f.write(file_bytes)
    
    # Directory for sub-PDF chunks
    chunk_dir = os.path.join(temp_root, "chunks")
    
    # 3) Split into multiple 8-page PDFs
    chunk_paths = split_pdf_into_subpdfs(
        pdf_path=input_pdf_path, 
        chunk_size=8,
        output_dir=chunk_dir
    )
    
    try:
        # 4) Process chunks with Gemini asynchronously
        gemini_results = await gemini_pdf_processor.process_pdf_chunks(chunk_paths)
        
        # 5) Concatenate Gemini text outputs into final Markdown
        final_markdown = "\n\n".join([res.text for res in gemini_results])
        #final_markdown = "\n\n".join(gemini_results)

        #chunkify markdown content in to 8k chunks
        chunks = load_and_split_markdown(final_markdown)

        all_embeddings = await vectorize_chunks(chunks, batch_size=20, concurrency=5)
        if len(all_embeddings) != len(chunks):
            raise HTTPException(status_code=500, detail="Embedding generation failed")        

        msg.info(f"Gkiri:: vectorize_chunks: ENTER.....! {len(all_embeddings)}") 

        file_id = await upload_file_chunks(user_id, pdf_file.filename, len(file_bytes), chunks, all_embeddings)
        # Return final Markdown
        return JSONResponse(content={
            "file_id": file_id,
            "status": "success"
        })
            
    except Exception as e:
        # Log the error
        if "Failed to upload file chunks" in str(e):
            msg.fail(f"Failed to upload file chunks: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={
                    "status": "fail",
                    "detail": "Failed to store or upload processed document"
                }
            )
        else:
            msg.fail(f"Error processing PDF: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={
                    "status": "fail",
                    "detail": "Failed to process PDF document"
                }
            )
    finally:
        # 6) Clean up: remove the unique folder and all its contents
        if os.path.exists(temp_root):
            shutil.rmtree(temp_root, ignore_errors=True)


###############################################################################
# Lexical Search 
###############################################################################

class LexicalSearchRequest(BaseModel):
    query_text: str
    match_count: int = 10
    file_ids: Optional[List[str]] = None  # If empty/None => search all user chunks

class SemanticSearchRequest(BaseModel):
    query_text: str
    match_threshold: float = 0.78
    match_count: int = 10
    file_ids: Optional[List[str]] = None

class HybridSearchRequest(BaseModel):
    query_text: str
    match_count: int = 10
    file_ids: Optional[List[str]] = None

# @app.post("/search/lexical")
# async def lexical_search(request: LexicalSearchRequest, user_id: str = Depends(get_current_user_id)):
#     if not request.file_ids:
#         # no specific file, so search entire "bucket" (all user chunks)
#         response = supabase.rpc("search_text_chunks", {
#             "user_id": user_id,
#             "query_text": request.query_text,
#             "match_count": request.match_count
#         }).execute()

#         msg.info(f"GKIRI:: lexical_search whole Bucket PDF: {response}")
#     else:
#         # search only on specific file_ids
#         response = supabase.rpc("search_text_chunks_customfiles", {
#             "user_id": user_id,
#             "file_ids": request.file_ids, #"file_ids": ["UUID1", "UUID2"],  # or an empty list
#             "query_text": request.query_text,
#             "match_count": request.match_count
#         }).execute()

#         msg.info(f"GKIRI:: lexical_search few file IDs PDF: {response}")

#     return response.data


@app.post("/search/lexical")
async def lexical_search(user_id: str, request: LexicalSearchRequest):
    """
    If file_ids is not specified or empty, call 'search_text_chunks'.
    Otherwise, call 'search_text_chunks_customfiles'.
    """
    try:
        if not request.file_ids:
            # Search across all text_chunks for this user
            rpc_resp = supabase.rpc("search_text_chunks", {
                "p_user_id": user_id,
                "p_query_text": request.query_text,
                "p_match_count": request.match_count
            }).execute()

            msg.info(f"GKIRI:: lexical_search whole Bucket PDF: {rpc_resp.data}")
        else:
            # Search only in specific file IDs
            rpc_resp = supabase.rpc("search_text_chunks_customfiles", {
                "p_user_id": user_id,
                "p_file_ids": request.file_ids,
                "p_query_text": request.query_text,
                "p_match_count": request.match_count
            }).execute()

            msg.info(f"GKIRI:: lexical_search few file IDs PDF: {rpc_resp.data}")

        if 'error' in rpc_resp:
            raise HTTPException(status_code=400, detail=rpc_resp['error'].get('message', 'RPC Error'))
        
        return rpc_resp.data

    except Exception as e:
        msg.info(f"GKIRI:: supabase.rpc call lexical search errors: {rpc_resp}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search/semantic")
async def semantic_search(user_id: str, request: SemanticSearchRequest):
    """
    If file_ids is not specified or empty, call 'match_text_chunks'.
    Otherwise, call 'match_text_chunks_customfiles'.

    The function also calls generate_embedding() on the query_text.
    """
    try:
        query_embedding = generate_embedding(request.query_text)

        if not request.file_ids:
            rpc_resp = supabase.rpc("match_text_chunks", {
                "p_user_id": user_id,
                "p_query_embedding": query_embedding,
                "p_match_threshold": request.match_threshold,
                "p_match_count": request.match_count
            }).execute()

            msg.info(f"GKIRI:: lexical_search whole Bucket PDF: {rpc_resp.data}")
        else:
            rpc_resp = supabase.rpc("match_text_chunks_customfiles", {
                "p_user_id": user_id,
                "p_file_ids": request.file_ids,
                "p_query_embedding": query_embedding,
                "p_match_threshold": request.match_threshold,
                "p_match_count": request.match_count
            }).execute()

            msg.info(f"GKIRI:: lexical_search few file IDs PDF: {rpc_resp.data}")

        if 'error' in rpc_resp:
            raise HTTPException(status_code=400, detail=rpc_resp['error'].get('message', 'RPC Error'))

        return rpc_resp.data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search/hybrid")
async def hybrid_search(user_id: str ,request: HybridSearchRequest):
    """
    If file_ids is not specified or empty, call 'hybrid_search_text_chunks'.
    Otherwise, call 'hybrid_search_text_chunks_customfiles'.

    This also calls generate_embedding() on the query_text.
    """
    try:
        msg.info(f"GKIRI1:: hybrid_search user_id : {user_id}")
        msg.info(f"GKIRI1:: hybrid_search request : {request}")
        
        query_embedding = generate_embedding(request.query_text)
        msg.info(f"GKIRI2:: hybrid_search request : {query_embedding}")

        if not request.file_ids:
            rpc_resp = supabase.rpc("hybrid_search_text_chunks_v2", {
                "p_user_id": user_id,
                "p_query_text": request.query_text,
                "p_query_embedding": query_embedding,
                "p_match_count": request.match_count
            }).execute()

            msg.info(f"GKIRI3:: hybrid_search_text_chunks whole Bucket PDF: {rpc_resp.data}")
        else:
            rpc_resp = supabase.rpc("hybrid_search_text_chunks_customfiles_v2", {
                "p_user_id": user_id,
                "p_file_ids": request.file_ids,
                "p_query_text": request.query_text,
                "p_query_embedding": query_embedding,
                "p_match_count": request.match_count
            }).execute()

            msg.info(f"GKIRI3:: hybrid_search_text_chunks_customfiles few file IDs PDF: {rpc_resp.data}")

        if 'error' in rpc_resp:
            raise HTTPException(status_code=400, detail=rpc_resp['error'].get('message', 'RPC Error'))

        return rpc_resp.data

    except Exception as e:
        msg.fail(f"GKIRI4 Error in hybrid_search: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search/hybrid_shared")
async def hybrid_shared_search(user_id: str, request: HybridSearchRequest):
    """
    Perform a hybrid search on shared text chunks.

    This endpoint searches all shared text chunks in the shared_text_chunks table using a combination
    of full-text and semantic search. It leverages the hybrid_search_shared_text_chunks_v2 SQL function
    and does not require a user ID or specific file IDs, as the content is shared across authenticated users.

    Parameters:
    - query_text: The text to search for.
    - match_count: The number of results to return (default: 10).
    - file_ids: Optional list of file IDs (unused in this endpoint).

    Returns:
    - A list of dictionaries containing: id, text, text_similarity, vector_similarity, combined_similarity.

    Raises:
    - HTTPException: 400 if the RPC call returns an error, 500 for other exceptions.
    """
    try:
        # Configure logging similar to msg.info in the reference code
        msg.info(f"GKIRI1:: hybrid_shared_search user_id : {user_id}")
        msg.info(f"GKIRI1:: hybrid_shared_search request : {request}")

        # Generate a 1536-dimensional embedding for the query text
        query_embedding = generate_embedding(request.query_text)
        msg.info(f"GKIRI2:: hybrid_search request : {query_embedding}")

        # Call the hybrid_search_shared_text_chunks_v2 SQL function via Supabase RPC
        rpc_resp = supabase.rpc("hybrid_search_shared_text_chunks_v2", {
            "p_query_text": request.query_text,
            "p_query_embedding": query_embedding,
            "p_match_count": request.match_count,
            "p_full_text_weight": 1.0,  # Default weight for full-text search
            "p_semantic_weight": 1.0,   # Default weight for semantic search
            "p_rrf_k": 50               # Default RRF k value
        }).execute()

        msg.info(f"GKIRI3:: hybrid_search_shared_text_chunks_v2 few file IDs PDF: {rpc_resp.data}")

        # Check for errors in the RPC response
        if 'error' in rpc_resp:
            raise HTTPException(status_code=400, detail=rpc_resp['error'].get('message', 'RPC Error'))
        
        # Return the search results
        return rpc_resp.data

    except Exception as e:
        msg.fail(f"GKIRI4 Error in hybrid_shared_search: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

###############################################################################
# Chat with Files and Buckets
###############################################################################


# New request models
class ChatCustomFilesRequest(BaseModel):
    user_id: str
    file_ids: List[str]
    query: str
    model_id: int

class ChatBucketRequest(BaseModel):
    user_id: str
    query: str
    model_id: int

@app.post("/api/chat_custom_files", response_class=StreamingResponse)
async def chat_custom_files(request: ChatCustomFilesRequest):
    debug_log(f"Received chat_custom_files request: {request}")
    try:
        # 1. Perform hybrid search on specified files
        search_results = await hybrid_search(request.user_id, HybridSearchRequest(
            query_text=request.query,
            match_count=4,
            file_ids=request.file_ids
        ))
        
        # 2. Extract and sort top 4 results by similarity score
        context_chunks = sorted(
            search_results,
            key=lambda x: x.get('similarity', 0),
            reverse=True
        )[:4]
        
        # 3. Combine context chunks into single context with chunk numbering and separation
        formatted_chunks = []
        for i, chunk in enumerate(context_chunks, 1):
            chunk_text = chunk.get('text', '')
            formatted_chunk = f"Here is CHUNK #{i}:\n{chunk_text}\n{'='*50}"  # Adding separator line
            formatted_chunks.append(formatted_chunk)
        
        context = "\n\n".join(formatted_chunks)


        # 4. Create chat prompt
        chat_prompt = f"Based on the following context, please answer the user's question. If the answer cannot be found in the context, say so.\n\nContext:\n{context}\n\nQuestion: {request.query}"

        # 5. Stream response based on model_id
        async def event_stream():
            try:
                generator = None
                if request.model_id in [0, 1]:
                    model_name = "gemini-1.5-flash-002" if request.model_id == 0 else "gemini-2.0-flash"
                    generator = gemini_generator.generate_stream([chat_prompt], [""], [], model_name)
                else:
                    model_name = "deepseek-r1" if request.model_id == 2 else "deepseek-chat"
                    generator = deepseek_generator.generate_stream([chat_prompt], [""], [], model_name)

                async for chunk in generator:
                    if chunk["finish_reason"] == "stop":
                        break
                    yield f"data: {json.dumps({'type': 'text-delta', 'content': chunk['message']})}\n\n"
                
                yield f"data: {json.dumps({'type': 'finish', 'content': ''})}\n\n"

            except Exception as e:
                msg.fail(f"Streaming failed: {str(e)}")
                yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    except Exception as e:
        msg.fail(f"Error in chat_custom_files: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat_bucket", response_class=StreamingResponse)
async def chat_bucket(request: ChatBucketRequest):
    #debug_log(f"Received chat_bucket request: {request}")
    msg.info(f"GKIRI1:: chat_bucket: {request}")
    try:
        # 1. Perform hybrid search on entire bucket (no file_ids specified)
        search_results = await hybrid_search(request.user_id, HybridSearchRequest(
            query_text=request.query,
            match_count=4
        ))
        
        msg.info(f"GKIRI2::chat_bucket  hybrid_search search_results: {search_results}")
        # 2. Extract and sort top 4 results by similarity score
        context_chunks = sorted(
            search_results,
            key=lambda x: x.get('similarity', 0),
            reverse=True
        )[:4]
        
        # 3. Combine context chunks into single context with chunk numbering and separation
        formatted_chunks = []
        for i, chunk in enumerate(context_chunks, 1):
            chunk_text = chunk.get('text', '')
            formatted_chunk = f"Here is CHUNK #{i}:\n{chunk_text}\n{'='*50}"  # Adding separator line
            formatted_chunks.append(formatted_chunk)
        
        context = "\n\n".join(formatted_chunks)
        
        # 4. Create chat prompt
        chat_prompt = f"Based on the following context, please answer the user's question. If the answer cannot be found in the context, say so.\n\nContext:\n{context}\n\nQuestion: {request.query}"

        # 5. Stream response based on model_id
        async def event_stream():
            try:
                generator = None
                if request.model_id in [0, 1]:
                    model_name = "gemini-1.5-flash-002" if request.model_id == 0 else "gemini-2.0-flash"
                    generator = gemini_generator.generate_stream([chat_prompt], [""], [], model_name)
                else:
                    model_name = "deepseek-r1" if request.model_id == 2 else "deepseek-chat"
                    generator = deepseek_generator.generate_stream([chat_prompt], [""], [], model_name)

                async for chunk in generator:
                    if chunk["finish_reason"] == "stop":
                        break
                    yield f"data: {json.dumps({'type': 'text-delta', 'content': chunk['message']})}\n\n"
                
                yield f"data: {json.dumps({'type': 'finish', 'content': ''})}\n\n"

            except Exception as e:
                msg.fail(f"Streaming failed: {str(e)}")
                yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    except Exception as e:
        msg.fail(f"Error in chat_bucket: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


#public sttaic books bucket shared for all users    
@app.post("/api/chat_shared", response_class=StreamingResponse)
async def chat_shared(request: ChatBucketRequest):
    #debug_log(f"Received chat_bucket request: {request}")
    msg.info(f"GKIRI1:: chat_shared: {request}")
    try:
        # 1. Perform hybrid search on entire bucket (no file_ids specified)
        search_results = await hybrid_shared_search(request.user_id, HybridSearchRequest(
            query_text=request.query,
            match_count=4
        ))
        
        msg.info(f"GKIRI2::chat_shared  hybrid_shared_search search_results: {search_results}")
        # 2. Extract and sort top 4 results by similarity score
        context_chunks = sorted(
            search_results,
            key=lambda x: x.get('similarity', 0),
            reverse=True
        )[:4]
        
        # 3. Combine context chunks into single context with chunk numbering and separation
        formatted_chunks = []
        for i, chunk in enumerate(context_chunks, 1):
            chunk_text = chunk.get('text', '')
            formatted_chunk = f"Here is CHUNK #{i}:\n{chunk_text}\n{'='*50}"  # Adding separator line
            formatted_chunks.append(formatted_chunk)
        
        context = "\n\n".join(formatted_chunks)
        
        # 4. Create chat prompt
        chat_prompt = f"Based on the following context, please answer the user's question. If the answer cannot be found in the context, say so.\n\nContext:\n{context}\n\nQuestion: {request.query}"

        # 5. Stream response based on model_id
        async def event_stream():
            try:
                generator = None
                if request.model_id in [0, 1]:
                    model_name = "gemini-1.5-flash-002" if request.model_id == 0 else "gemini-2.0-flash"
                    generator = gemini_generator.generate_stream([chat_prompt], [""], [], model_name)
                else:
                    model_name = "deepseek-r1" if request.model_id == 2 else "deepseek-chat"
                    generator = deepseek_generator.generate_stream([chat_prompt], [""], [], model_name)

                async for chunk in generator:
                    if chunk["finish_reason"] == "stop":
                        break
                    yield f"data: {json.dumps({'type': 'text-delta', 'content': chunk['message']})}\n\n"
                
                yield f"data: {json.dumps({'type': 'finish', 'content': ''})}\n\n"

            except Exception as e:
                msg.fail(f"Streaming failed: {str(e)}")
                yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    except Exception as e:
        msg.fail(f"Error in chat_shared: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

############################web search section


import aiohttp

SERPER_API_KEY=os.getenv("SERPER_API_KEY")

async def serper_search_async(query, num_results=20, location="India"):
    """
    Performs a search using the Serper.dev API asynchronously and returns the JSON response.

    Args:
        query (str): The search query string.
        num_results (int): The number of search results to retrieve (default: 20).
        location (str): The location for the search (default: "India").

    Returns:
        str: A string containing the JSON response from the Serper.dev API.
        None: Returns None if the request fails. Also prints an error message in case of a failed request.
    """
    url = "https://google.serper.dev/search"
    payload = json.dumps({
        "q": query,
        "num": num_results,
        "location": location,
    })
    headers = {
        'X-API-KEY': SERPER_API_KEY,
        'Content-Type': 'application/json'
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=payload) as response:
                # If the response status is not 200, raise an exception
                if response.status != 200:
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=response.status,
                        message=f"Request failed with status {response.status}",
                    )
                return await response.text()
    except aiohttp.ClientError as e:
        # Print to stderr in case of error
        import sys
        print(f"Error during Serper API request: {e}", file=sys.stderr)
        return None


import ast

def parse_numbers(input_string):
    """
    Parse a string to extract a list of integers.
    Handles various input formats including:
    - '[0, 1, 3, 5, 8]'
    - '0, 1, 3, 5, 8'
    - '0 1 3 5 8'
    - Text containing numbers like 'The indices are 0, 1, 3, 5, 8'
    
    Args:
        input_string (str): The input string to parse.
        
    Returns:
        list: A list of integers.
        
    Raises:
        ValueError: If no valid integers can be extracted.
    """
    try:
        # First try direct ast.literal_eval for standard list format
        try:
            parsed = ast.literal_eval(input_string)
            if isinstance(parsed, list) and all(isinstance(x, int) for x in parsed):
                return parsed
        except (ValueError, SyntaxError):
            pass

        # If that fails, try to extract numbers using regex
        import re
        numbers = re.findall(r'\d+', input_string)
        if numbers:
            return [int(n) for n in numbers]
            
        raise ValueError("No valid integers found in input string.")
            
    except Exception as e:
        raise ValueError(f"Invalid input format. Expected a string containing numbers. Error: {str(e)}")


async def filter_top_search_results_with_gemini(
    search_data: dict,
    top_n: int = 5,
    model_id: int = 1,
    ) -> List:
    
    # Validate input
    if not isinstance(search_data, dict) or 'searchParameters' not in search_data or 'organic' not in search_data:
        msg.warn("Invalid search_data format")
        return []
        
    query = search_data['searchParameters']['q']
    organic_results = search_data['organic']

    # --- Construct the Prompt for Gemini ---
    filter_prompt = f"""
        Task: You need to help another UPSC AI assistant by analysing and selecting top "{top_n}" search results that are most relevant to answer the user query very correctly, accurately and best way .
        Also given in order of  first one being most relevant and then next and so on .Think carefully and analyse title, url and snippet to make decision and give just indexes in array.
        Final answer should be array of indexes separated by comma and nothing else.

        Sample output format = [0,5,8,11,15]

        Original Search Query: "{query}"

        Here are Search Results:
        {organic_results}
        """
    
    # Generate response based on model_id
    try:
        if model_id == 0:
            filter_results = await generate_gemini_response(filter_prompt, "", "gemini-1.5-flash-002")
        elif model_id == 1:
            filter_results = await generate_gemini_response(filter_prompt, "", "gemini-2.0-flash")
        elif model_id == 2:
            filter_results = await generate_deepseek_response(filter_prompt, "", "deepseek-r1")
        elif model_id == 3:
            filter_results = await generate_deepseek_response(filter_prompt, "", "deepseek-chat")
        else:
            filter_results = await generate_gemini_response(filter_prompt, "", "gemini-1.5-flash-002")

        # Parse the response to get the list of indices
        indices = parse_numbers(filter_results)
        # Return only the top N results
        return indices[:top_n]
    except Exception as e:
        msg.warn(f"Error in filter_top_search_results_with_gemini: {str(e)}")
        return []



import trafilatura
import httpx # Async HTTP client
import logging
from typing import Optional # Use Optional for older Python versions if needed

# Configure basic logging (important for production)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configure a reusable httpx client (good practice for connection pooling)
# Set appropriate timeouts for production!
# Adjust limits based on expected load and server capabilities
# keepalive_expiry: How long to keep connections open after last use.
# max_keepalive_connections: Max idle connections to keep per host. None = no limit.
# max_connections: Max total connections. None = no limit. Adjust based on ulimit!
limits = httpx.Limits(max_keepalive_connections=20, max_connections=100, keepalive_expiry=15)
timeout_config = httpx.Timeout(15.0, connect=5.0) # 15s total, 5s connect timeout

# Create the client outside the function if you plan to reuse it across multiple calls
# in your API. If creating per request, use 'async with httpx.AsyncClient(...)' inside.
# For this example function structure, creating inside is simpler to show.
# Consider dependency injection in your API framework (e.g., FastAPI).

async def extract_markdown_from_url_async(
    url: str,
    client: httpx.AsyncClient # Allow passing a pre-configured client
) -> Optional[str]:
    """
    Asynchronously fetches a webpage using httpx and extracts its main content
    as Markdown using Trafilatura, running extraction in a thread pool.

    Designed for use in high-concurrency environments like async web APIs.

    Args:
        url (str): The URL of the webpage to process.
        client (httpx.AsyncClient): An active httpx AsyncClient instance.

    Returns:
        Optional[str]: The extracted content in Markdown format if successful,
                       otherwise None.
    """
    logging.info(f"Attempting to fetch URL asynchronously: {url}")
    downloaded_content: Optional[bytes] = None

    try:
        # --- Asynchronous HTTP GET Request ---
        response = await client.get(url, follow_redirects=True)
        response.raise_for_status() # Raise HTTPStatusError for 4xx/5xx responses
        downloaded_content = response.content # Get raw bytes, trafilatura handles encoding
        logging.info(f"Successfully downloaded content ({len(downloaded_content)} bytes) from {url}")

    except httpx.TimeoutException:
        logging.warning(f"Request timed out for {url}")
        return None
    except httpx.RequestError as exc:
        # Handles connection errors, invalid URLs, resolution errors, etc.
        logging.warning(f"HTTP request failed for {url}: {exc}")
        return None
    except Exception as e:
        # Catch potential unexpected errors during download/response handling
        logging.error(f"Unexpected error during download phase for {url}: {e}", exc_info=True)
        return None

    if not downloaded_content:
        # Should be caught by exceptions above, but belt-and-suspenders
        logging.warning(f"Download succeeded but content was empty for {url}.")
        return None

    try:
        # --- Run Blocking Trafilatura Extraction in Thread Pool ---
        # This prevents blocking the main asyncio event loop
        logging.debug(f"Starting Trafilatura extraction for {url} in thread pool.")
        markdown_output = await asyncio.to_thread(
            trafilatura.extract, # The blocking function to call
            downloaded_content,  # Argument for the function
            output_format='markdown', # Keyword argument
            include_comments=False, # Example: other trafilatura options
            include_tables=True
        )
        logging.debug(f"Finished Trafilatura extraction for {url}.")

        if not markdown_output:
            logging.warning(f"Content downloaded, but Trafilatura couldn't extract main content from {url}.")
            return None

        logging.info(f"Successfully extracted Markdown content from {url}.")
        return markdown_output

    except Exception as e:
        # Catch potential errors *within* trafilatura.extract
        logging.error(f"An unexpected error occurred during Trafilatura extraction for {url}: {e}", exc_info=True)
        return None



async def process_urls_to_markdown(urls: List[str], max_concurrent: int = 10) -> Dict[str, Optional[str]]:
    """
    Process a list of URLs and extract markdown content from each one.
    
    Args:
        urls (List[str]): List of URLs to process
        max_concurrent (int): Maximum number of concurrent requests (default: 5)
        
    Returns:
        Dict[str, Optional[str]]: Dictionary mapping URLs to their extracted markdown content
    """
    results = {}
    
    # Configure httpx client with reasonable limits
    limits = httpx.Limits(max_keepalive_connections=20, max_connections=100, keepalive_expiry=15)
    timeout_config = httpx.Timeout(15.0, connect=5.0)  # 30s total timeout, 10s connect timeout
    
    try:
        async with httpx.AsyncClient(limits=limits, timeout=timeout_config, http2=True) as client:
            # Process URLs in chunks to control concurrency
            for i in range(0, len(urls), max_concurrent):
                chunk = urls[i:i + max_concurrent]
                tasks = [extract_markdown_from_url_async(url, client) for url in chunk]
                
                # Gather results for this chunk
                chunk_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results
                for url, result in zip(chunk, chunk_results):
                    if isinstance(result, Exception):
                        logging.error(f"Failed to process {url}: {str(result)}")
                        results[url] = None
                    else:
                        results[url] = result
                        
                # Small delay between chunks to avoid overwhelming servers
                if i + max_concurrent < len(urls):
                    await asyncio.sleep(1)
                    
    except Exception as e:
        logging.error(f"Error processing URLs: {str(e)}", exc_info=True)
        # Mark remaining URLs as failed
        for url in urls:
            if url not in results:
                results[url] = None
                
    return results




#public static books bucket shared for all users web search  
@app.post("/api/chat_search", response_class=StreamingResponse)
async def chat_search(request: ChatBucketRequest):
    #debug_log(f"Received chat_bucket request: {request}")
    msg.info(f"GKIRI1:: chat_search: {request}")
    try:
        #1 web search
        web_search_results = await serper_search_async(request.query, num_results=20, location="India")


        search_data = json.loads(web_search_results)

        #1.1 filter top n relvant search results
        top_n=4
        final_web_search_results = await filter_top_search_results_with_gemini(search_data,top_n,1)

        url_list=[]
        for index in range(len(final_web_search_results)):
            url_list.append(search_data['organic'][index]['link'])

        #2 call process_urls_to_markdown
        web_search_markdown_results = await process_urls_to_markdown(url_list)

        #3 web_search_markdown_results
        # Format web search markdown results with URL attribution
        formatted_web_content = ""
        for idx, (url, markdown_content) in enumerate(web_search_markdown_results.items(), 1):
            if markdown_content:  # Only add if content exists
                formatted_web_content += f"Here is web source #{idx} of url: '{url}'\n\n{markdown_content}\n\n"

        
        msg.info(f"GKIRI2::chat_search  formatted_web_content search_results: {formatted_web_content}")

        # 4. Perform hybrid search on entire bucket (no file_ids specified)
        search_results = await hybrid_shared_search(request.user_id, HybridSearchRequest(
            query_text=request.query,
            match_count=4
        ))
        
        msg.info(f"GKIRI2::chat_search  hybrid_shared_search search_results: {search_results}")
        # 5. Extract and sort top 4 results by similarity score
        context_chunks = sorted(
            search_results,
            key=lambda x: x.get('similarity', 0),
            reverse=True
        )[:4]
        
        # 6. Combine context chunks into single context with chunk numbering and separation
        formatted_chunks = []
        for i, chunk in enumerate(context_chunks, 1):
            chunk_text = chunk.get('text', '')
            doc_name = chunk.get('doc_name', 'Unknown Document')
            formatted_chunk = f"Document: {doc_name}\nContent:\n{chunk_text}\n{'='*50}"  # Adding separator line
            formatted_chunks.append(formatted_chunk)
        
        context = "\n\n".join(formatted_chunks)
        
        # 7. Create enhanced chat prompt with clear instructions for source attribution
        # chat_prompt = f"""You are a helpful UPSC AI assistant that provides well-researched, comprehensive answers based on multiple sources.

        # CONTEXT FROM KNOWLEDGE BASE:
        # {context}

        # WEB-BASED CONTENT:
        # {formatted_web_content}

        # Instructions for your response:
        # 1. Provide a detailed, well-structured answer to the question
        # 2. Use numbered citations in square brackets [1], [2], etc. for ALL references
        # 3. After your main answer, include a numbered reference list with full source information
        # 4. Format your citations EXACTLY as follows:

        # For knowledge base sources:
        # [1]: Document Title | Knowledge Base

        # For web sources:
        # [2]: Title of Web Page | https://example.com/full-url

        # Question: {request.query}

        # IMPORTANT FORMATTING REQUIREMENTS:
        # - Use numbered citations [n] inline within your text whenever you reference information from a source
        # - Place citations immediately after the relevant statement
        # - Include a complete numbered list of all references at the end of your response
        # - Maintain consistent citation numbering throughout your answer
        # - Do not use footnotes, parenthetical citations, or any other citation style
        # - Any statement of fact MUST have at least one citation

        # Your response structure should follow this format:
        # 1. Detailed answer with inline numbered citations [n]
        # 2. Line break
        # 3. "References:" heading
        # 4. Numbered list of all sources in the format specified above

        # Example reference format:
        # References:
        # [1]: NCERT History Textbook | Knowledge Base
        # [2]: Evolution of Administration in India | https://example.com/indian-administration

        # If you cannot find a reliable answer from the provided sources, clearly state this and suggest what information would be needed.
        # """

        ###### para level citation
        # chat_prompt = f"""You are a helpful UPSC AI assistant providing clear, comprehensive answers based on multiple reliable sources.

        # CONTEXT FROM KNOWLEDGE BASE:
        # {context}

        # WEB-BASED CONTENT:
        # {formatted_web_content}

        # Instructions for your response:
        # 1. Provide a structured, concise, and easily readable answer to the question.
        # 2. Use numbered inline citations [1], [2], etc., sparingly—cite only the single best or most relevant source if multiple URLs convey essentially the same point.
        # 3. Prefer paragraph-level citations over sentence-level citations whenever possible to avoid overwhelming the reader.
        # 4. Include a numbered reference list at the end, formatted exactly as follows:

        # For knowledge base sources:
        # [1]: Document Title | Knowledge Base

        # For web sources:
        # [2]: Title of Web Page | https://example.com/full-url

        # Question: {request.query}

        # IMPORTANT FORMATTING GUIDELINES:
        # - Inline citations [n] should appear immediately after the paragraph or statement they reference.
        # - All key facts and claims must be supported by at least one clearly cited source.
        # - Do NOT use footnotes, parenthetical citations, or any other citation style.
        # - Provide citations only where genuinely helpful or necessary for verification.

        # Your answer should have this structure:
        # 1. Structured, concise answer (with selective inline citations)
        # 2. Line break
        # 3. "References:" heading
        # 4. Numbered list of cited sources formatted per instructions

        # Example:

        # References:
        # [1]: NCERT History Textbook | Knowledge Base
        # [2]: Evolution of Administration in India | https://example.com/indian-administration

        # If a reliable answer isn't available from the sources provided, clearly state this and suggest the type of information required for a complete answer."""

        #####better markdown + para level citation
        # chat_prompt = f"""You are a helpful UPSC AI assistant providing clear, holistic, and structured answers tailored specifically for UPSC aspirants, based on multiple reliable sources.

        # CONTEXT FROM KNOWLEDGE BASE:
        # {context}

        # WEB-BASED CONTENT:
        # {formatted_web_content}

        # Guidelines for crafting your answer:
        # 1. Present a holistic, logically structured, and easy-to-follow answer.
        # 2. Organize your response using clear markdown headings (##), subheadings (###), bullet points, and numbered lists to enhance readability and flow.
        # 3. Connect key points clearly to build a coherent narrative, making connections between different pieces of information obvious.
        # 4. Provide inline citations sparingly and effectively—only cite the single most relevant source if multiple sources convey similar points.
        # 5. Prefer paragraph-level citations rather than frequent sentence-level citations to maintain readability.

        # CITATION FORMAT:
        # - Inline citations: Use numbered references [1], [2], etc., placed immediately after the paragraph or statement referenced.
        # - Reference List: Include at the end of your response under a clearly marked heading "## References."

        # Reference formatting:
        # - For knowledge base sources:
        # [1]: Document Title | Knowledge Base

        # - For web sources:
        # [2]: Title of Web Page | https://example.com/full-url

        # Question: {request.query}

        # IMPORTANT FORMATTING TIPS:
        # - Clearly structure your response with logical flow: start with an introduction or overview, follow with main points organized into sections and subsections, and conclude with a concise summary if necessary.
        # - All significant facts and claims must be supported by at least one citation.
        # - Use a professional yet straightforward language suitable for UPSC aspirants.

        # Answer Format Example:

        # ## Introduction
        # Briefly introduce and summarize key points.

        # ## Main Topic Heading
        # ### Subheading
        # - Bullet point or numbered list if appropriate

        # ## Conclusion
        # Briefly summarize or highlight the most critical points.

        # ## References
        # [1]: NCERT History Textbook | Knowledge Base
        # [2]: Evolution of Administration in India | https://example.com/indian-administration

        # If sufficient information isn't available from provided sources, clearly state this and suggest what additional information would be helpful for a comprehensive answer."""

        ## direct hyper links and robus response
        # chat_prompt = f"""You are a helpful UPSC AI assistant providing clear, holistic, and structured answers tailored specifically for UPSC aspirants, based on multiple reliable sources.

        # CONTEXT FROM KNOWLEDGE BASE:
        # {context}

        # WEB-BASED CONTENT:
        # {formatted_web_content}

        # Guidelines for crafting your answer:
        # 1. Present a holistic, logically structured, and easy-to-follow answer.
        # 2. Organize your response using clear markdown headings (##), subheadings (###), bullet points, and numbered lists to enhance readability and flow.
        # 3. Connect key points clearly to build a coherent narrative, making connections between different pieces of information obvious.
        # 4. Provide inline citations sparingly and effectively—only cite the single most relevant source if multiple sources convey similar points.
        # 5. Prefer paragraph-level citations rather than frequent sentence-level citations to maintain readability.

        # CITATION FORMAT:
        # - For knowledge base sources: <sup class="citation" title="Document Title | Knowledge Base">number</sup>
        # - For web sources: <sup class="citation" title="Title of Web Page | https://example.com/full-url"><a href="https://example.com/full-url">number</a></sup>
        # - Assign a unique number to each distinct source, starting from 1.

        # Reference List:
        # - Include at the end of your response under a clearly marked heading "## References."
        # - Format references as:
        # - [number]: Document Title | Knowledge Base (for knowledge base sources)
        # - [number]: Title of Web Page | https://example.com/full-url (for web sources)

        # Question: {request.query}

        # IMPORTANT FORMATTING TIPS:
        # - Clearly structure your response with logical flow: start with an introduction or overview, follow with main points organized into sections and subsections, and conclude with a concise summary if necessary.
        # - All significant facts and claims must be supported by at least one citation.
        # - Use a professional yet straightforward language suitable for UPSC aspirants.

        # Answer Format Example:

        # ## Introduction
        # Briefly introduce and summarize key points.<sup class="citation" title="NCERT History Textbook | Knowledge Base">1</sup>

        # ## Main Topic Heading
        # ### Subheading
        # - Bullet point or numbered list if appropriate.<sup class="citation" title="Evolution of Administration in India | https://example.com/indian-administration"><a href="https://example.com/indian-administration">2</a></sup>

        # ## Conclusion
        # Briefly summarize or highlight the most critical points.

        # ## References
        # [1]: NCERT History Textbook | Knowledge Base
        # [2]: Evolution of Administration in India | https://example.com/indian-administration

        # If sufficient information isn't available from provided sources, clearly state this and suggest what additional information would be helpful for a comprehensive answer."""


        #####better markdown + para level citation
        chat_prompt = f"""You are a helpful UPSC AI assistant providing clear, holistic, and structured answers tailored specifically for UPSC aspirants, based on multiple reliable sources.

        CONTEXT FROM KNOWLEDGE BASE:
        {context}

        WEB-BASED CONTENT:
        {formatted_web_content}

        Guidelines for crafting your answer:
        1. Present a holistic, logically structured, and easy-to-follow answer.
        2. Organize your response using clear markdown headings (##), subheadings (###), bullet points, and numbered lists to enhance readability and flow.
        3. Connect key points clearly to build a coherent narrative, making connections between different pieces of information obvious.
        4. Provide inline citations sparingly and effectively—only cite the single most relevant source if multiple sources convey similar points.
        5. Prefer paragraph-level citations rather than frequent sentence-level citations to maintain readability.

        CITATION FORMAT:
        - Please strictly follow below syntax and citation format as its very critical for the project
        - Inline citations: Use unique tokens in the form ((cite:1)), ((cite:2)), etc., placed immediately after the relevant paragraph or statement.
          Always use numeric references in ascending order, starting from 1, like ((cite:1)), ((cite:2)).
          Never use labels like ((cite:web2)), ((cite:kb1)), or anything other than numeric tokens.
          If you see references in the provided context labeled “web2” or “web4,” map them to numeric references in ascending order. For example, if “web4” is your second source, you must cite it as ((cite:2)).
          If multiple sources are being cited for a single point, combine them on one line using the format: ((cite:2), (cite:4)).

        - Reference List: Include at the end of your response under the heading "## References." For each citation, use the format:
        ((ref:1)): [Title or short description] | [URL or “Knowledge Base”]
        ((ref:2)): [Title or short description] | [URL or “Knowledge Base”]


        Question: {request.query}

        IMPORTANT FORMATTING TIPS:
        - Clearly structure your response with logical flow: start with an introduction or overview, follow with main points organized into sections and subsections, and conclude with a concise summary if necessary.
        - All significant facts and claims must be supported by at least one citation.
        - Use a professional yet straightforward language suitable for UPSC aspirants.

        Answer Format Example:

        ## Introduction
        Briefly introduce and summarize key points.

        ## Main Topic Heading
        ### Subheading
        - Bullet point or numbered list if appropriate. For example, include supporting data or points with inline citations such as ((cite:1)).

        ## Conclusion
        Briefly summarize or highlight the most critical points.

        ## References
        ((ref:1)): NCERT History Textbook | Knowledge Base  
        ((ref:2)): Evolution of Administration in India | https://example.com/indian-administration

        If sufficient information isn't available from the provided sources, clearly state this and suggest what additional information would be helpful for a comprehensive answer.""" 

        # 8. Stream response based on model_id
        async def event_stream():
            try:
                generator = None
                if request.model_id in [0, 1]:
                    model_name = "gemini-1.5-flash-002" if request.model_id == 0 else "gemini-2.0-flash"
                    generator = gemini_generator.generate_stream([chat_prompt], [""], [], model_name)
                else:
                    model_name = "deepseek-r1" if request.model_id == 2 else "deepseek-chat"
                    generator = deepseek_generator.generate_stream([chat_prompt], [""], [], model_name)

                async for chunk in generator:
                    if chunk["finish_reason"] == "stop":
                        break
                    yield f"data: {json.dumps({'type': 'text-delta', 'content': chunk['message']})}\n\n"
                
                yield f"data: {json.dumps({'type': 'finish', 'content': ''})}\n\n"

            except Exception as e:
                msg.fail(f"Streaming failed: {str(e)}")
                yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    except Exception as e:
        msg.fail(f"Error in chat_search: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))



#public static books bucket shared for all users web search  
@app.post("/api/search", response_class=StreamingResponse)
async def search(request: ChatBucketRequest):
    #debug_log(f"Received chat_bucket request: {request}")
    msg.info(f"GKIRI1:: search: {request}")
    try:
        #1 web search
        web_search_results = await serper_search_async(request.query, num_results=20, location="India")


        search_data = json.loads(web_search_results)

        #1.1 filter top n relvant search results
        top_n=10
        final_web_search_results = await filter_top_search_results_with_gemini(search_data,top_n,1)

        url_list=[]
        for index in range(len(final_web_search_results)):
            url_list.append(search_data['organic'][index]['link'])

        #2 call process_urls_to_markdown
        web_search_markdown_results = await process_urls_to_markdown(url_list)

        #3 web_search_markdown_results
        # Format web search markdown results with URL attribution
        formatted_web_content = ""
        for idx, (url, markdown_content) in enumerate(web_search_markdown_results.items(), 1):
            if markdown_content:  # Only add if content exists
                formatted_web_content += f"Here is web source #{idx} of url: '{url}'\n\n{markdown_content}\n\n"

        
        msg.info(f"GKIRI2::search  formatted_web_content search_results: {formatted_web_content}")

       
        # 7. Create enhanced chat prompt with clear instructions for source attribution
        chat_prompt = f"""You are a helpful UPSC AI assistant that provides well-researched answers based on multiple sources in the internet. 
        Please analyze the following information carefully and provide a comprehensive answer:

        WEB-BASED CONTENT:
        {formatted_web_content}

        Instructions for your response:
        1. Synthesize information from all the web sources
        2. For each key point or claim, cite the specific source:
        - For web content: Cite the web source URL
        3. If information appears in multiple sources, acknowledge all relevant sources
        4. If sources provide conflicting information, highlight the differences
        5. If the answer cannot be found in the provided context, clearly state this
        6. Structure your response in a clear, logical manner with proper paragraphs

        Question: {request.query}

        Please provide a detailed answer with proper citations.
        """

        # 8. Stream response based on model_id
        async def event_stream():
            try:
                generator = None
                if request.model_id in [0, 1]:
                    model_name = "gemini-1.5-flash-002" if request.model_id == 0 else "gemini-2.0-flash"
                    generator = gemini_generator.generate_stream([chat_prompt], [""], [], model_name)
                else:
                    model_name = "deepseek-r1" if request.model_id == 2 else "deepseek-chat"
                    generator = deepseek_generator.generate_stream([chat_prompt], [""], [], model_name)

                async for chunk in generator:
                    if chunk["finish_reason"] == "stop":
                        break
                    yield f"data: {json.dumps({'type': 'text-delta', 'content': chunk['message']})}\n\n"
                
                yield f"data: {json.dumps({'type': 'finish', 'content': ''})}\n\n"

            except Exception as e:
                msg.fail(f"Streaming failed: {str(e)}")
                yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    except Exception as e:
        msg.fail(f"Error in search: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


