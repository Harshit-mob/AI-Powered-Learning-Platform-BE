import uuid
from typing import Dict, Any, Optional

from app.application.recommendations.providers.base import RecommendationProvider
from app.models.assessment.learning_session import LearningSession


class RevisionProvider(RecommendationProvider):
    """
    Recommends a revision session when the student's most recent completed session
    had accuracy < 0.6 (i.e. recommended_next_session == 'REVISION').
    Uses the same content_id + content_type from that session.
    """

    def get_recommendation(self, student_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        # Find the most recent completed session for this student
        last_session = (
            self.uow.session.query(LearningSession)
            .filter(
                LearningSession.student_id == student_id,
                LearningSession.end_time.isnot(None),          # completed
                LearningSession.completion_reason == "COMPLETED",
            )
            .order_by(LearningSession.end_time.desc())
            .first()
        )

        if not last_session:
            return None

        # Only surface a revision card if accuracy was below 60%
        if (last_session.accuracy or 0.0) >= 0.6:
            return None

        content_type = last_session.content_type   # e.g. "TOPIC", "CHAPTER"
        content_id   = last_session.content_id     # UUID

        # Map DB content_type → the scope key the session API expects
        scope_map = {
            "TOPIC":       "topic",
            "CHAPTER":     "chapter",
            "MULTI_TOPIC": "multi_topic",
            "STUDENT":     "student",
        }
        scope = scope_map.get(content_type, "topic")

        # Build a human-readable label from the content
        content_label = self._resolve_label(content_type, content_id)

        weak_count = len(last_session.weak_concepts or [])
        accuracy_pct = int((last_session.accuracy or 0.0) * 100)

        return {
            "title": "Revision Session",
            "priority": 2,                          # sits between Daily Practice (1) and Chapter Revision (3)
            "estimated_duration": 10,
            "question_count": 10,
            "xp_reward": 60,
            "status": "READY",
            "reason": (
                f"You scored {accuracy_pct}% in your last session"
                + (f" — {weak_count} weak topic(s) need attention." if weak_count else ".")
            ),
            "session_type": "REVISION",
            "content_type": content_type,
            "content_ids": [str(content_id)],
            "scope": scope,
            "content_label": content_label,
            "weak_concepts": last_session.weak_concepts or [],
        }

    # ── helpers ──────────────────────────────────────────────────────────────

    def _resolve_label(self, content_type: str, content_id: uuid.UUID) -> str:
        """Try to return a human-readable name for the content."""
        try:
            if content_type == "CHAPTER":
                from app.models.course import Chapter
                obj = self.uow.session.query(Chapter).filter_by(id=content_id).first()
                return obj.title if obj else "Chapter"

            elif content_type in ("TOPIC", "MULTI_TOPIC"):
                from app.models.course import Topic
                obj = self.uow.session.query(Topic).filter_by(id=content_id).first()
                return obj.title if obj else "Topic"

        except Exception:
            pass

        return "Previous Session Content"
