import uuid
from typing import Dict, Any
from app.repositories.base.unit_of_work import UnitOfWork

class StudentService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def get_profile(self, student_id: uuid.UUID) -> Dict[str, Any]:
        with self.uow:
            check_and_update_student_streak(self.uow, student_id)
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
                "completed_sessions": completed_count,
                "role": getattr(student, "role", "STUDENT")
            }

    def get_progress(self, student_id: uuid.UUID) -> Dict[str, Any]:
        with self.uow:
            check_and_update_student_streak(self.uow, student_id)
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

            from app.models.course import Subject, Chapter, Topic
            from app.models.assessment.learning_session import LearningSession
            from app.models.learning.student_daily_learning import StudentDailyLearning
            
            # Get completed topic IDs for the student
            completed_sessions = self.uow.session.query(LearningSession.content_id).filter(
                LearningSession.student_id == student_id,
                LearningSession.content_type.in_(["TOPIC", "MULTI_TOPIC"]),
                LearningSession.completion_reason == "COMPLETED"
            ).all()
            completed_session_topic_ids = {str(s[0]) for s in completed_sessions}

            daily_learnings = self.uow.session.query(StudentDailyLearning).filter(
                StudentDailyLearning.student_id == student_id,
                StudentDailyLearning.status == "COMPLETED"
            ).all()
            completed_daily_topic_ids = {str(dl.topic_id) for dl in daily_learnings}
            
            completed_topic_ids = completed_session_topic_ids.union(completed_daily_topic_ids)

            # Retrieve all topics grouped by subject and chapter
            topics_query = self.uow.session.query(
                Subject.id, Subject.name, Chapter.id, Chapter.title, Topic.id
            ).select_from(Subject)\
             .join(Chapter, Chapter.subject_id == Subject.id)\
             .join(Topic, Topic.chapter_id == Chapter.id).all()
             
            subject_map = {}
            for sub_id, sub_name, ch_id, ch_title, topic_id in topics_query:
                sub_id_str = str(sub_id)
                ch_id_str = str(ch_id)
                
                if sub_id_str not in subject_map:
                    subject_map[sub_id_str] = {
                        "subject_id": sub_id_str,
                        "subject_name": sub_name,
                        "progress": 0,
                        "chapters": {},
                        "_total_topics": 0,
                        "_completed_topics": 0
                    }
                
                sub = subject_map[sub_id_str]
                if ch_id_str not in sub["chapters"]:
                    sub["chapters"][ch_id_str] = {
                        "chapter_id": ch_id_str,
                        "chapter_title": ch_title,
                        "progress": 0,
                        "_total_topics": 0,
                        "_completed_topics": 0
                    }
                
                ch = sub["chapters"][ch_id_str]
                ch["_total_topics"] += 1
                sub["_total_topics"] += 1
                
                if str(topic_id) in completed_topic_ids:
                    ch["_completed_topics"] += 1
                    sub["_completed_topics"] += 1

            subject_progress = []
            grand_total_topics = 0
            grand_completed_topics = 0
            
            for sub_id, sub in subject_map.items():
                chapters_list = []
                for ch_id, ch in sub["chapters"].items():
                    total_ch = ch.pop("_total_topics")
                    completed_ch = ch.pop("_completed_topics")
                    ch["progress"] = int((completed_ch / total_ch) * 100) if total_ch > 0 else 0
                    chapters_list.append(ch)
                
                total_sub = sub.pop("_total_topics")
                completed_sub = sub.pop("_completed_topics")
                sub["progress"] = int((completed_sub / total_sub) * 100) if total_sub > 0 else 0
                sub["chapters"] = chapters_list
                subject_progress.append(sub)
                
                grand_total_topics += total_sub
                grand_completed_topics += completed_sub
                
            absolute_overall_progress = int((grand_completed_topics / grand_total_topics) * 100) if grand_total_topics > 0 else 0

            return {
                "overall_progress": absolute_overall_progress,
                "current_level": getattr(student, "current_level", 1),
                "total_xp": getattr(student, "total_xp", 0),
                "target_xp": getattr(student, "current_level", 1) * 100,
                "streak_days": student.streak_days,
                "subject_progress": subject_progress,
                "current_mastery": display_prog,
                "recent_sessions": recent_sessions
            }
            
            
    def set_daily_learning(self, student_id: uuid.UUID, learning_date: Any, topic_ids: list[uuid.UUID], source: str) -> None:
        from app.models.learning.student_daily_learning import StudentDailyLearning
        from app.models.course import Topic, Chapter
        
        with self.uow:
            # 1. Delete ALL PENDING entries for this student that are NOT in the newly selected topic_ids
            # This handles unselecting a topic (both for today or previous dates)
            pending_query = self.uow.session.query(StudentDailyLearning).filter(
                StudentDailyLearning.student_id == student_id,
                StudentDailyLearning.status == "PENDING"
            )
            if topic_ids:
                pending_query = pending_query.filter(~StudentDailyLearning.topic_id.in_(topic_ids))
            
            pending_query.delete(synchronize_session='fetch')
            
            # 2. Delete any existing entries for today for the subjects of the newly selected topics
            # so we can insert the new active selections cleanly
            if topic_ids:
                subjects_query = self.uow.session.query(Chapter.subject_id).join(
                    Topic, Topic.chapter_id == Chapter.id
                ).filter(Topic.id.in_(topic_ids)).distinct()
                subject_ids = [row[0] for row in subjects_query.all()]
                
                if subject_ids:
                    ids_to_delete = self.uow.session.query(StudentDailyLearning.id).join(
                        Topic, Topic.id == StudentDailyLearning.topic_id
                    ).join(
                        Chapter, Chapter.id == Topic.chapter_id
                    ).filter(
                        StudentDailyLearning.student_id == student_id,
                        StudentDailyLearning.learning_date == learning_date,
                        Chapter.subject_id.in_(subject_ids)
                    ).all()
                    
                    id_list = [row[0] for row in ids_to_delete]
                    if id_list:
                        self.uow.session.query(StudentDailyLearning).filter(
                            StudentDailyLearning.id.in_(id_list)
                        ).delete(synchronize_session='fetch')

                # 3. Add the selected topics for today if they are not already present
                for topic_id in topic_ids:
                    exists = self.uow.session.query(StudentDailyLearning).filter(
                        StudentDailyLearning.student_id == student_id,
                        StudentDailyLearning.topic_id == topic_id,
                        StudentDailyLearning.learning_date == learning_date
                    ).first()
                    
                    if not exists:
                        daily_learning = StudentDailyLearning(
                            student_id=student_id,
                            topic_id=topic_id,
                            learning_date=learning_date,
                            source=source,
                            status="PENDING"
                        )
                        self.uow.session.add(daily_learning)
            else:
                # If topic_ids is empty, delete any remaining entries for today.
                self.uow.session.query(StudentDailyLearning).filter(
                    StudentDailyLearning.student_id == student_id,
                    StudentDailyLearning.learning_date == learning_date
                ).delete(synchronize_session='fetch')
                
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

    def get_weekly_streak(self, student_id: uuid.UUID) -> list[dict[str, Any]]:
        from datetime import datetime, timezone, timedelta
        from app.models.assessment.learning_session import LearningSession
        from sqlalchemy import func
        
        with self.uow:
            now = datetime.now(timezone.utc)
            today_date = now.date()
            
            # Find the Monday of the current week
            monday_date = today_date - timedelta(days=today_date.weekday())
            
            # Generate the 7 days of the week starting from Monday
            week_days = []
            for i in range(7):
                day_date = monday_date + timedelta(days=i)
                week_days.append(day_date)
                
            # Query all completed learning sessions for the student during this week
            start_datetime = datetime(monday_date.year, monday_date.month, monday_date.day, tzinfo=timezone.utc)
            end_datetime = start_datetime + timedelta(days=7)
            
            completed_sessions = self.uow.session.query(
                func.date(LearningSession.end_time)
            ).filter(
                LearningSession.student_id == student_id,
                LearningSession.completion_reason == "COMPLETED",
                LearningSession.end_time >= start_datetime,
                LearningSession.end_time < end_datetime
            ).all()
            
            completed_dates = {s[0] for s in completed_sessions if s[0] is not None}
            
            # Form response
            day_names = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
            result = []
            for i, d in enumerate(week_days):
                is_completed = False
                for c_date in completed_dates:
                    if isinstance(c_date, str):
                        # Handle potential string return from SQLite/Postgres func.date
                        # e.g., "2026-08-13" or "2026-08-13 00:00:00"
                        date_part = c_date.split()[0]
                        if date_part == d.isoformat():
                            is_completed = True
                            break
                    elif c_date == d:
                        is_completed = True
                        break
                        
                result.append({
                    "day_name": day_names[i],
                    "date": d.strftime("%d"), # "03", "04", etc.
                    "full_date": d.isoformat(), # "2026-08-03"
                    "completed": is_completed,
                    "is_today": d == today_date
                })
                
            return result



def check_and_update_student_streak(uow: UnitOfWork, student_id: uuid.UUID) -> int:
    from datetime import datetime, timezone, timedelta
    from app.models.assessment.learning_session import LearningSession
    
    student = uow.students.find_by_id(student_id)
    if not student:
        return 0
        
    now = datetime.now(timezone.utc)
    today_date = now.date()
    yesterday_date = today_date - timedelta(days=1)
    
    # Find the most recent completed DAILY_PRACTICE session for this student
    latest_completed = uow.session.query(LearningSession).filter(
        LearningSession.student_id == student_id,
        LearningSession.session_type == "DAILY_PRACTICE",
        LearningSession.completion_reason == "COMPLETED",
        LearningSession.end_time.isnot(None)
    ).order_by(LearningSession.end_time.desc()).first()
    
    if not latest_completed:
        # No sessions ever completed
        student.streak_days = 0
        uow.commit()
        return 0
        
    latest_date = latest_completed.end_time.date()
    
    if latest_date == today_date:
        # Already completed today, streak is active
        pass
    elif latest_date == yesterday_date:
        # Completed yesterday, but not today yet. Streak is still active.
        pass
    else:
        # Last completion was before yesterday. Streak is broken!
        student.streak_days = 0
        uow.commit()
        
    return student.streak_days
