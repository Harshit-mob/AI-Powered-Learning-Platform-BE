import uuid
from typing import List, Optional
from pydantic import BaseModel

# --- Curriculum / Study Center Response Schemas ---

class SubjectResponse(BaseModel):
    subject_id: str
    subject_name: str
    icon: str
    total_chapters: int

class TopicProgressDTO(BaseModel):
    id: str
    title: str
    learning_units_count: int
    is_completed: bool
    is_selected: bool

class ChapterProgressInfo(BaseModel):
    completed_topics: int
    total_topics: int
    mastery: int
    revision_unlocked: bool
    daily_completed: bool

class ChapterResponse(BaseModel):
    chapter_id: str
    title: str
    description: str
    estimated_duration: int
    progress: ChapterProgressInfo
    topics: List[TopicProgressDTO]

class CurriculumResponse(SubjectResponse):
    chapters: List[ChapterResponse]

# --- QBank Curation Pipeline Response Schemas ---

class QBankUploadResponse(BaseModel):
    qbank_id: str

class QBankItemResponse(BaseModel):
    qbank_id: str
    display_name: str
    subject_name: str
    chapter_title: str
    file_name: str
    source_type: str
    status: str
    total_questions: int
    error_message: Optional[str]
    created_at: str

class QBankQuestionDTO(BaseModel):
    draft_id: str
    learning_unit_id: str
    question_type: str
    concept: str
    text: str
    mcq_options: List[str]
    correct_option: Optional[str]
    expected_answer: Optional[str]
    acceptable_answers: List[str]
    difficulty: int
    bloom_level: str
    cognitive_level: str
    hint_level_1: str
    hint_level_2: str
    full_explanation: str
    source_pages: List[int]
    keywords: List[str]
    question_purpose: str
    status: str

class QBankTopicQuestionsResponse(BaseModel):
    topic_id: str
    topic_title: str
    questions: List[QBankQuestionDTO]


class CheckedInTopicResponse(BaseModel):
    id: str
    title: str


class CheckedInChapterResponse(BaseModel):
    chapter_id: str
    title: str
    topics: List[CheckedInTopicResponse]
