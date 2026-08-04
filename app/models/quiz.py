import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, Boolean, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.session import Base

class Question(Base):
    __tablename__ = "questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Moved FK from subtopics to learning_units
    learning_unit_id = Column(UUID(as_uuid=True), ForeignKey("learning_units.id"), nullable=True)
    
    question_type = Column(String, nullable=False, server_default='Concept')
    concept = Column(String, nullable=True)
    text = Column(Text, nullable=False)
    
    # MCQ Fallback
    mcq_options = Column(JSONB, nullable=True)
    correct_option = Column(String, nullable=True)
    
    # Answer formatting & evaluation
    answer_complexity = Column(String, nullable=False, server_default='WORD')
    evaluation_method = Column(String, nullable=True)

    # --- New Rich Assessment Assets ---
    learning_objective = Column(String, nullable=True)
    keywords = Column(JSONB, nullable=True)
    difficulty = Column(Integer, nullable=True)
    estimated_time = Column(Integer, nullable=True)
    hint_level_1 = Column(Text, nullable=True)
    hint_level_2 = Column(Text, nullable=True)
    full_explanation = Column(Text, nullable=True)
    source_pages = Column(JSONB, nullable=True)
    
    # Support for Voice, Text, MCQ
    supported_answer_modes = Column(ARRAY(String), nullable=True)
    expected_answer = Column(String, nullable=True)
    acceptable_answers = Column(JSONB, nullable=True)

    # --- Intelligence Engine Metadata ---
    question_hash = Column(String, nullable=True, unique=True)
    bloom_level = Column(String, nullable=True)
    cognitive_level = Column(String, nullable=True)
    intent = Column(String, nullable=True)
    voice_score = Column(Integer, nullable=True)
    speaking_time = Column(Float, nullable=True)
    thinking_time = Column(Float, nullable=True)
    cluster_id = Column(String, nullable=True)
    session_tags = Column(ARRAY(String), nullable=True)
    production_score = Column(Integer, nullable=True)
    coverage_weight = Column(Float, nullable=True)
    metadata_score = Column(Integer, nullable=True)
    normalized_concept = Column(String, nullable=True)
    cluster_name = Column(String, nullable=True)
    question_purpose = Column(String, nullable=True)
    progression_level = Column(Integer, nullable=True)
    prerequisite_concepts = Column(ARRAY(String), nullable=True)
    misconception_tags = Column(ARRAY(String), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship
    learning_unit = relationship("LearningUnit", back_populates="questions")
    
    question_bank_id = Column(UUID(as_uuid=True), ForeignKey("question_banks.id", ondelete="SET NULL"), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")
    
    question_bank = relationship("QuestionBank", back_populates="questions")


class QuestionBank(Base):
    __tablename__ = "question_banks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    chapter_id = Column(UUID(as_uuid=True), ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False)
    
    file_name = Column(String(255), nullable=False)
    source_type = Column(String(50), nullable=False) # 'TEXTBOOK_EXERCISE', 'STUDENT_NOTEBOOK'
    status = Column(String(50), nullable=False, default="PROCESSING", server_default="PROCESSING") # 'PROCESSING', 'PENDING_REVIEW', 'APPROVED', 'REJECTED', 'FAILED'
    total_questions = Column(Integer, nullable=False, default=0, server_default="0")
    error_message = Column(Text, nullable=True)
    
    created_at = Column(sa_DateTime(timezone=True) if 'sa_DateTime' in globals() else DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    questions = relationship("Question", back_populates="question_bank")
    draft_questions = relationship("DraftQuestion", back_populates="question_bank", cascade="all, delete-orphan")


class DraftQuestion(Base):
    __tablename__ = "draft_questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_bank_id = Column(UUID(as_uuid=True), ForeignKey("question_banks.id", ondelete="CASCADE"), nullable=False)
    learning_unit_id = Column(UUID(as_uuid=True), ForeignKey("learning_units.id", ondelete="CASCADE"), nullable=False)
    
    question_type = Column(String(50), nullable=False)
    concept = Column(String(255), nullable=False)
    text = Column(Text, nullable=False)
    mcq_options = Column(JSONB, nullable=False, default=list, server_default="[]")
    correct_option = Column(String(255), nullable=True)
    answer_complexity = Column(String(50), server_default="WORD")
    evaluation_method = Column(String(50), server_default="WORD_MATCH")
    expected_answer = Column(Text, nullable=True)
    acceptable_answers = Column(JSONB, nullable=False, default=list, server_default="[]")
    difficulty = Column(Integer, nullable=False, default=2, server_default="2")
    bloom_level = Column(String(50), nullable=True)
    cognitive_level = Column(String(50), nullable=True)
    hint_level_1 = Column(Text, nullable=True)
    hint_level_2 = Column(Text, nullable=True)
    full_explanation = Column(Text, nullable=True)
    source_pages = Column(JSONB, nullable=False, default=list, server_default="[]")
    keywords = Column(JSONB, nullable=False, default=list, server_default="[]")
    question_purpose = Column(String(50), nullable=False, default="Practice", server_default="Practice")
    progression_level = Column(Integer, nullable=False, default=3, server_default="3")
    status = Column(String(50), nullable=False, default="PENDING", server_default="PENDING") # 'PENDING', 'APPROVED', 'REJECTED'
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    question_bank = relationship("QuestionBank", back_populates="draft_questions")
    learning_unit = relationship("LearningUnit")



