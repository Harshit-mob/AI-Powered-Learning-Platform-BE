from app.repositories.base import CRUDBase
from app.models.course import Chapter, Topic, Subtopic
from app.schemas.course import ChapterCreate, TopicCreate, SubtopicCreate

class CRUDChapter(CRUDBase[Chapter, ChapterCreate, ChapterCreate]):
    pass

class CRUDTopic(CRUDBase[Topic, TopicCreate, TopicCreate]):
    pass

class CRUDSubtopic(CRUDBase[Subtopic, SubtopicCreate, SubtopicCreate]):
    pass

# Instantiate the repositories to be used across the app
chapter = CRUDChapter(Chapter)
topic = CRUDTopic(Topic)
subtopic = CRUDSubtopic(Subtopic)
