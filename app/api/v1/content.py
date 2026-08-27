from fastapi import APIRouter, Depends, File, UploadFile, Form, BackgroundTasks
import uuid
import os
import shutil
from typing import List, Optional
from pydantic import BaseModel

from app.api.v1.responses import SuccessResponse, GenericSuccessResponse, create_response
from app.schemas.content_schema import (
    SubjectResponse,
    ChapterResponse,
    CurriculumResponse,
    QBankUploadResponse,
    QBankItemResponse,
    QBankTopicQuestionsResponse
)
from app.application.content_service import ContentService
from app.api.v1.dependencies import get_uow, get_current_student, get_current_admin
from app.repositories.base.unit_of_work import UnitOfWork
from app.models.quiz import QuestionBank, DraftQuestion, Question
from app.models.course import Topic, Subtopic, LearningUnit, Chapter

router = APIRouter(prefix="/content", tags=["Content"])

# --- Request DTOs ---
class QBankReviewRequest(BaseModel):
    approved_ids: List[uuid.UUID]
    rejected_ids: List[uuid.UUID]

class QBankToggleActiveRequest(BaseModel):
    is_active: bool

class DraftQuestionUpdateRequest(BaseModel):
    text: Optional[str] = None
    mcq_options: Optional[List[str]] = None
    correct_option: Optional[str] = None
    expected_answer: Optional[str] = None
    acceptable_answers: Optional[List[str]] = None
    hint_level_1: Optional[str] = None
    hint_level_2: Optional[str] = None
    full_explanation: Optional[str] = None

class TopicCreateRequest(BaseModel):
    title: str
    chapter_id: uuid.UUID

class QuestionCreateRequest(BaseModel):
    topic_id: uuid.UUID
    text: str
    mcq_options: List[str] = []
    correct_option: Optional[str] = None
    expected_answer: Optional[str] = None
    acceptable_answers: List[str] = []
    hint_level_1: Optional[str] = None
    hint_level_2: Optional[str] = None
    full_explanation: Optional[str] = None
    difficulty: int = 2



@router.get("/subjects", response_model=GenericSuccessResponse[List[SubjectResponse]])
def get_subjects(student = Depends(get_current_student), uow: UnitOfWork = Depends(get_uow)):
    service = ContentService(uow)
    data = service.get_subjects(student.id)
    return create_response(data, "Subjects retrieved successfully")

@router.get("/chapters", response_model=GenericSuccessResponse[List[ChapterResponse]])
def get_chapters(subject_id: uuid.UUID, student = Depends(get_current_student), uow: UnitOfWork = Depends(get_uow)):
    service = ContentService(uow)
    data = service.get_chapters(student.id, subject_id)
    return create_response(data, "Chapters retrieved successfully")

@router.get("/curriculum", response_model=GenericSuccessResponse[List[CurriculumResponse]])
def get_full_curriculum(student = Depends(get_current_student), uow: UnitOfWork = Depends(get_uow)):
    service = ContentService(uow)
    data = service.get_full_curriculum(student.id)
    return create_response(data, "Curriculum retrieved successfully")

# --- QBank Curation Pipeline APIs ---

@router.post("/curriculum/qbank/upload", response_model=GenericSuccessResponse[QBankUploadResponse])
def upload_qbank_pdf(
    background_tasks: BackgroundTasks,
    board_id: uuid.UUID = Form(...),
    grade_id: uuid.UUID = Form(...),
    subject_id: uuid.UUID = Form(...),
    chapter_name: str = Form(...),
    file: UploadFile = File(...),
    admin = Depends(get_current_admin),
    uow: UnitOfWork = Depends(get_uow)
):
    # 1. Create a staging directory for temp files
    temp_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../temp_uploads"))
    os.makedirs(temp_dir, exist_ok=True)
    
    qbank_id = uuid.uuid4()
    file_path = os.path.join(temp_dir, f"{qbank_id}_{file.filename}")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # 2. Dynamically Resolve or Create Subject & Chapter
    from app.models.course import Board, Grade, Subject, Chapter
    from app.api.v1.errors import error_response
    with uow:
        # Resolve Board, Grade, and Subject
        board = uow.session.query(Board).filter(Board.id == board_id).first()
        grade = uow.session.query(Grade).filter(Grade.id == grade_id).first()
        subject = uow.session.query(Subject).filter(Subject.id == subject_id).first()
        
        if not board:
            return error_response("NOT_FOUND", f"Board with ID {board_id} not found.", status_code=404)
        if not grade:
            return error_response("NOT_FOUND", f"Grade with ID {grade_id} not found.", status_code=404)
        if not subject:
            return error_response("NOT_FOUND", f"Subject with ID {subject_id} not found.", status_code=404)
            
        # Verify consistent scoping
        if grade.board_id != board_id:
            return error_response("BAD_REQUEST", f"Grade {grade.name} does not belong to Board {board.name}.", status_code=400)
        if subject.grade_id != grade_id:
            return error_response("BAD_REQUEST", f"Subject {subject.name} does not belong to Grade {grade.name}.", status_code=400)
            
        # Find or create Chapter
        chap_norm = chapter_name.strip()
        chapter = uow.session.query(Chapter).filter(
            Chapter.title == chap_norm,
            Chapter.subject_id == subject.id
        ).first()
        if not chapter:
            chapter = Chapter(title=chap_norm, subject_id=subject.id)
            uow.session.add(chapter)
            uow.session.flush()
            
        # 3. Register QuestionBank record as PROCESSING
        qbank = QuestionBank(
            id=qbank_id,
            subject_id=subject.id,
            chapter_id=chapter.id,
            file_name=file.filename,
            source_type="TEXTBOOK_EXERCISE",
            status="PROCESSING",
            total_questions=0
        )
        uow.session.add(qbank)
        uow.commit()

    # 4. Trigger asynchronous background parsing and LLM generation
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

@router.get("/curriculum/qbank", response_model=GenericSuccessResponse[List[QBankItemResponse]])
def get_qbanks_list(
    admin = Depends(get_current_admin),
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
                "subject_name": r.subject_name,
                "chapter_title": r.chapter_title,
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

@router.get("/curriculum/qbank/{qbank_id}/questions")
def get_qbank_draft_questions(
    qbank_id: uuid.UUID,
    admin = Depends(get_current_admin),
    uow: UnitOfWork = Depends(get_uow)
):
    with uow:
        # Check QBank status
        qbank = uow.session.query(QuestionBank).filter(QuestionBank.id == qbank_id).first()
        if not qbank:
            from app.api.v1.errors import error_response
            return error_response("NOT_FOUND", "Question bank not found", status_code=404)
        if qbank.status == "PROCESSING":
            from app.api.v1.errors import error_response
            return error_response("PROCESSING", "Question bank is still processing", status_code=400)
            
        from app.models.course import Topic, Subtopic, LearningUnit, Subject, Chapter
        from collections import OrderedDict
        
        # We will build a structured hierarchy of the questions grouped by Topic -> Subtopic -> Learning Unit
        hierarchy = OrderedDict()
        
        draft_count = uow.session.query(DraftQuestion).filter(DraftQuestion.question_bank_id == qbank_id).count()
        
        if draft_count > 0:
            # Fetch from draft_questions table with curriculum contexts
            rows = uow.session.query(
                DraftQuestion,
                Topic.id.label("topic_id"),
                Topic.title.label("topic_title")
            ).join(LearningUnit, LearningUnit.id == DraftQuestion.learning_unit_id) \
             .join(Subtopic, Subtopic.id == LearningUnit.subtopic_id) \
             .join(Topic, Topic.id == Subtopic.topic_id) \
             .filter(DraftQuestion.question_bank_id == qbank_id) \
             .order_by(Topic.created_at, DraftQuestion.created_at).all()
             
            for row in rows:
                d = row.DraftQuestion
                q_dict = {
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
                
                t_id = str(row.topic_id)
                if t_id not in hierarchy:
                    hierarchy[t_id] = {
                        "topic_id": t_id,
                        "topic_title": row.topic_title,
                        "questions": []
                    }
                hierarchy[t_id]["questions"].append(q_dict)
        else:
            # Fetch from main questions table with curriculum contexts
            rows = uow.session.query(
                Question,
                Topic.id.label("topic_id"),
                Topic.title.label("topic_title")
            ).join(LearningUnit, LearningUnit.id == Question.learning_unit_id) \
             .join(Subtopic, Subtopic.id == LearningUnit.subtopic_id) \
             .join(Topic, Topic.id == Subtopic.topic_id) \
             .filter(Question.question_bank_id == qbank_id) \
             .order_by(Topic.created_at, Question.created_at).all()
             
            for row in rows:
                q = row.Question
                q_dict = {
                    "draft_id": str(q.id),
                    "learning_unit_id": str(q.learning_unit_id),
                    "question_type": q.question_type,
                    "concept": q.concept,
                    "text": q.text,
                    "mcq_options": q.mcq_options or [],
                    "correct_option": q.correct_option or "",
                    "expected_answer": q.expected_answer or "",
                    "acceptable_answers": q.acceptable_answers or [],
                    "difficulty": q.difficulty or 2,
                    "bloom_level": q.bloom_level or "",
                    "cognitive_level": q.cognitive_level or "",
                    "hint_level_1": q.hint_level_1 or "",
                    "hint_level_2": q.hint_level_2 or "",
                    "full_explanation": q.full_explanation or "",
                    "source_pages": q.source_pages or [],
                    "keywords": q.keywords or [],
                    "question_purpose": q.question_purpose or "Practice",
                    "status": "APPROVED" if q.is_active else "REJECTED"
                }
                
                t_id = str(row.topic_id)
                if t_id not in hierarchy:
                    hierarchy[t_id] = {
                        "topic_id": t_id,
                        "topic_title": row.topic_title,
                        "questions": []
                    }
                hierarchy[t_id]["questions"].append(q_dict)
                
        # Fetch subject & chapter names
        subject = uow.session.query(Subject).filter(Subject.id == qbank.subject_id).first()
        chapter = uow.session.query(Chapter).filter(Chapter.id == qbank.chapter_id).first()
        
        total_questions = sum(len(t["questions"]) for t in hierarchy.values())
        
        result_data = {
            "subject_name": subject.name if subject else None,
            "chapter_title": chapter.title if chapter else None,
            "total_questions": total_questions,
            "status": qbank.status,
            "topics": list(hierarchy.values())
        }
        return create_response(result_data, "Questions retrieved and grouped topic-wise successfully")

@router.put("/curriculum/qbank/draft-questions/{question_id}", response_model=SuccessResponse)
def update_draft_question(
    question_id: uuid.UUID,
    payload: DraftQuestionUpdateRequest,
    admin = Depends(get_current_admin),
    uow: UnitOfWork = Depends(get_uow)
):
    """Update details of a generated draft question before approval."""
    with uow:
        draft_q = uow.session.query(DraftQuestion).filter(DraftQuestion.id == question_id).first()
        if not draft_q:
            from app.api.v1.errors import error_response
            return error_response("NOT_FOUND", "Draft question not found", status_code=404)
            
        # Check if QBank is active
        qbank = uow.session.query(QuestionBank).filter(QuestionBank.id == draft_q.question_bank_id).first()
        if qbank and qbank.status == "APPROVED":
            from app.api.v1.errors import error_response
            return error_response("BAD_REQUEST", "Cannot edit questions in an active question bank. Please deactivate it first.", status_code=400)
            
        # Update fields if provided
        if payload.text is not None:
            draft_q.text = payload.text
            
        if payload.mcq_options is not None:
            draft_q.mcq_options = payload.mcq_options
            
        if payload.correct_option is not None:
            draft_q.correct_option = payload.correct_option
            
        if payload.expected_answer is not None:
            draft_q.expected_answer = payload.expected_answer
            
        if payload.acceptable_answers is not None:
            draft_q.acceptable_answers = payload.acceptable_answers
            
        if payload.hint_level_1 is not None:
            draft_q.hint_level_1 = payload.hint_level_1
            
        if payload.hint_level_2 is not None:
            draft_q.hint_level_2 = payload.hint_level_2
            
        if payload.full_explanation is not None:
            draft_q.full_explanation = payload.full_explanation
            
        # Dynamically determine the question type and validation based on mcq_options
        if draft_q.mcq_options and len(draft_q.mcq_options) > 0:
            if len(draft_q.mcq_options) == 4:
                draft_q.question_type = "MCQ"
                draft_q.evaluation_method = "MCQ"
                draft_q.answer_complexity = "MCQ"
                
                if not draft_q.correct_option:
                    from app.api.v1.errors import error_response
                    return error_response("BAD_REQUEST", "correct_option is required for MCQ question type.", status_code=400)
                if draft_q.correct_option not in draft_q.mcq_options:
                    from app.api.v1.errors import error_response
                    return error_response("BAD_REQUEST", "correct_option must match one of the mcq_options exactly.", status_code=400)
                if draft_q.expected_answer != draft_q.correct_option:
                    from app.api.v1.errors import error_response
                    return error_response("BAD_REQUEST", "expected_answer must be identical to correct_option for MCQs.", status_code=400)
                    
            elif len(draft_q.mcq_options) == 2:
                draft_q.question_type = "TRUE_FALSE"
                draft_q.evaluation_method = "MCQ"
                draft_q.answer_complexity = "MCQ"
                
                if not draft_q.correct_option:
                    from app.api.v1.errors import error_response
                    return error_response("BAD_REQUEST", "correct_option is required for TRUE_FALSE question type.", status_code=400)
                if draft_q.correct_option not in draft_q.mcq_options:
                    from app.api.v1.errors import error_response
                    return error_response("BAD_REQUEST", "correct_option must match one of the TRUE_FALSE options exactly.", status_code=400)
                if draft_q.expected_answer != draft_q.correct_option:
                    from app.api.v1.errors import error_response
                    return error_response("BAD_REQUEST", "expected_answer must be identical to correct_option for True/False questions.", status_code=400)
            else:
                from app.api.v1.errors import error_response
                return error_response("BAD_REQUEST", "mcq_options must contain exactly 4 options (for MCQ) or exactly 2 options (for True/False).", status_code=400)
        else:
            if draft_q.question_type in ("MCQ", "TRUE_FALSE"):
                draft_q.question_type = "UNDERSTANDING"
            
            draft_q.mcq_options = []
            draft_q.correct_option = None
            
            if draft_q.question_type == "FILL_BLANK":
                draft_q.evaluation_method = "WORD_MATCH"
                draft_q.answer_complexity = "WORD"
            elif draft_q.question_type in ("RECALL", "DEFINITION"):
                draft_q.evaluation_method = "WORD_MATCH"
                draft_q.answer_complexity = "WORD"
            else:
                draft_q.evaluation_method = "SEMANTIC"
                draft_q.answer_complexity = "SENTENCE"
                
        uow.commit()
        return create_response(None, "Draft question updated successfully")

@router.post("/curriculum/qbank/{qbank_id}/review", response_model=SuccessResponse)
def review_qbank_draft_questions(
    qbank_id: uuid.UUID,
    payload: QBankReviewRequest,
    admin = Depends(get_current_admin),
    uow: UnitOfWork = Depends(get_uow)
):
    with uow:
        qbank = uow.session.query(QuestionBank).filter(QuestionBank.id == qbank_id).first()
        if not qbank:
            from app.api.v1.errors import error_response
            return error_response("NOT_FOUND", "Question bank not found", status_code=404)
            
        if qbank.status == "APPROVED":
            from app.api.v1.errors import error_response
            return error_response("BAD_REQUEST", "Cannot review questions in an active question bank. Please deactivate it first.", status_code=400)
            
        # 1. Reject questions
        if payload.rejected_ids:
            uow.session.query(DraftQuestion).filter(
                DraftQuestion.id.in_(payload.rejected_ids),
                DraftQuestion.question_bank_id == qbank_id
            ).update({"status": "REJECTED"}, synchronize_session=False)
            
        # 2. Approve questions (simply update draft status)
        if payload.approved_ids:
            uow.session.query(DraftQuestion).filter(
                DraftQuestion.id.in_(payload.approved_ids),
                DraftQuestion.question_bank_id == qbank_id
            ).update({"status": "APPROVED"}, synchronize_session=False)
            
        uow.commit()
        return create_response(None, "Draft questions reviewed and applied successfully")

@router.post("/curriculum/qbank/{qbank_id}/toggle-active", response_model=SuccessResponse)
def toggle_qbank_active_status(
    qbank_id: uuid.UUID,
    payload: QBankToggleActiveRequest,
    admin = Depends(get_current_admin),
    uow: UnitOfWork = Depends(get_uow)
):
    with uow:
        qbank = uow.session.query(QuestionBank).filter(QuestionBank.id == qbank_id).first()
        if not qbank:
            from app.api.v1.errors import error_response
            return error_response("NOT_FOUND", "Question bank not found", status_code=404)
            
        if payload.is_active:
            # Check number of approved questions
            approved_count = uow.session.query(DraftQuestion).filter(
                DraftQuestion.question_bank_id == qbank_id,
                DraftQuestion.status == "APPROVED"
            ).count()
            
            if approved_count < 10:
                from app.api.v1.errors import error_response
                return error_response(
                    "INSUFFICIENT_APPROVED_QUESTIONS",
                    f"Cannot publish. The question bank must have at least 10 approved questions. (Currently approved: {approved_count})",
                    status_code=400
                )
                
            # Copy/Update approved draft questions to main questions table
            approved_drafts = uow.session.query(DraftQuestion).filter(
                DraftQuestion.question_bank_id == qbank_id,
                DraftQuestion.status == "APPROVED"
            ).all()
            
            active_ids = []
            for d in approved_drafts:
                active_ids.append(d.id)
                
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
                    existing.supported_answer_modes = (
                        ["MCQ"] if d.question_type in ("MCQ", "TRUE_FALSE")
                        else ["TEXT"] if d.question_type == "FILL_BLANK"
                        else ["VOICE", "TEXT"]
                    )
                    existing.source_type = getattr(d, "source_type", "AI_GENERATED")
                else:
                    # Insert new
                    new_q = Question(
                        id=d.id,
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
                        supported_answer_modes=(
                            ["MCQ"] if d.question_type in ("MCQ", "TRUE_FALSE")
                            else ["TEXT"] if d.question_type == "FILL_BLANK"
                            else ["VOICE", "TEXT"]
                        ),
                        question_hash=qhash,
                        source_type=getattr(d, "source_type", "AI_GENERATED"),
                        is_active=True
                    )
                    uow.session.add(new_q)
            
            # Deactivate any questions in main table for this qbank that are not approved anymore
            uow.session.query(Question).filter(
                Question.question_bank_id == qbank_id,
                Question.id.not_in(active_ids)
            ).update({"is_active": False}, synchronize_session=False)
            
            qbank.status = "APPROVED"
        else:
            uow.session.query(Question).filter(
                Question.question_bank_id == qbank_id
            ).update({"is_active": False}, synchronize_session=False)
            
            qbank.status = "PENDING_REVIEW"
            
        uow.commit()
        status_str = "activated" if payload.is_active else "deactivated"
        return create_response(None, f"All questions in this question bank have been {status_str}")

@router.delete("/curriculum/qbank/{qbank_id}", response_model=SuccessResponse)
def delete_qbank(
    qbank_id: uuid.UUID,
    admin = Depends(get_current_admin),
    uow: UnitOfWork = Depends(get_uow)
):
    from app.api.v1.errors import error_response
    with uow:
        qbank = uow.session.query(QuestionBank).filter(QuestionBank.id == qbank_id).first()
        if not qbank:
            return error_response("NOT_FOUND", f"Question bank with ID {qbank_id} not found.", status_code=404)
        
        uow.session.delete(qbank)
        uow.commit()
        
    return create_response(None, "Question bank removed successfully.")


@router.post("/curriculum/topics", response_model=SuccessResponse)
def create_topic_manually(
    payload: TopicCreateRequest,
    admin = Depends(get_current_admin),
    uow: UnitOfWork = Depends(get_uow)
):
    """Manually add a Topic. Automatically creates standard Subtopic and Learning Unit under the hood."""
    from app.api.v1.errors import error_response
    with uow:
        # Verify Chapter exists
        chapter = uow.session.query(Chapter).filter(Chapter.id == payload.chapter_id).first()
        if not chapter:
            return error_response("NOT_FOUND", "Chapter not found", status_code=404)
            
        # Create Topic
        topic = Topic(title=payload.title, chapter_id=payload.chapter_id)
        uow.session.add(topic)
        uow.session.flush() # get topic ID
        
        # Auto-create Subtopic
        subtopic = Subtopic(
            title=f"{payload.title} - Core Content",
            content=f"Core subtopic for {payload.title}",
            topic_id=topic.id
        )
        uow.session.add(subtopic)
        uow.session.flush() # get subtopic ID
        
        # Auto-create LearningUnit
        lu = LearningUnit(
            subtopic_id=subtopic.id,
            title=f"{payload.title} - Focus Unit",
            content=f"Focus learning unit for {payload.title}",
            learning_objective=f"Master the concepts of {payload.title}",
            summary=f"Summary of master concepts for {payload.title}"
        )
        uow.session.add(lu)
        uow.commit()
        
        return create_response({"topic_id": topic.id}, "Topic and default structures created successfully")


def calculate_estimated_time(text: str, expected_answer: str, question_type: str, complexity: str, difficulty: int) -> int:
    # 1. Speaking time
    comp_time = 2.0
    if complexity == "SHORT_PHRASE": comp_time = 4.0
    elif complexity == "PHRASE": comp_time = 6.0
    elif complexity == "SENTENCE": comp_time = 10.0
    elif complexity == "PARAGRAPH": comp_time = 15.0
        
    len_time = len(expected_answer) / 10.0
    
    type_bonus = 0.0
    if question_type in ("MCQ", "TRUE_FALSE"):
        type_bonus = 2.0
        
    speaking_time = (comp_time + len_time) / 2.0 + type_bonus
    speaking_time = min(15.0, max(2.0, speaking_time))

    # 2. Thinking time
    q_words = len(text.strip().split())
    ans_words = len(expected_answer.strip().split())
    reading_time = (q_words + ans_words) / 3.3
    
    base_time = 5.0 # default to UNDERSTAND level cognitive time
    diff_bonus = float(difficulty) * 1.5
    
    thinking_time = reading_time + base_time + diff_bonus
    thinking_time = min(45.0, max(2.0, thinking_time))

    # 3. Buffer
    buffer_map = {1: 1, 2: 2, 3: 2, 4: 3, 5: 3}
    buffer = buffer_map.get(difficulty, 2)
    
    total_time = speaking_time + thinking_time + buffer
    return int(round(total_time))


@router.post("/curriculum/questions", response_model=SuccessResponse)
def create_question_manually(
    payload: QuestionCreateRequest,
    admin = Depends(get_current_admin),
    uow: UnitOfWork = Depends(get_uow)
):
    """Manually add a Question. Dynamically maps it to a dedicated manual Learning Unit."""
    from app.api.v1.errors import error_response
    with uow:
        # Verify Topic exists
        topic = uow.session.query(Topic).filter(Topic.id == payload.topic_id).first()
        if not topic:
            return error_response("NOT_FOUND", "Topic not found", status_code=404)
            
        # Try to find an existing manual additions subtopic/learning unit
        manual_sub = uow.session.query(Subtopic).filter(
            Subtopic.topic_id == payload.topic_id,
            Subtopic.title == f"{topic.title} - Manual Additions"
        ).first()
        
        if not manual_sub:
            # Create the manual additions subtopic
            manual_sub = Subtopic(
                title=f"{topic.title} - Manual Additions",
                content=f"Dedicated subtopic for manually added questions in {topic.title}",
                topic_id=topic.id
            )
            uow.session.add(manual_sub)
            uow.session.flush()
            
        manual_lu = uow.session.query(LearningUnit).filter(
            LearningUnit.subtopic_id == manual_sub.id,
            LearningUnit.title == f"{topic.title} - Manual Additions"
        ).first()
        
        if not manual_lu:
            # Create the manual additions learning unit
            manual_lu = LearningUnit(
                subtopic_id=manual_sub.id,
                title=f"{topic.title} - Manual Additions",
                content=f"Dedicated learning unit for manually added questions in {topic.title}",
                learning_objective=f"Evaluate manually supplemented topics for {topic.title}",
                summary=f"Summary of manually added questions in {topic.title}"
            )
            uow.session.add(manual_lu)
            uow.session.flush()
            
        # Determine the question type dynamically based on options length
        q_type = "UNDERSTANDING"
        eval_method = "SEMANTIC"
        complexity = "SENTENCE"
        modes = ["VOICE", "TEXT"]
        
        if payload.mcq_options and len(payload.mcq_options) > 0:
            if len(payload.mcq_options) == 4:
                q_type = "MCQ"
                eval_method = "MCQ"
                complexity = "MCQ"
                modes = ["MCQ"]
                
                # MCQ Validations
                if not payload.correct_option:
                    return error_response("BAD_REQUEST", "correct_option is required for MCQ question type.", status_code=400)
                if payload.correct_option not in payload.mcq_options:
                    return error_response("BAD_REQUEST", "correct_option must match one of the mcq_options exactly.", status_code=400)
                if payload.expected_answer != payload.correct_option:
                    return error_response("BAD_REQUEST", "expected_answer must be identical to correct_option for MCQs.", status_code=400)
            elif len(payload.mcq_options) == 2:
                q_type = "TRUE_FALSE"
                eval_method = "MCQ"
                complexity = "MCQ"
                modes = ["MCQ"]
                
                # TF Validations
                if not payload.correct_option:
                    return error_response("BAD_REQUEST", "correct_option is required for TRUE_FALSE question type.", status_code=400)
                if payload.correct_option not in payload.mcq_options:
                    return error_response("BAD_REQUEST", "correct_option must match one of the TRUE_FALSE options exactly.", status_code=400)
                if payload.expected_answer != payload.correct_option:
                    return error_response("BAD_REQUEST", "expected_answer must be identical to correct_option for True/False questions.", status_code=400)
            else:
                return error_response("BAD_REQUEST", "mcq_options must contain exactly 4 options (for MCQ) or exactly 2 options (for True/False).", status_code=400)
                
        # Generate question hash
        import hashlib
        qhash = hashlib.sha256(payload.text.strip().lower().encode()).hexdigest()
        
        # Check duplicate
        existing_active = uow.session.query(Question).filter(Question.question_hash == qhash).first()
        existing_draft = uow.session.query(DraftQuestion).filter(DraftQuestion.text == payload.text).first()
        if existing_active or existing_draft:
            return error_response("BAD_REQUEST", "A question with identical content already exists.", status_code=400)
            
        # Find the QBank associated with this Chapter
        qbank = uow.session.query(QuestionBank).filter(QuestionBank.chapter_id == topic.chapter_id).first()
        if qbank and qbank.status == "APPROVED":
            return error_response("BAD_REQUEST", "Cannot add manual questions to an active question bank. Please deactivate it first.", status_code=400)
            
        q_id = uuid.uuid4()
        
        # Calculate estimated answering time dynamically
        est_time = calculate_estimated_time(
            text=payload.text,
            expected_answer=payload.expected_answer or "",
            question_type=q_type,
            complexity=complexity,
            difficulty=payload.difficulty
        )
        
        # 1. Create the DraftQuestion record if QBank exists, so it shows up in curation lists
        if qbank:
            new_draft = DraftQuestion(
                id=q_id,
                question_bank_id=qbank.id,
                learning_unit_id=manual_lu.id,
                question_type=q_type,
                concept="Manual Supplementary",
                text=payload.text,
                mcq_options=payload.mcq_options,
                correct_option=payload.correct_option,
                answer_complexity=complexity,
                evaluation_method=eval_method,
                expected_answer=payload.expected_answer,
                acceptable_answers=payload.acceptable_answers,
                difficulty=payload.difficulty,
                hint_level_1=payload.hint_level_1,
                hint_level_2=payload.hint_level_2,
                full_explanation=payload.full_explanation,
                source_type="MANUAL",
                status="APPROVED",  # default to APPROVED so it's ready to promote
                question_purpose="Practice",
                progression_level=3,
                bloom_level="COMPREHENSION",
                cognitive_level="UNDERSTAND",
                source_pages=[],
                keywords=[]
            )
            uow.session.add(new_draft)

        # 2. If no QBank exists (e.g. manually created topic), insert directly into active Question pool
        else:
            new_q = Question(
                id=q_id,
                learning_unit_id=manual_lu.id,
                question_type=q_type,
                concept="Manual Supplementary",
                text=payload.text,
                mcq_options=payload.mcq_options,
                correct_option=payload.correct_option,
                answer_complexity=complexity,
                evaluation_method=eval_method,
                expected_answer=payload.expected_answer,
                acceptable_answers=payload.acceptable_answers,
                difficulty=payload.difficulty,
                hint_level_1=payload.hint_level_1,
                hint_level_2=payload.hint_level_2,
                full_explanation=payload.full_explanation,
                supported_answer_modes=modes,
                question_hash=qhash,
                source_type="MANUAL",
                estimated_time=est_time,
                learning_objective=f"Master concepts for {topic.title}",
                keywords=[],
                source_pages=[],
                question_purpose="Practice",
                progression_level=3,
                bloom_level="COMPREHENSION",
                cognitive_level="UNDERSTAND",
                is_active=True
            )
            uow.session.add(new_q)
            
        uow.commit()
        return create_response({"question_id": q_id}, "Question created successfully in curation pipeline")

