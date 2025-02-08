from pydantic import BaseModel, field_validator 
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


# Question model for the Mock Exam
class Question(BaseModel):
    global_questionID: int # Unique identifier for the question - made optional for import 
    year: str                # Year of the exam question
    question: str          # The question text
    options: List[str]     # A list of answer options
    answer_key: str         # The correct answer key (e.g., 'a', 'b', 'c', 'd') 
    topic: str = ""           # Topic of the question (optional)
    description: str = ""      # Explanation for the answer (optional)
    question_number: str = ""   # Question number in the original exam (optional) 

    # @field_validator("year", mode='before')
    # def validate_year(cls, value):
    #     if isinstance(value, str):
    #         try:
    #             return int(value)
    #         except ValueError:
    #             raise ValueError("Year must be an integer")
    #     return value


class MockQuestion(BaseModel):
    global_questionID: str  # Unique identifier for the question
    year: str = ""          # Allow empty string if 'None' is encountered
    question: str           # The question text
    options: List[str]      # A list of answer options
    answer_key: str         # The correct answer key (e.g., 'a', 'b', 'c', 'd')
    topic: str = ""         # Topic of the question (optional)
    description: str = ""   # Explanation for the answer (optional)
    question_number: str = ""  # Question number in the original exam (optional)

    @field_validator("year", mode="before")
    def convert_year_to_str_or_empty(cls, value):
        """
        If 'year' is None, return an empty string.
        Otherwise, force it to string.
        """
        if value is None:
            return ""
        return str(value)
        
    @field_validator("description", mode="before")
    def convert_description_to_str_or_empty(cls, value):
        if value is None:
            return ""
        return str(value)
        
    @field_validator("question_number", mode="before")
    def convert_number_to_str(cls, value):
        if value is None:
            return ""
        return str(value)
    
    @field_validator("topic", mode="before")
    def convert_topic(cls, value):
        if value is None:
            return ""
        return str(value)