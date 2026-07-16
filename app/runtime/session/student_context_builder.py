import uuid
from typing import List
from sqlalchemy import select

from app.repositories.base.unit_of_work import UnitOfWork
from app.runtime.session.models.student_context import StudentContext
from app.models.learning.student_mastery import StudentMastery
from app.models.assessment.student_response import StudentResponse

class StudentContextBuilder:
    """
    Builds the StudentContext using exactly 2 database queries:
    1. Fetching all StudentMastery records for the student.
    2. Fetching recent StudentResponse records for the student.
    """
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def build(self, student_id: uuid.UUID) -> StudentContext:
        context = StudentContext(student_id=student_id)
        
        with self.uow:
            # Query 1: Fetch all mastery records (assuming batch fetch per student is small enough for MVP)
            # In a true scalable environment, we'd filter by the LUs loaded by CandidateLoader.
            mastery_stmt = select(StudentMastery).where(StudentMastery.student_id == student_id)
            mastery_records = self.uow.session.execute(mastery_stmt).scalars().all()
            
            for m in mastery_records:
                # We map concept_id as learning_unit_id for now as per schema
                lu_id = m.concept_id 
                context.mastery_by_lu[lu_id] = float(m.mastery_percentage)
                context.confidence_by_lu[lu_id] = float(m.confidence_score)
                context.status_by_lu[lu_id] = m.status

            # Query 2: Fetch recent responses to track attempt counts and correctness
            # We limit to the last 1000 responses to keep it fast
            response_stmt = (
                select(StudentResponse)
                .join(StudentResponse.session)
                .where(StudentResponse.session.has(student_id=student_id))
                .order_by(StudentResponse.created_at.desc())
                .limit(1000)
            )
            response_records = self.uow.session.execute(response_stmt).scalars().all()
            
            for r in response_records:
                q_id = r.question_id
                # Track attempts
                context.question_attempts[q_id] = context.question_attempts.get(q_id, 0) + 1
                
                # Track if ever correctly answered
                if r.is_correct:
                    context.correct_questions[q_id] = True
                    
                # Track recent incorrect by LU (assuming we have LU info, wait - we need LU on response or we map from question)
                # For Phase 1, we will just track question correctness. The QuestionVariantSelector handles the rest.

        return context
