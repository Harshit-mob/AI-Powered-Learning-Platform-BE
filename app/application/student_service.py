import uuid
from typing import Dict, Any
from app.repositories.base.unit_of_work import UnitOfWork

class StudentService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def get_profile(self, student_id: uuid.UUID) -> Dict[str, Any]:
        with self.uow:
            student = self.uow.students.find_by_id(student_id)
            if not student:
                return {}
            
            # For phase 1, compute completed sessions via all sessions retrieved
            sessions = self.uow.sessions.student_sessions(student_id, limit=100)
            completed_count = sum(1 for s in sessions if s.end_time is not None)
            
            return {
                "name": student.name,
                "email": student.email,
                "current_streak": student.streak_days,
                "current_level": getattr(student, "current_level", 1),
                "total_xp": getattr(student, "total_xp", 0),
                "target_xp": getattr(student, "current_level", 1) * 100,
                "daily_goal_minutes": 30, # default placeholder
                "total_mastery_percentage": int(student.overall_mastery_percentage * 100) if student.overall_mastery_percentage <= 1.0 else int(student.overall_mastery_percentage),
                "completed_sessions": completed_count
            }

    def get_progress(self, student_id: uuid.UUID) -> Dict[str, Any]:
        with self.uow:
            student = self.uow.students.find_by_id(student_id)
            if not student:
                return {}
                
            sessions = self.uow.sessions.student_sessions(student_id, limit=5)
            
            recent_sessions = []
            for s in sessions:
                # Score is XP earned (correct * 10). If missing (legacy data), fallback to 0
                xp_score = getattr(s, 'questions_correct', 0) * 10
                recent_sessions.append({
                    "session_id": str(s.id),
                    "date": s.start_time.isoformat() if s.start_time else None,
                    "score": xp_score
                })

            mastery_val = student.overall_mastery_percentage
            # Ensure it is displayed safely depending on whether DB stores 0-1 or 0-100
            display_prog = int(mastery_val * 100) if mastery_val <= 1.0 else int(mastery_val)

            from sqlalchemy import func
            from app.models.course import Subject, Chapter, Topic, Subtopic, LearningUnit
            from app.models.learning.student_mastery import StudentMastery
            
            # 1. Total LUs per chapter and subject
            chapter_lu_counts = self.uow.session.query(
                Subject.id, Subject.name, Chapter.id, Chapter.title, func.count(LearningUnit.id)
            ).select_from(Subject)\
             .join(Chapter, Chapter.subject_id == Subject.id)\
             .join(Topic, Topic.chapter_id == Chapter.id)\
             .join(Subtopic, Subtopic.topic_id == Topic.id)\
             .join(LearningUnit, LearningUnit.subtopic_id == Subtopic.id)\
             .group_by(Subject.id, Subject.name, Chapter.id, Chapter.title).all()
             
            # 2. Sum of mastery per chapter for this student
            student_mastery_sum = self.uow.session.query(
                Chapter.id, func.sum(StudentMastery.mastery_percentage)
            ).join(Topic, Topic.chapter_id == Chapter.id)\
             .join(Subtopic, Subtopic.topic_id == Topic.id)\
             .join(LearningUnit, LearningUnit.subtopic_id == Subtopic.id)\
             .join(StudentMastery, StudentMastery.concept_id == LearningUnit.id)\
             .filter(StudentMastery.student_id == student_id)\
             .group_by(Chapter.id).all()
             
            mastery_dict = {ch_id: val for ch_id, val in student_mastery_sum}
            
            subject_map = {}
            grand_total_lus = 0
            grand_total_mastery = 0.0
            
            for sub_id, sub_name, ch_id, ch_title, total_lus in chapter_lu_counts:
                if sub_id not in subject_map:
                    subject_map[sub_id] = {
                        "subject_id": str(sub_id),
                        "subject_name": sub_name,
                        "progress": 0,
                        "chapters": [],
                        "_total_lus": 0,
                        "_total_mastery": 0.0
                    }
                    
                sum_mastery = mastery_dict.get(ch_id, 0.0)
                
                # Subject totals
                subject_map[sub_id]["_total_lus"] += total_lus
                subject_map[sub_id]["_total_mastery"] += sum_mastery
                
                # Grand totals
                grand_total_lus += total_lus
                grand_total_mastery += sum_mastery
                
                avg_mastery = sum_mastery / total_lus if total_lus > 0 else 0.0
                progress_pct = int(avg_mastery * 100) if avg_mastery <= 1.0 else int(avg_mastery)
                
                subject_map[sub_id]["chapters"].append({
                    "chapter_id": str(ch_id),
                    "chapter_title": ch_title,
                    "progress": progress_pct
                })
                
            subject_progress = []
            for sub in subject_map.values():
                sub_lus = sub.pop("_total_lus")
                sub_mast = sub.pop("_total_mastery")
                sub_pct = (sub_mast / sub_lus) if sub_lus > 0 else 0.0
                sub["progress"] = int(sub_pct * 100) if sub_pct <= 1.0 else int(sub_pct)
                subject_progress.append(sub)
                
            absolute_overall_pct = (grand_total_mastery / grand_total_lus) if grand_total_lus > 0 else 0.0
            absolute_overall_progress = int(absolute_overall_pct * 100) if absolute_overall_pct <= 1.0 else int(absolute_overall_pct)

            return {
                "overall_progress": absolute_overall_progress,
                "current_level": getattr(student, "current_level", 1),
                "total_xp": getattr(student, "total_xp", 0),
                "target_xp": getattr(student, "current_level", 1) * 100,
                "streak_days": student.streak_days,
                "subject_progress": subject_progress,
                "current_mastery": mastery_val,
                "recent_sessions": recent_sessions
            }
            
    def set_daily_learning(self, student_id: uuid.UUID, learning_date: Any, topic_ids: list[uuid.UUID], source: str) -> None:
        from app.models.learning.student_daily_learning import StudentDailyLearning
        with self.uow:
            # Delete any existing entries for this student on this date to ensure idempotency
            self.uow.session.query(StudentDailyLearning).filter(
                StudentDailyLearning.student_id == student_id,
                StudentDailyLearning.learning_date == learning_date
            ).delete()
            
            for topic_id in topic_ids:
                daily_learning = StudentDailyLearning(
                    student_id=student_id,
                    topic_id=topic_id,
                    learning_date=learning_date,
                    source=source,
                    status="PENDING"
                )
                self.uow.session.add(daily_learning)
                
            self.uow.commit()

    def check_daily_status(self, student_id: uuid.UUID) -> Dict[str, Any]:
        from app.models.learning.student_daily_learning import StudentDailyLearning
        from datetime import datetime, timezone
        
        with self.uow:
            today = datetime.now(timezone.utc).date()
            
            # Check if there are any records for today
            count = self.uow.session.query(StudentDailyLearning).filter(
                StudentDailyLearning.student_id == student_id,
                StudentDailyLearning.learning_date == today
            ).count()
            
            return {
                "is_completed": count > 0,
                "learning_date": today.isoformat()
            }
