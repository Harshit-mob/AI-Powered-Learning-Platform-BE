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



