from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class QuestionType(str, Enum):
    single = "single"
    multiple = "multiple"
    text = "text"


# ---------- Choices ----------
class ChoiceBase(BaseModel):
    text: str = Field(min_length=1, max_length=300)


class ChoiceCreate(ChoiceBase):
    is_correct: bool = False


class ChoiceRead(ChoiceBase):
    id: int


class ChoicePublic(ChoiceBase):
    pass  # в превью правильность не выдаем


# ---------- Questions ----------
class QuestionBase(BaseModel):
    text: str = Field(min_length=1, max_length=1000)
    type: QuestionType


class QuestionCreate(QuestionBase):
    quiz_id: int
    choices: Optional[List[ChoiceCreate]] = None


class QuestionUpdate(BaseModel):
    text: Optional[str] = Field(default=None, min_length=1, max_length=1000)
    type: Optional[QuestionType] = None
    choices: Optional[List[ChoiceCreate]] = None  # полная замена, если передано


class QuestionRead(QuestionBase):
    id: int
    choices: Optional[List[ChoiceRead]] = None


class QuestionPublic(QuestionBase):
    id: int
    choices: Optional[List[ChoicePublic]] = None


# ---------- Quizzes ----------
class QuizCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)


class QuizUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)


class QuizRead(BaseModel):
    id: int
    title: str


class QuizDetail(QuizRead):
    questions: List[QuestionRead] = []


class QuizPreview(QuizRead):
    questions: List[QuestionPublic] = []


# ---------- Passing (submit) ----------
class Answer(BaseModel):
    question_id: int
    choice_id: Optional[int] = None  # для single
    choice_ids: Optional[List[int]] = None  # для multiple
    text: Optional[str] = None  # для text


class SubmitRequest(BaseModel):
    answers: List[Answer]


class SubmitResult(BaseModel):
    score: int
    max_score: int


class ResultRead(BaseModel):
    id: int
    user_id: Optional[int] = None
    score: int
    max_score: int
    created_at: int  # epoch seconds
