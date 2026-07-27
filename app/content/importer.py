import logging
from sqlalchemy.orm import Session
from app.content.curriculum_parser import ParsedCurriculum
from app.content.learning_unit_builder import ParsedLearningUnit
from app.models.course import Board, Grade, Subject, Chapter, Topic, Subtopic, LearningUnit

logger = logging.getLogger(__name__)

class ContentImporter:
    """
    Service responsible for safely persisting parsed curriculum hierarchies 
    and highly granular learning units into PostgreSQL.
    """
    
    def import_curriculum(self, db: Session, parsed: ParsedCurriculum) -> Chapter:
        """
        Idempotently inserts the Board, Grade, and Subject to avoid duplicates,
        then forcefully inserts the new Chapter, Topics, and Subtopics.
        """
        try:
            logger.info(f"Importing curriculum for {parsed.board} > {parsed.grade} > {parsed.subject}")
            
            # 1. Get or Create Board
            board = db.query(Board).filter(Board.name == parsed.board).first()
            if not board:
                board = Board(name=parsed.board)
                db.add(board)
                db.flush() # Flush to generate UUIDs instantly without committing
                
            # 2. Get or Create Grade
            grade = db.query(Grade).filter(Grade.name == parsed.grade, Grade.board_id == board.id).first()
            if not grade:
                grade = Grade(name=parsed.grade, board_id=board.id)
                db.add(grade)
                db.flush()
                
            # 3. Get or Create Subject
            subject = db.query(Subject).filter(Subject.name == parsed.subject, Subject.grade_id == grade.id).first()
            if not subject:
                subject = Subject(name=parsed.subject, grade_id=grade.id)
                db.add(subject)
                db.flush()
                
            # 4. Insert Chapter
            chapter = Chapter(title=parsed.chapter.title, subject_id=subject.id)
            db.add(chapter)
            db.flush()
            
            # 5. Insert Topics & Subtopics
            for p_topic in parsed.chapter.topics:
                topic = Topic(
                    title=p_topic.title,
                    chapter_id=chapter.id
                )
                db.add(topic)
                db.flush()
                
                for p_subtopic in p_topic.subtopics:
                    subtopic = Subtopic(
                        title=p_subtopic.title.replace('\x00', '') if p_subtopic.title else "",
                        content=p_subtopic.content.replace('\x00', '') if p_subtopic.content else "",
                        topic_id=topic.id
                    )
                    db.add(subtopic)
                    
            db.commit()
            logger.info(f"Successfully imported Chapter: {chapter.title} with UUID {chapter.id}")
            return chapter
            
        except Exception as e:
            db.rollback()
            logger.error(f"Database import failed for Curriculum: {str(e)}")
            raise RuntimeError(f"Import failed: {str(e)}")


    def import_learning_units(self, db: Session, subtopic_id: str, units: list[ParsedLearningUnit]) -> list[LearningUnit]:
        """
        Persists newly generated learning units and securely links them to their parent Subtopic.
        """
        try:
            db_units = []
            for p_unit in units:
                content = p_unit.content.replace('\x00', '') if p_unit.content else ""
                title = p_unit.title.replace('\x00', '') if p_unit.title else ""
                learning_objective = p_unit.learning_objective.replace('\x00', '') if p_unit.learning_objective else ""
                summary = p_unit.summary.replace('\x00', '') if p_unit.summary else ""
                
                unit = LearningUnit(
                    subtopic_id=subtopic_id,
                    title=title,
                    content=content,
                    learning_objective=learning_objective,
                    keywords=p_unit.keywords,
                    difficulty=p_unit.difficulty,
                    estimated_reading_time=p_unit.estimated_reading_time,
                    source_pages=p_unit.source_pages,
                    summary=summary
                )
                db.add(unit)
                db_units.append(unit)
                
            db.commit()
            logger.info(f"Successfully imported {len(db_units)} Learning Units for Subtopic {subtopic_id}")
            return db_units
            
        except Exception as e:
            db.rollback()
            logger.error(f"Database import failed for Learning Units: {str(e)}")
            raise RuntimeError(f"Import failed: {str(e)}")
