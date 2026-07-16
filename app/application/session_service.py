import uuid
from typing import Dict, Any, List

from app.repositories.base.unit_of_work import UnitOfWork
from app.runtime.session.session_generator import SessionGenerator
from app.runtime.session.session_types import SessionType, LearningContext
from app.api.v1.errors import APIException
from app.assessment.evaluation_engine import EvaluationEngine

class SessionApplicationService:
    """
    Orchestrates boundary crossing between FastAPI controllers and Runtime engines.
    """
    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.session_generator = SessionGenerator(uow)
        self.eval_engine = EvaluationEngine()

    def generate_session(self, student_id: uuid.UUID, payload: Dict[str, Any]) -> Dict[str, Any]:
        # payload has either chapter_ids or topic_ids based on schema validation
        
        chapter_ids = payload.get("chapter_ids")
        topic_ids = payload.get("topic_ids")
        multi_topic_ids = payload.get("multi_topic_ids")
        student_ids = payload.get("student_ids")
        
        if chapter_ids and not topic_ids and not multi_topic_ids and not student_ids:
            cid = chapter_ids[0]
            content_id = cid if isinstance(cid, uuid.UUID) else uuid.UUID(str(cid))
            content_type = "CHAPTER"
            session_type = SessionType.CHAPTER_REVISION
        elif topic_ids and not chapter_ids and not multi_topic_ids and not student_ids:
            tid = topic_ids[0]
            content_id = tid if isinstance(tid, uuid.UUID) else uuid.UUID(str(tid))
            content_type = "TOPIC"
            session_type = SessionType.DAILY_PRACTICE
        elif multi_topic_ids and not chapter_ids and not topic_ids and not student_ids:
            content_id = [tid if isinstance(tid, uuid.UUID) else uuid.UUID(str(tid)) for tid in multi_topic_ids]
            content_type = "MULTI_TOPIC"
            session_type = SessionType.DAILY_PRACTICE
        elif student_ids and not chapter_ids and not topic_ids and not multi_topic_ids:
            sid = student_ids[0]
            content_id = [sid if isinstance(sid, uuid.UUID) else uuid.UUID(str(sid))]
            content_type = "STUDENT"
            session_type = SessionType.WEAK_POINT
        else:
            raise APIException("INVALID_REQUEST", "Provide exactly one scope", 400)
            
        from app.runtime.session.exceptions import NoEligibleQuestionsError, SessionEngineException
        
        try:
            session_payload = self.session_generator.generate(
                student_id=student_id,
                content_id=content_id,
                content_type=content_type,
                session_type=session_type
            )
        except NoEligibleQuestionsError as e:
            raise APIException("NO_QUESTIONS_FOUND", str(e), 404)
        except SessionEngineException as e:
            msg = str(e)
            if msg.startswith("INSUFFICIENT_QUESTIONS|"):
                _, err_msg = msg.split("|", 1)
                raise APIException("INSUFFICIENT_QUESTIONS", err_msg, 400)
            raise APIException("SESSION_GENERATION_FAILED", str(e), 400)
        
        return session_payload.model_dump()

    def answer_question(self, student_id: uuid.UUID, payload: Dict[str, Any]) -> Dict[str, Any]:
        sid = payload["session_id"]
        session_id = sid if isinstance(sid, uuid.UUID) else uuid.UUID(str(sid))
        qid = payload["question_id"]
        question_id = qid if isinstance(qid, uuid.UUID) else uuid.UUID(str(qid))
        
        student_answer = payload.get("student_answer", "")
        time_taken = payload.get("time_taken", 0)
        answer_mode = payload.get("answer_mode", "TEXT")
        hints_used = payload.get("hints_used", 0)
        device_type = payload.get("device_type", "UNKNOWN")
        is_skipped = payload.get("is_skipped", False)
        
        with self.uow:
            question = self.uow.questions.get_by_id(question_id)
            if not question:
                raise APIException("NOT_FOUND", "Question not found", 404)
                
            expected_answer = question.expected_answer or question.correct_option or ""
            question_type = question.question_type or "MCQ"
            
            if is_skipped:
                eval_status = "SKIPPED"
                explanation = f"You skipped this question. The correct answer was: {expected_answer}."
                mastery_change = -0.01
                is_correct = False
                eval_score = 0.0
                eval_method = "SKIPPED"
                student_answer = "SKIPPED"
            else:
                from app.assessment.models.dto import AnswerSubmission
                submission = AnswerSubmission(
                    session_id=session_id,
                    question_id=question_id,
                    student_id=student_id,
                    provided_answer=student_answer,
                    time_taken_seconds=time_taken,
                    hints_used=hints_used,
                    device_type=device_type,
                    confidence_rating=None
                )
                
                result = self.eval_engine.evaluate(
                    submission=submission,
                    expected_answer=expected_answer,
                    question_type=question_type,
                    acceptable_answers=question.acceptable_answers
                )
                
                if result.evaluation_score >= 1.0:
                    eval_status = "CORRECT"
                    explanation = question.full_explanation or "Great job! You got it right!"
                    mastery_change = 0.05
                elif result.evaluation_score > 0.0:
                    eval_status = "PARTIAL"
                    explanation = question.full_explanation or f"You're on the right track! The full answer is: {expected_answer}"
                    mastery_change = 0.02
                else:
                    eval_status = "WRONG"
                    explanation = question.full_explanation or f"Good effort! The correct concept here is: {expected_answer}. Keep practicing, you're doing great!"
                    mastery_change = -0.02
                    
                is_correct = result.is_correct
                eval_score = result.evaluation_score
                eval_method = result.evaluation_method
            
            # In Phase 1, we track mastery directly at the Learning Unit level
            # We map learning_unit_id to concept_id in the mastery table to avoid schema migrations
            lu_id = question.learning_unit_id
            if lu_id:
                mastery = self.uow.mastery.get_by_concept(student_id, lu_id)
                current_pct = mastery.mastery_percentage if mastery else 0.0
                new_pct = min(1.0, max(0.0, current_pct + mastery_change))
                
                mastery_status = "NEW"
                if new_pct > 0.0:
                    mastery_status = "LEARNING"
                if new_pct > 0.4:
                    mastery_status = "PRACTICING"
                if new_pct >= 0.8:
                    mastery_status = "MASTERED"
                
                correct_count = (mastery.correct_count if mastery else 0) + (1 if eval_status == "CORRECT" else 0)
                wrong_count = (mastery.wrong_count if mastery else 0) + (1 if eval_status == "WRONG" else 0)
                
                self.uow.mastery.upsert_mastery(student_id, lu_id, {
                    "mastery_percentage": new_pct,
                    "status": mastery_status,
                    "correct_count": correct_count,
                    "wrong_count": wrong_count
                })
                
            from app.models.assessment.student_response import StudentResponse
            db_answer = StudentResponse(
                session_id=session_id,
                question_id=question_id,
                provided_answer=student_answer,
                is_correct=is_correct,
                time_taken_seconds=time_taken,
                evaluation_score=eval_score,
                evaluation_method=eval_method,
                expected_answer=expected_answer,
                device_type=device_type,
                hints_used=hints_used,
                question_difficulty=getattr(question, "difficulty", None)
            )
            self.uow.session.add(db_answer)
            self.uow.commit()
            
        return {
            "status": eval_status,
            "evaluation": result.evaluation_score,
            "correct_answer": expected_answer,
            "explanation": explanation,
            "mastery_change": mastery_change
        }

    def complete_session(self, student_id: uuid.UUID, session_id: uuid.UUID) -> Dict[str, Any]:
        with self.uow:
            from app.models.assessment.student_response import StudentResponse
            from app.models.quiz import Question
            from app.models.course import LearningUnit
            
            answers = self.uow.session.query(StudentResponse).filter(StudentResponse.session_id == session_id).all()
            
            total = len(answers)
            correct = sum(1 for a in answers if a.is_correct)
            skipped = sum(1 for a in answers if getattr(a, 'evaluation_method', '') == "SKIPPED")
            accuracy = round(correct / total, 2) if total > 0 else 0.0
            score = correct * 10
            
            mastery_gain = round((accuracy - 0.5) * 0.1, 2) if accuracy > 0 else 0.0
            
            leveled_up = False
            
            session = self.uow.sessions.get_by_id(session_id)
            if session:
                from datetime import datetime, timezone, timedelta
                now = datetime.now(timezone.utc)
                session.end_time = now
                session.accuracy = accuracy
                session.mastery_gain = mastery_gain
                session.questions_answered = total
                session.questions_correct = correct
                session.questions_skipped = skipped
                
            student = self.uow.students.find_by_id(student_id)
            if student:
                # 1. Update Overall Mastery Percentage
                mastery_records = self.uow.mastery.get_by_student(student_id)
                if mastery_records:
                    avg_mastery = sum(m.mastery_percentage for m in mastery_records) / len(mastery_records)
                    student.overall_mastery_percentage = min(1.0, round(avg_mastery, 2))
                elif mastery_gain > 0:
                    student.overall_mastery_percentage = min(1.0, student.overall_mastery_percentage + mastery_gain)
                    
                # 2. Update Total Study Minutes
                if session and session.start_time and session.end_time:
                    duration_minutes = int((session.end_time - session.start_time).total_seconds() / 60)
                    student.total_study_minutes += max(0, duration_minutes)
                    
                # 3. Bump Streak (Max +1 per day)
                if accuracy > 0.0:
                    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                    from app.models.quiz import LearningSession
                    completed_today = self.uow.session.query(LearningSession).filter(
                        LearningSession.student_id == student_id,
                        LearningSession.end_time >= today_start,
                        LearningSession.id != session_id
                    ).count()
                    
                    if completed_today == 0:
                        student.streak_days += 1
                        
                # 4. XP and Leveling
                student.total_xp += score
                new_level = (student.total_xp // 100) + 1
                if new_level > student.current_level:
                    student.current_level = new_level
                    leveled_up = True
                    
                streak = student.streak_days
                total_xp = student.total_xp
                current_level = student.current_level
                self.uow.commit()
            else:
                streak = 0
                total_xp = score
                current_level = 1
            
            # 4. Identify Weak and Strong Learning Units for this session
            weak_lus = []
            strong_lus = []
            
            if answers:
                question_ids = [a.question_id for a in answers]
                questions = self.uow.session.query(Question).filter(Question.id.in_(question_ids)).all()
                q_to_lu = {q.id: q.learning_unit_id for q in questions}
                
                lu_ids = list({lu_id for lu_id in q_to_lu.values() if lu_id})
                if lu_ids:
                    learning_units = self.uow.session.query(LearningUnit).filter(LearningUnit.id.in_(lu_ids)).all()
                    lu_to_title = {lu.id: lu.title for lu in learning_units}
                    
                    lu_stats = {}
                    for a in answers:
                        lu_id = q_to_lu.get(a.question_id)
                        if lu_id:
                            if lu_id not in lu_stats:
                                lu_stats[lu_id] = {"correct": 0, "total": 0}
                            lu_stats[lu_id]["total"] += 1
                            if a.is_correct:
                                lu_stats[lu_id]["correct"] += 1
                    
                    for lu_id, stats in lu_stats.items():
                        lu_acc = stats["correct"] / stats["total"]
                        title = lu_to_title.get(lu_id, "Unknown Topic")
                        if lu_acc < 0.6:
                            weak_lus.append(title)
                        elif lu_acc >= 0.8:
                            strong_lus.append(title)
                
        return {
            "score": score,
            "accuracy": accuracy,
            "mastery_gain": mastery_gain,
            "total_xp": total_xp,
            "current_level": current_level,
            "leveled_up": leveled_up,
            "weak_learning_units": weak_lus,
            "strong_learning_units": strong_lus,
            "recommended_next_session": "REVISION" if accuracy < 0.6 else "DAILY_PRACTICE",
            "daily_goal_progress": {
               "completed": True,
               "streak_maintained": True
            },
            "streak": streak,
            "session_summary": "Great job! Keep practicing." if accuracy >= 0.8 else "Keep practicing to improve!"
        }

    def resume_session(self, student_id: uuid.UUID, session_id: uuid.UUID) -> Dict[str, Any]:
        raise APIException("NOT_IMPLEMENTED", "Resume session is not supported in this phase.", 501)

    def get_session_recommendations(self, student_id: uuid.UUID) -> List[Dict[str, Any]]:
        from app.application.recommendations.recommendation_engine import RecommendationEngine
        engine = RecommendationEngine(self.uow)
        return engine.get_recommendations(student_id)
