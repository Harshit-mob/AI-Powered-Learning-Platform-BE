import uuid
import logging
import os
from typing import Dict, Any, List

from app.repositories.base.unit_of_work import UnitOfWork
from app.models.quiz import QuestionBank, DraftQuestion
from app.content.pdf_extractor import PDFExtractor
from app.content.ocr_service import OCRService
from app.content.question_generator import QuestionGenerationService
from app.content.ai_provider import GoogleGeminiProvider

logger = logging.getLogger(__name__)

class QBankPipelineService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        
        # Instantiate OCR and PDF Extractor
        ocr_service = OCRService()
        self.pdf_extractor = PDFExtractor(ocr_service=ocr_service)
        
        ai_provider = GoogleGeminiProvider()
        self.question_generator = QuestionGenerationService(ai_provider=ai_provider)

    def process_qbank_pdf(self, qbank_id: uuid.UUID, file_path: str):
        """
        Runs asynchronously in a background thread/process.
        Extracts content, sends it to the AI generation engine, and populates draft questions.
        """
        logger.info(f"Starting QBank PDF processing pipeline for QBank ID: {qbank_id}")
        
        with self.uow:
            qbank = self.uow.session.query(QuestionBank).filter(QuestionBank.id == qbank_id).first()
            if not qbank:
                logger.error(f"QuestionBank with ID {qbank_id} not found in DB.")
                # Cleanup file
                if os.path.exists(file_path):
                    os.remove(file_path)
                return
                
            qbank.status = "PROCESSING"
            chapter_id = qbank.chapter_id
            subject_id = qbank.subject_id
            self.uow.commit()

        try:
            # 1. Parse PDF pages using PDFExtractor
            logger.info(f"Extracting pages from PDF file: {file_path}")
            pages = self.pdf_extractor.extract(file_path)
            full_text = "\n".join([p.text for p in pages])
            
            if not full_text.strip():
                raise ValueError("PDF text extraction resulted in empty content.")
 
            # 2. Get Chapter context from DB
            from app.models.course import Board, Grade, Chapter, Subject, Topic, Subtopic, LearningUnit
            with self.uow:
                chapter = self.uow.session.query(Chapter).filter(Chapter.id == chapter_id).first()
                if not chapter:
                    raise ValueError(f"Chapter with ID {chapter_id} not found.")
                
                subject = self.uow.session.query(Subject).filter(Subject.id == subject_id).first()
                subject_name = subject.name if subject else "General"
                
                board_name = "CBSE"
                grade_name = "Grade 6"
                if subject:
                    grade_obj = self.uow.session.query(Grade).filter(Grade.id == subject.grade_id).first()
                    if grade_obj:
                        grade_name = grade_obj.name
                        board_obj = self.uow.session.query(Board).filter(Board.id == grade_obj.board_id).first()
                        if board_obj:
                            board_name = board_obj.name
                
                # Fetch all Learning Units under this chapter
                db_lus = self.uow.session.query(
                    LearningUnit.id,
                    LearningUnit.title,
                    LearningUnit.learning_objective,
                    Topic.title.label("topic_title"),
                    Subtopic.title.label("subtopic_title")
                ).join(Subtopic, Subtopic.id == LearningUnit.subtopic_id) \
                 .join(Topic, Topic.id == Subtopic.topic_id) \
                 .filter(Topic.chapter_id == chapter.id).all()
                 
                if not db_lus:
                    logger.info(f"No learning units found under Chapter {chapter.title}. Generating curriculum & learning units on the fly from PDF...")
                    
                    from app.content.curriculum_parser import CurriculumParser
                    from app.content.importer import ContentImporter
                    from app.content.learning_unit_builder import LearningUnitBuilder
                    
                    # A. Parse the curriculum from the PDF full text
                    parser = CurriculumParser(ai_provider=self.question_generator.ai_provider)
                    parsed_curr = parser.parse(cleaned_text=full_text, metadata_hints={
                        "board": board_name,
                        "grade": grade_name,
                        "subject": subject_name,
                        "chapter": chapter.title
                    })
                    
                    # B. Import the Board/Grade/Subject/Chapter/Topic/Subtopic hierarchy
                    importer = ContentImporter()
                    # ContentImporter expects to create its own Chapter. 
                    # To avoid creating duplicate chapters, we override/mock it or update the importer.
                    # Or we can just import the topics/subtopics under our existing chapter manually.
                    # Let's import manually or let the importer run and then link if it creates a new chapter.
                    # Let's link the subtopics and topics directly under our existing chapter ID to be clean and simple.
                    for p_topic in parsed_curr.chapter.topics:
                        topic = Topic(
                            title=p_topic.title,
                            chapter_id=chapter.id
                        )
                        self.uow.session.add(topic)
                        self.uow.session.flush()
                        
                        for p_subtopic in p_topic.subtopics:
                            subtopic = Subtopic(
                                title=p_subtopic.title.replace('\x00', '') if p_subtopic.title else "",
                                content=p_subtopic.content.replace('\x00', '') if p_subtopic.content else "",
                                topic_id=topic.id
                            )
                            self.uow.session.add(subtopic)
                            self.uow.session.flush()
                            
                            # C. Build learning units for this subtopic
                            # Serialise the subtopic as json to slice
                            import json
                            subtopic_payload = json.dumps({
                                "subtopics": [{
                                    "title": p_subtopic.title,
                                    "content": p_subtopic.content,
                                    "learning_objectives": p_subtopic.learning_objectives
                                }]
                            })
                            lu_builder = LearningUnitBuilder(ai_provider=self.question_generator.ai_provider)
                            parsed_lus = lu_builder.build_from_curriculum(subtopic_payload)
                            
                            # D. Persist learning units linked to subtopic
                            importer.import_learning_units(self.uow.session, subtopic.id, parsed_lus)
                            
                    self.uow.commit()
                    
                    # Re-query learning units
                    db_lus = self.uow.session.query(
                        LearningUnit.id,
                        LearningUnit.title,
                        LearningUnit.learning_objective,
                        Topic.title.label("topic_title"),
                        Subtopic.title.label("subtopic_title")
                    ).join(Subtopic, Subtopic.id == LearningUnit.subtopic_id) \
                     .join(Topic, Topic.id == Subtopic.topic_id) \
                     .filter(Topic.chapter_id == chapter.id).all()
                     
                    if not db_lus:
                        raise ValueError(f"Failed to generate learning units for Chapter {chapter.title}.")

            # Map DB query results to payload format expected by question generator
            learning_units_payload = [
                {
                    "id": str(lu.id),
                    "title": lu.title,
                    "learning_objective": lu.learning_objective or lu.title,
                    "textbook_context": full_text
                }
                for lu in db_lus
            ]

            # 3. Call AI Question Generator
            logger.info(f"Generating questions for {len(learning_units_payload)} Learning Units in {subject_name}...")
            # We treat the entire PDF as the context for each LU in the chapter
            generation_result = self.question_generator.generate_question_bank(
                subject=subject_name,
                grade=6,  # Default to grade 6 mapping
                board="CBSE",
                chapter=chapter.title,
                topic=db_lus[0].topic_title if db_lus else "General",
                sub_topic=db_lus[0].subtopic_title if db_lus else "General",
                learning_units=learning_units_payload
            )

            generated_questions = generation_result.get("questions", [])
            logger.info(f"AI generated {len(generated_questions)} questions successfully.")

            # 4. Insert Draft Questions to draft_questions table
            with self.uow:
                qbank_record = self.uow.session.query(QuestionBank).filter(QuestionBank.id == qbank_id).first()
                
                drafts = []
                for pq in generated_questions:
                    merged_keywords = list(set(pq.keywords + pq.voice_expected_keywords))
                    
                    draft_q = DraftQuestion(
                        id=uuid.uuid4(),
                        question_bank_id=qbank_id,
                        learning_unit_id=uuid.UUID(pq.learning_unit_id),
                        question_type=pq.question_type,
                        concept=pq.concept,
                        text=pq.question,
                        mcq_options=pq.mcq_options,
                        correct_option=pq.correct_option,
                        answer_complexity=pq.answer_complexity,
                        evaluation_method=pq.evaluation_method,
                        expected_answer=pq.expected_answer,
                        acceptable_answers=pq.acceptable_answers,
                        difficulty=pq.difficulty or 2,
                        bloom_level=pq.bloom_level,
                        cognitive_level=pq.cognitive_level,
                        hint_level_1=pq.hint_level_1,
                        hint_level_2=pq.hint_level_2,
                        full_explanation=pq.full_explanation,
                        source_pages=pq.source_pages,
                        keywords=merged_keywords,
                        question_purpose=pq.question_purpose or "Practice",
                        progression_level=pq.progression_level or 3,
                        status="APPROVED"
                    )
                    drafts.append(draft_q)
                    self.uow.session.add(draft_q)
                
                # Update QBank Status to PENDING_REVIEW
                qbank_record.status = "PENDING_REVIEW"
                qbank_record.total_questions = len(drafts)
                self.uow.commit()
                logger.info(f"Saved {len(drafts)} draft questions for review under QBank {qbank_id}")

        except Exception as e:
            logger.exception(f"Error occurred in QBank pipeline for ID {qbank_id}: {str(e)}")
            with self.uow:
                qbank_record = self.uow.session.query(QuestionBank).filter(QuestionBank.id == qbank_id).first()
                if qbank_record:
                    qbank_record.status = "FAILED"
                    qbank_record.error_message = str(e)
                    self.uow.commit()

        finally:
            # Delete temp PDF file
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.info(f"Cleaned up temporary PDF file: {file_path}")
                except Exception as ex:
                    logger.error(f"Failed to delete temp file {file_path}: {str(ex)}")
