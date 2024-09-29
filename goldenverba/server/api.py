from fastapi import FastAPI, WebSocket, UploadFile, status,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import json
import uuid
import os
from pathlib import Path

from dotenv import load_dotenv
from starlette.websockets import WebSocketDisconnect
from wasabi import msg  # type: ignore[import]
import time
import random
from goldenverba.components.generation.GPT3Generator import GPT3Generator
from goldenverba.components.generation.GroqGenerator import GroqGenerator
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
from goldenverba.server.prompts import get_prompt
from goldenverba.server.supabase.supabase_client import supabase

load_dotenv()

gpt3_generator = GPT3Generator()
groq_generator = GroqGenerator()

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
    "http://3.83.67.48:8000",
]

# Add middleware for handling Cross Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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
#         prompt = f"Generate a Mermaid code block to visualize the following: {payload.query}"

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

        bullet_points_response = await generate_groq_response(prompt,payload.query)
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
        
        prompt = "Provide a concise summary of the following: "
        summary_response = await generate_groq_response(prompt,payload.query)
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
        
        summary_prompt = get_prompt("VISUALIZE", topic=payload.query)

        mermaid_response = await generate_gpt3_response(summary_prompt,payload.query)
        #mermaid_response = await generate_groq_response(summary_prompt,payload.query)
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

class SyllabusChapterResponse(BaseModel):
    chapter_content: str
    user_progress: dict
    prompt: str
    llm_response: str

@app.post("/api/get_syllabus_chapter_with_userstatus", response_model=SyllabusChapterResponse)
async def get_syllabus_chapter_with_userstatus(request: GetSyllabusChapterRequest):
    debug_log(f"Received get_syllabus_chapter_with_userstatus request: {request}")
    try:
        # 1. Fetch chapter content from Weaviate
        chapter_id = request.chapter_id
        user_id = request.user_id

        msg.info(f"Fetching content for Chapter ID: {chapter_id} for User ID: {user_id}")

        # Assuming manager.weaviate_client is the Weaviate client
        # chapter_query = {
        #     "class_name": "VERBA_Syllabus_Chapters",
        #     "where": {
        #         "path": ["ch_id"],
        #         "operator": "Equal",
        #         "valueText": chapter_id
        #     }
        # }
        chapter_query = (
            manager.client.query
            .get("VERBA_Syllabus_Chapters", ["chapter_content"])  # Class name and fields to retrieve
            .with_where({
                "path": ["ch_id"],
                "operator": "Equal",
                "valueText": chapter_id
            })
            .with_limit(1)
            .do()
        )

        print("Gkiri:chapter_query Format:", chapter_query)

        # Check for the result
        if not chapter_query["data"]["Get"]["VERBA_Syllabus_Chapters"]:
            raise HTTPException(status_code=404, detail="Chapter not found")

        #chapter_result = manager.client.query.get(**chapter_query).with_limit(1).do()

        chapter_content = chapter_query["data"]["Get"]["VERBA_Syllabus_Chapters"][0].get("chapter_content", "")

        # 2. Fetch user progress from Supabase
        user_progress = await get_user_chapter_progress(user_id, chapter_id)

        # 3. Get relevant prompt
        prompt_template = "Provide a personalized learning plan based on the user's progress and the chapter content."

        # You can customize the prompt as needed, possibly using predefined prompts
        prompt = f"{prompt_template}\n\nChapter Content:\n{chapter_content}\n\nUser Progress:\n{json.dumps(user_progress)}"

        # 4. Call LLM API
        llm_response = await generate_gpt3_response(prompt, chapter_content)

        return SyllabusChapterResponse(
            chapter_content=chapter_content,
            user_progress=user_progress,
            prompt=prompt,
            llm_response=llm_response
        )

    except HTTPException as he:
        raise he
    except Exception as e:
        msg.fail(f"Error in get_syllabus_chapter_with_userstatus: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def get_user_chapter_progress(user_id: str, chapter_id: str) -> dict:
    debug_log(f"Fetching user progress for Chapter ID: {chapter_id} for User ID: {user_id}")
    try:
        response = await asyncio.get_event_loop().run_in_executor(
            None, lambda: supabase.table("GS1").select("*").eq("user_id", user_id).single().execute()
        )
        if response.status_code == 200 and response.data:
            user_progress = response.data
            chapter_progress = user_progress.get(chapter_id, {})
            return chapter_progress
        else:
            msg.warn(f"No progress found for user_id: {user_id}, chapter_id: {chapter_id}")
            return {}
    except Exception as e:
        msg.warn(f"Failed to retrieve user progress for Chapter ID {chapter_id}: {e}")
        return {}