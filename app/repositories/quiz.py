from sqlalchemy.orm import Session
from app.repositories.base import CRUDBase
from app.models.quiz import Question, QuizSession, SubmittedAnswer
from app.schemas.quiz import QuestionCreate, QuizSessionCreate, AnswerSubmit

class CRUDQuestion(CRUDBase[Question, QuestionCreate, QuestionCreate]):
    pass

class CRUDQuizSession(CRUDBase[QuizSession, QuizSessionCreate, QuizSessionCreate]):
    pass

class CRUDSubmittedAnswer(CRUDBase[SubmittedAnswer, AnswerSubmit, AnswerSubmit]):
    def submit_answer(self, db: Session, *, obj_in: AnswerSubmit) -> SubmittedAnswer:
        # 1. Fetch the question to get the correct option
        question = db.query(Question).filter(Question.id == obj_in.question_id).first()
        if not question:
            raise ValueError("Question not found")
        
        # 2. Check if answer is correct
        is_correct = (obj_in.selected_option.lower() == question.correct_option.lower())
        
        # 3. Save the answer
        db_answer = SubmittedAnswer(
            session_id=obj_in.session_id,
            question_id=obj_in.question_id,
            selected_option=obj_in.selected_option.lower(),
            is_correct=is_correct
        )
        db.add(db_answer)
        
        # 4. If correct, update the session score
        if is_correct:
            session = db.query(QuizSession).filter(QuizSession.id == obj_in.session_id).first()
            if session:
                session.score += 1
                db.add(session)
        
        db.commit()
        db.refresh(db_answer)
        return db_answer

question = CRUDQuestion(Question)
quiz_session = CRUDQuizSession(QuizSession)
submitted_answer = CRUDSubmittedAnswer(SubmittedAnswer)
