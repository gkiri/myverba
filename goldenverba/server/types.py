from pydantic import BaseModel
from goldenverba.components.types import FileData
from typing import Optional, List



class QueryPayload(BaseModel):
    query: str


class ConversationItem(BaseModel):
    type: str
    content: str


class GeneratePayload(BaseModel):
    query: str
    context: str
    conversation: list[ConversationItem]


class SearchQueryPayload(BaseModel):
    query: str
    doc_type: str
    page: int
    pageSize: int


class GetDocumentPayload(BaseModel):
    document_id: str


class ResetPayload(BaseModel):
    resetMode: str


class LoadPayload(BaseModel):
    reader: str
    chunker: str
    embedder: str
    fileBytes: list[str]
    fileNames: list[str]
    filePath: str
    document_type: str
    chunkUnits: int
    chunkOverlap: int


class ImportPayload(BaseModel):
    data: list[FileData]
    textValues: list[str]
    config: dict


class ConfigPayload(BaseModel):
    config: dict


class GetComponentPayload(BaseModel):
    component: str


class SetComponentPayload(BaseModel):
    component: str
    selected_component: str


class TextToVideoRequest(BaseModel):
    topic: str
    num_scenes: Optional[int] = 3
    user_id: str


class TextToVideoResponse(BaseModel):
    status: str
    video_path: Optional[str] = None
    storage_video_url: Optional[str] = None
    individual_videos: Optional[List[str]] = None
    scenes_completed: int = 0
    scenes_total: int = 0
    processing_time: Optional[float] = None
    error: Optional[str] = None
