from pydantic import BaseModel
from typing import Literal,List


class InputText(BaseModel):
    type: Literal["text"]
    text: str
    description: str


class InputNumber(BaseModel):
    type: Literal["number"]
    value: int
    description: str


class FileData(BaseModel):
    filename: str
    extension: str
    content: str


class Question(BaseModel):
    id: int              # Unique identifier for the question
    text: str            # The question text
    options: List[str]   # A list of answer options
    correctAnswer: str   # The correct answer
    explanation: str = "" # Explanation for the correct answer (optional)
