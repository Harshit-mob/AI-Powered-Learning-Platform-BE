from app.database.session import SessionLocal
from app.services.content.course_service import CourseService
from app.services.content.question_generator import QuestionGenerationService
from app.services.content.ai_provider import GeminiProvider
from app.core.config import settings
import json

def test():
    db = SessionLocal()
    course_service = CourseService(db)
    ai_provider = GeminiProvider(api_key=settings.GEMINI_API_KEY)
    generator = QuestionGenerationService(ai_provider)

    chapter_1 = course_service.get_chapter_by_title("What Is Science?")
    if not chapter_1:
        print("Chapter 1 not found.")
        return
        
    topic = chapter_1.topics[0]
    subtopic = topic.subtopics[0]
    units = [{"id": str(u.id), "title": u.title, "content": u.content, "keywords": u.keywords} for u in subtopic.learning_units]
    
    result = generator.generate_question_bank(
        subject="Science", grade=6, board="CBSE", chapter=chapter_1.title,
        topic=topic.title, sub_topic=subtopic.title, learning_units=units[:1]
    )
    
    if result["questions"]:
        print(json.dumps(result["questions"][0].model_dump(), indent=2, default=str))
    
    db.close()

if __name__ == "__main__":
    test()
