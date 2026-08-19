import sys
import os
from datetime import datetime, timezone, timedelta
import logging

# Ensure parent directory is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database.session import SessionLocal
from app.repositories.base.unit_of_work import UnitOfWork
from app.models.core.student import Student
from app.models.assessment.learning_session import LearningSession
from app.models.learning.student_mastery import StudentMastery
from app.models.course import LearningUnit
from app.constants.session import SessionType
from app.application.notification_service import NotificationService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("scheduled_notifications")

def get_first_name(full_name: str) -> str:
    if not full_name:
        return "there"
    parts = full_name.strip().split()
    return parts[0] if parts else "there"

def process_scheduled_notifications():
    db = SessionLocal()
    uow = UnitOfWork(lambda: db)
    notification_service = NotificationService(uow)

    now = datetime.now(timezone.utc)
    today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
    seven_days_ago = now - timedelta(days=7)
    three_days_ago = now - timedelta(days=3)

    logger.info(f"Starting scheduled notification run at {now.isoformat()}")

    try:
        # Fetch all active students who have device tokens registered
        students = db.query(Student).filter(
            Student.device_tokens.any(is_active=True)
        ).all()

        logger.info(f"Found {len(students)} students with active device tokens.")

        for student in students:
            first_name = get_first_name(student.name)
            student_id = student.id
            logger.info(f"Processing student: {student.email} (ID: {student_id})")

            # 1. Check if daily session completed today
            completed_today = db.query(LearningSession).filter(
                LearningSession.student_id == student_id,
                LearningSession.completion_reason == "COMPLETED",
                LearningSession.end_time >= today_start
            ).count() > 0

            # 2. Check if revision completed in last 7 days
            revision_completed_recently = db.query(LearningSession).filter(
                LearningSession.student_id == student_id,
                LearningSession.completion_reason == "COMPLETED",
                LearningSession.session_type.in_([SessionType.REVISION, SessionType.WEEKLY_REVIEW]),
                LearningSession.end_time >= seven_days_ago
            ).count() > 0

            # 3. Check for weak concepts
            weak_mastery = db.query(StudentMastery, LearningUnit.title).join(
                LearningUnit, StudentMastery.concept_id == LearningUnit.id
            ).filter(
                StudentMastery.student_id == student_id,
                (StudentMastery.mastery_percentage < 0.5) | 
                ((StudentMastery.mastery_percentage > 1.0) & (StudentMastery.mastery_percentage < 50.0))
            ).order_by(StudentMastery.mastery_percentage.asc()).first()

            # 4. Check for inactivity (last session ended > 3 days ago)
            latest_session = db.query(LearningSession).filter(
                LearningSession.student_id == student_id,
                LearningSession.completion_reason == "COMPLETED"
            ).order_by(LearningSession.end_time.desc()).first()

            is_inactive = False
            if latest_session and latest_session.end_time < three_days_ago:
                is_inactive = True
            elif not latest_session:
                is_inactive = True

            # Decide which notification to send
            title = ""
            body = ""
            notification_type = ""

            if not completed_today:
                if student.streak_days > 0:
                    # Daily Streak Reminder
                    notification_type = "daily_streak_reminder"
                    title = "Keep the Streak Alive! 🔥"
                    body = f"Hi {first_name}, your {student.streak_days}-day streak is pending! Hurry keep it up, never break your streak."
                else:
                    if is_inactive:
                        # Friendly Re-engagement Nudge
                        notification_type = "re_engagement_nudge"
                        title = "Your Study Buddy Misses You! 🎒"
                        body = f"Hi {first_name}, let's get back on track! Spend just 10 minutes practicing today."
                    else:
                        # Daily Streak Builder
                        notification_type = "daily_streak_builder"
                        title = "Start Your Streak Today! 🚀"
                        body = f"Hi {first_name}, begin your daily practice and start building your learning streak today!"
            else:
                # Student already studied today
                if not revision_completed_recently:
                    # Weekly Revision Reminder
                    notification_type = "weekly_revision_reminder"
                    title = "Time for Revision! 🧠"
                    body = f"Hi {first_name}, revision is due! Review what you learned this week to make it stick."
                elif weak_mastery:
                    # Concept Mastery Booster
                    concept_title = weak_mastery[1]
                    notification_type = "mastery_booster"
                    title = "Boost Your Mastery! ⚡"
                    body = f"Hi {first_name}, let's level up your mastery in '{concept_title}' with a quick practice session."

            if title and body:
                logger.info(f"Sending '{notification_type}' push to {student.email}: '{body}'")
                notification_service.send_push_to_student(
                    student_id=student_id,
                    title=title,
                    body=body,
                    data={"type": notification_type}
                )
            else:
                logger.info(f"No notification needed for {student.email} at this time.")

    except Exception as e:
        logger.error(f"Error during scheduled notifications run: {e}", exc_info=True)
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    process_scheduled_notifications()
