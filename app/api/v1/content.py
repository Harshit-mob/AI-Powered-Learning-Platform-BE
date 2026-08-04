from fastapi import APIRouter, Depends, File, UploadFile, Form, BackgroundTasks
import uuid
import os
import shutil
from typing import List
from pydantic import BaseModel

from app.api.v1.responses import SuccessResponse, create_response
from app.application.content_service import ContentService
from app.api.v1.dependencies import get_uow, get_current_student
from app.repositories.base.unit_of_work import UnitOfWork
from app.models.quiz import QuestionBank, DraftQuestion, Question

router = APIRouter(prefix="/content", tags=["Content"])

# --- Request DTOs ---
class QBankReviewRequest(BaseModel):
    approved_ids: List[uuid.UUID]
    rejected_ids: List[uuid.UUID]

class QBankToggleActiveRequest(BaseModel):
    is_active: bool

@router.get("/subjects", response_model=SuccessResponse)
def get_subjects(student = Depends(get_current_student), uow: UnitOfWork = Depends(get_uow)):
    service = ContentService(uow)
    data = service.get_subjects(student.id)
    return create_response(data, "Subjects retrieved successfully")

@router.get("/chapters", response_model=SuccessResponse)
def get_chapters(subject_id: uuid.UUID, student = Depends(get_current_student), uow: UnitOfWork = Depends(get_uow)):
    service = ContentService(uow)
    data = service.get_chapters(student.id, subject_id)
    return create_response(data, "Chapters retrieved successfully")

@router.get("/curriculum", response_model=SuccessResponse)
def get_full_curriculum(student = Depends(get_current_student), uow: UnitOfWork = Depends(get_uow)):
    service = ContentService(uow)
    data = service.get_full_curriculum(student.id)
    return create_response(data, "Curriculum retrieved successfully")

# --- QBank Curation Pipeline APIs ---

@router.post("/curriculum/qbank/upload", response_model=SuccessResponse)
def upload_qbank_pdf(
    background_tasks: BackgroundTasks,
    subject_id: uuid.UUID = Form(...),
    chapter_id: uuid.UUID = Form(...),
    source_type: str = Form(...), # 'TEXTBOOK_EXERCISE', 'STUDENT_NOTEBOOK'
    file: UploadFile = File(...),
    student = Depends(get_current_student),
    uow: UnitOfWork = Depends(get_uow)
):
    # 1. Create a staging directories for temp files
    temp_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../temp_uploads"))
    os.makedirs(temp_dir, exist_ok=True)
    
    qbank_id = uuid.uuid4()
    file_path = os.path.join(temp_dir, f"{qbank_id}_{file.filename}")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # 2. Register QuestionBank record as PROCESSING
    with uow:
        qbank = QuestionBank(
            id=qbank_id,
            subject_id=subject_id,
            chapter_id=chapter_id,
            file_name=file.filename,
            source_type=source_type,
            status="PROCESSING",
            total_questions=0
        )
        uow.session.add(qbank)
        uow.commit()

    # 3. Trigger asynchronous background parsing and LLM generation
    from app.application.qbank_pipeline_service import QBankPipelineService
    pipeline_service = QBankPipelineService(uow)
    
    background_tasks.add_task(
        pipeline_service.process_qbank_pdf,
        qbank_id=qbank_id,
        file_path=file_path
    )
    
    return create_response(
        {"qbank_id": str(qbank_id)},
        "Question bank generation in progress."
    )

@router.get("/curriculum/qbank", response_model=SuccessResponse)
def get_qbanks_list(
    student = Depends(get_current_student),
    uow: UnitOfWork = Depends(get_uow)
):
    from app.models.course import Subject, Chapter
    with uow:
        rows = uow.session.query(
            QuestionBank.id,
            QuestionBank.file_name,
            QuestionBank.source_type,
            QuestionBank.status,
            QuestionBank.total_questions,
            QuestionBank.error_message,
            QuestionBank.created_at,
            Subject.name.label("subject_name"),
            Chapter.title.label("chapter_title")
        ).join(Subject, Subject.id == QuestionBank.subject_id) \
         .join(Chapter, Chapter.id == QuestionBank.chapter_id) \
         .order_by(QuestionBank.created_at.desc()).all()
         
        data = [
            {
                "qbank_id": str(r.id),
                "display_name": f"{r.subject_name}_{r.chapter_title}_{r.created_at.strftime('%Y%m%d_%H%M')}",
                "file_name": r.file_name,
                "source_type": r.source_type,
                "status": r.status,
                "total_questions": r.total_questions,
                "error_message": r.error_message,
                "created_at": r.created_at.isoformat()
            }
            for r in rows
        ]
        return create_response(data, "Question banks retrieved successfully")

@router.get("/curriculum/qbank/{qbank_id}/questions", response_model=SuccessResponse)
def get_qbank_draft_questions(
    qbank_id: uuid.UUID,
    student = Depends(get_current_student),
    uow: UnitOfWork = Depends(get_uow)
):
    with uow:
        # Check QBank status
        qbank = uow.session.query(QuestionBank).filter(QuestionBank.id == qbank_id).first()
        if not qbank:
            return create_response(None, "Question bank not found", status_code=404)
        if qbank.status == "PROCESSING":
            return create_response(None, "Question bank is still processing", status_code=400)
            
        drafts = uow.session.query(DraftQuestion).filter(DraftQuestion.question_bank_id == qbank_id).all()
        
        data = [
            {
                "draft_id": str(d.id),
                "learning_unit_id": str(d.learning_unit_id),
                "question_type": d.question_type,
                "concept": d.concept,
                "text": d.text,
                "mcq_options": d.mcq_options,
                "correct_option": d.correct_option,
                "expected_answer": d.expected_answer,
                "acceptable_answers": d.acceptable_answers,
                "difficulty": d.difficulty,
                "bloom_level": d.bloom_level,
                "cognitive_level": d.cognitive_level,
                "hint_level_1": d.hint_level_1,
                "hint_level_2": d.hint_level_2,
                "full_explanation": d.full_explanation,
                "source_pages": d.source_pages,
                "keywords": d.keywords,
                "question_purpose": d.question_purpose,
                "status": d.status
            }
            for d in drafts
        ]
        return create_response(data, "Draft questions retrieved successfully")

@router.post("/curriculum/qbank/{qbank_id}/review", response_model=SuccessResponse)
def review_qbank_draft_questions(
    qbank_id: uuid.UUID,
    payload: QBankReviewRequest,
    student = Depends(get_current_student),
    uow: UnitOfWork = Depends(get_uow)
):
    with uow:
        qbank = uow.session.query(QuestionBank).filter(QuestionBank.id == qbank_id).first()
        if not qbank:
            return create_response(None, "Question bank not found", status_code=404)
            
        # 1. Reject questions
        if payload.rejected_ids:
            uow.session.query(DraftQuestion).filter(
                DraftQuestion.id.in_(payload.rejected_ids),
                DraftQuestion.question_bank_id == qbank_id
            ).update({"status": "REJECTED"}, synchronize_session=False)
            
        # 2. Approve questions & Transfer to main questions table
        if payload.approved_ids:
            approved_drafts = uow.session.query(DraftQuestion).filter(
                DraftQuestion.id.in_(payload.approved_ids),
                DraftQuestion.question_bank_id == qbank_id
            ).all()
            
            for d in approved_drafts:
                d.status = "APPROVED"
                
                # Check duplicate
                import hashlib
                qhash = hashlib.sha256(d.text.strip().lower().encode()).hexdigest()
                
                existing = uow.session.query(Question).filter(Question.question_hash == qhash).first()
                if existing:
                    # Update existing
                    existing.is_active = True
                    existing.question_bank_id = qbank_id
                    existing.learning_unit_id = d.learning_unit_id
                    existing.question_type = d.question_type
                    existing.concept = d.concept
                    existing.text = d.text
                    existing.mcq_options = d.mcq_options
                    existing.correct_option = d.correct_option
                    existing.answer_complexity = d.answer_complexity
                    existing.evaluation_method = d.evaluation_method
                    existing.expected_answer = d.expected_answer
                    existing.acceptable_answers = d.acceptable_answers
                    existing.difficulty = d.difficulty
                    existing.bloom_level = d.bloom_level
                    existing.cognitive_level = d.cognitive_level
                    existing.hint_level_1 = d.hint_level_1
                    existing.hint_level_2 = d.hint_level_2
                    existing.full_explanation = d.full_explanation
                    existing.source_pages = d.source_pages
                    existing.keywords = d.keywords
                    existing.question_purpose = d.question_purpose
                    existing.progression_level = d.progression_level
                else:
                    # Insert new
                    new_q = Question(
                        id=d.id, # Keep same ID or let it generate
                        question_bank_id=qbank_id,
                        learning_unit_id=d.learning_unit_id,
                        question_type=d.question_type,
                        concept=d.concept,
                        text=d.text,
                        mcq_options=d.mcq_options,
                        correct_option=d.correct_option,
                        answer_complexity=d.answer_complexity,
                        evaluation_method=d.evaluation_method,
                        expected_answer=d.expected_answer,
                        acceptable_answers=d.acceptable_answers,
                        difficulty=d.difficulty,
                        bloom_level=d.bloom_level,
                        cognitive_level=d.cognitive_level,
                        hint_level_1=d.hint_level_1,
                        hint_level_2=d.hint_level_2,
                        full_explanation=d.full_explanation,
                        source_pages=d.source_pages,
                        keywords=d.keywords,
                        question_purpose=d.question_purpose,
                        progression_level=d.progression_level,
                        question_hash=qhash,
                        is_active=True
                    )
                    uow.session.add(new_q)
                    
        # Update overall QBank status to APPROVED
        qbank.status = "APPROVED"
        uow.commit()
        return create_response(None, "Draft questions reviewed and applied successfully")

@router.post("/curriculum/qbank/{qbank_id}/toggle-active", response_model=SuccessResponse)
def toggle_qbank_active_status(
    qbank_id: uuid.UUID,
    payload: QBankToggleActiveRequest,
    student = Depends(get_current_student),
    uow: UnitOfWork = Depends(get_uow)
):
    with uow:
        qbank = uow.session.query(QuestionBank).filter(QuestionBank.id == qbank_id).first()
        if not qbank:
            return create_response(None, "Question bank not found", status_code=404)
            
        uow.session.query(Question).filter(
            Question.question_bank_id == qbank_id
        ).update({"is_active": payload.is_active}, synchronize_session=False)
        
        uow.commit()
        status_str = "activated" if payload.is_active else "deactivated"
        return create_response(None, f"All questions in this question bank have been {status_str}")

