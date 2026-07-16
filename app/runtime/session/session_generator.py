import uuid
from typing import List, Dict, Any

from app.repositories.base.unit_of_work import UnitOfWork
from app.runtime.session.session_types import SessionType
from app.runtime.session.candidate_loader import CandidateLoader
from app.runtime.session.student_context_builder import StudentContextBuilder
from app.runtime.session.learning_unit_coverage import LearningUnitCoverage
from app.runtime.session.question_variant_selector import QuestionVariantSelector, VariantScore
from app.runtime.session.distribution_policy import PolicyFactory
from app.runtime.session.pedagogical_sequencer import PedagogicalSequencer
from app.runtime.session.dto import SessionPayload, QuestionDTO
from app.runtime.session.session_validator import SessionValidator

class SessionGenerator:
    """
    Orchestrates the Phase 1 Adaptive Session Engine pipeline.
    Replaces SessionEngine, DailyPracticeEngine, and ChapterRevisionEngine.
    """
    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.validator = SessionValidator(uow)
        
        self.candidate_loader = CandidateLoader(uow)
        self.context_builder = StudentContextBuilder(uow)
        self.lu_coverage = LearningUnitCoverage()
        self.variant_selector = QuestionVariantSelector()
        self.sequencer = PedagogicalSequencer()

    def generate(
        self, 
        student_id: uuid.UUID, 
        content_id: Any, 
        content_type: str, 
        session_type: SessionType
    ) -> SessionPayload:
        
        # 1. Validation
        self.validator.validate_content_access(student_id, content_id, content_type)
        
        # Pipeline execution
        # 2. Load candidates strictly filtered
        lu_map = self.candidate_loader.load_candidates(content_id, content_type)
        
        if not lu_map:
            from app.runtime.session.exceptions import NoEligibleQuestionsError
            raise NoEligibleQuestionsError(f"No active questions found for content {content_id}.")
            
        # 3. Build single runtime context
        context = self.context_builder.build(student_id)
        
        # 4. Create Session Entity inside UoW FIRST so we have an ID for seeding
        session_id = uuid.uuid4()
        
        # Determine actual ID to store in the DB (schema expects UUID)
        primary_content_id = content_id[0] if isinstance(content_id, list) else content_id
        
        with self.uow:
            self.uow.sessions.create_session({
                "id": session_id,
                "student_id": student_id,
                "session_type": session_type.value,
                "content_id": primary_content_id,
                "content_type": content_type
            })
            
            # 5. Rank Learning Units using session_id for seed
            ranked_lus = self.lu_coverage.rank_learning_units(lu_map, context, session_type, session_id)
            
            # 6. Question Variant Selector using session_id for seed
            variants_by_lu: Dict[uuid.UUID, List[VariantScore]] = {}
            for lu_id in ranked_lus:
                candidates = lu_map[lu_id]
                eligible = self.variant_selector.select_variants(candidates, context, session_type, session_id)
                if eligible:
                    variants_by_lu[lu_id] = eligible
                    
            # 7. Distribution Policy Strategy
            policy = PolicyFactory.get_policy(session_type)
            final_scored_variants = policy.apply(ranked_lus, variants_by_lu)
            
            # Extract underlying questions for sequencer
            final_pool = [v.question for v in final_scored_variants]
            
            # 8. Pedagogical Sequencer
            ordered_questions = self.sequencer.sequence(final_pool)
            
            self.uow.commit()

            # Assemble API payload precisely matching existing DTO
            dtos = []
            for q in ordered_questions:
                diff_val = getattr(q, "difficulty", 3)
                diff_str = "MEDIUM" if diff_val == 3 else ("EASY" if diff_val <= 2 else "HARD")
                
                bloom_val = getattr(q, "bloom_level", "RECALL")
                bloom_str = str(bloom_val).upper()
                if bloom_str in ["REMEMBER", "RECALL"]: bloom_str = "RECALL"
                elif bloom_str in ["UNDERSTAND", "COMPREHENSION"]: bloom_str = "COMPREHENSION"
                elif bloom_str in ["APPLY", "APPLICATION"]: bloom_str = "APPLICATION"
                elif bloom_str in ["ANALYZE", "ANALYSIS"]: bloom_str = "ANALYSIS"
                elif bloom_str in ["EVALUATE", "EVALUATION"]: bloom_str = "EVALUATION"
                elif bloom_str in ["CREATE", "CREATION"]: bloom_str = "CREATION"
                
                modes = getattr(q, "supported_answer_modes", None) or ["TEXT"]
                if "VOICE" in modes:
                    modes.remove("VOICE")
                modes.insert(0, "VOICE")
                
                dtos.append(QuestionDTO(
                    question_id=getattr(q, "id", uuid.uuid4()),
                    question_type=getattr(q, "question_type", "MCQ"),
                    difficulty=diff_str,
                    question=getattr(q, "text", ""),
                    options=getattr(q, "mcq_options", []),
                    hint_1=getattr(q, "hint_level_1", ""),
                    hint_2=getattr(q, "hint_level_2", ""),
                    supported_answer_modes=modes,
                    # Note: In the future, we could add selection_reason to the DTO here:
                    # selection_reason=next((v.selection_reasons for v in final_scored_variants if v.question.id == q.id), [])
                ))
            
        return SessionPayload(
            session_id=session_id,
            questions=dtos
        )
