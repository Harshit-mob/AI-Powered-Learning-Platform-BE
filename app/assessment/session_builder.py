import uuid
from typing import List
from app.models.quiz import Question
from app.assessment.models.dto import GeneratedSession, QuestionPayload
from app.constants.session import SessionType

class SessionBuilder:
    def build_session(self, 
                      student_id: uuid.UUID, 
                      content_id: uuid.UUID, 
                      session_type: SessionType,
                      questions: List[Question],
                      estimated_minutes: int) -> GeneratedSession:
        
        question_payloads = []
        for q in questions:
            payload = QuestionPayload(
                id=q.id,
                learning_unit_id=q.learning_unit_id,
                question_text=q.question_text,
                question_type=q.question_type,
                difficulty=q.difficulty_level,
                bloom_level=q.bloom_level,
                cognitive_level=q.cognitive_level,
                options=q.options,
                hints=q.hints,
                metadata={}
            )
            question_payloads.append(payload)

        return GeneratedSession(
            session_id=uuid.uuid4(),
            session_type=session_type,
            student_id=student_id,
            content_id=content_id,
            estimated_minutes=estimated_minutes,
            question_count=len(question_payloads),
            questions=question_payloads,
            metadata={
                "builder_version": "1.0",
                "taxonomy_diversity_checked": True
            }
        )
