import logging
import json
import re
import time
from typing import List, Dict, Any, Tuple
from pydantic import BaseModel, ValidationError

from app.content.ai_provider import AIProviderInterface, PromptBuilder
from app.content.question_validator import SchemaValidator
from app.models.quiz import Question
from sqlalchemy.dialects.postgresql import insert

from app.content.quality_engine.validation_models import QualityConfig, ValidationSeverity
from app.content.quality_engine.duplicate_analyzer import DuplicateAnalyzer
from app.content.quality_engine.coverage_analyzer import CoverageAnalyzer
from app.content.quality_engine.question_quality_analyzer import QuestionQualityAnalyzer
from app.content.quality_engine.question_validator import QuestionValidator as QualityEngineValidator
from app.content.quality_engine.question_statistics import QuestionStatistics
from app.content.quality_engine.generation_reporter import GenerationReporter
from app.content.question_intelligence.intelligence_engine import IntelligenceEngine

logger = logging.getLogger(__name__)

# --- Structured JSON Schemas ---
class ParsedQuestion(BaseModel):
    question: str
    question_type: str
    concept: str
    expected_answer: str
    acceptable_answers: List[str] = []
    evaluation_method: str
    hint_level_1: str
    hint_level_2: str
    full_explanation: str
    difficulty: int
    keywords: List[str] = []
    learning_unit_id: str
    learning_objective: str
    source_pages: List[int] = []
    estimated_answer_time: int = 5
    supported_answer_modes: List[str] = []
    answer_complexity: str = "WORD"
    mcq_options: List[str] = []
    correct_option: str = ""
    voice_expected_keywords: List[str] = []
    
    # --- Intelligence Engine Metadata ---
    question_hash: str = ""
    bloom_level: str = ""
    cognitive_level: str = ""
    intent: str = ""
    voice_score: int = 0
    speaking_time: float = 0.0
    thinking_time: float = 0.0
    cluster_id: str = ""
    session_tags: List[str] = []
    production_score: int = 0
    coverage_weight: float = 0.0
    metadata_score: int = 0
    estimated_time: int = 5
    normalized_concept: str = ""
    cluster_name: str = ""
    question_purpose: str = "Teaching"
    progression_level: int = 1
    prerequisite_concepts: List[str] = []
    misconception_tags: List[str] = []

class QuestionGenerationService:
    def __init__(self, ai_provider: AIProviderInterface):
        self.ai_provider = ai_provider
        self.prompt_builder = PromptBuilder()
        self.schema_validator = SchemaValidator()
        
        # Initialize Quality Engine
        self.config = QualityConfig()
        self.duplicate_analyzer = DuplicateAnalyzer(self.config)
        self.coverage_analyzer = CoverageAnalyzer()
        self.quality_analyzer = QuestionQualityAnalyzer(self.config)
        self.quality_engine = QualityEngineValidator(self.config, self.duplicate_analyzer, self.quality_analyzer)
        self.reporter = GenerationReporter()
        self.statistics = QuestionStatistics()
        
        self.intelligence_engine = IntelligenceEngine()

    def build_question_generation_payload(
        self, 
        subject: str, 
        grade: int, 
        board: str, 
        chapter: str, 
        topic: str, 
        sub_topic: str, 
        learning_units: List[Dict[str, Any]]
    ) -> str:
        clean_units = []
        for unit in learning_units:
            clean_unit = {
                "learning_unit_id": str(unit.get("id", unit.get("learning_unit_id", ""))),
                "title": unit.get("title", ""),
                "learning_objective": unit.get("learning_objective", ""),
                "content": unit.get("content", ""),
                "keywords": unit.get("keywords", []),
                "difficulty": unit.get("difficulty", 2),
                "source_pages": unit.get("source_pages", [])
            }
            clean_units.append(clean_unit)
            
        payload = {
            "subject": subject,
            "grade": grade,
            "board": board,
            "chapter": chapter,
            "topic": topic,
            "sub_topic": sub_topic,
            "learning_units": clean_units,
            "STRICT_PIPELINE_CONSTRAINTS": {
                "scenario_questions": "AT LEAST 30% of non-definition questions MUST be scenario-based involving a person (e.g. 'Riya notices that...').",
                "child_friendly_language": "Target audience is CBSE Grade 6. Remove unnecessary academic wording. Prefer 'look carefully' instead of 'systematically observe'.",
                "explanation_format": "Explanations MUST be written as a single child-friendly, natural conversational paragraph of max 70 words. It should state what the correct answer is, why it is correct (using 'because' or 'since'), briefly mention why other answers are wrong, and include one everyday example. DO NOT use lists or numbered parts (like 1), 2), etc.).",
                "acceptable_answers": "Generate natural spoken variants (e.g. 'The science', 'It is science') rather than substituting concepts.",
                "hint_generation": "Hints must progressively reveal the answer structurally. NEVER generate generic hints like 'Think carefully', 'Consider the concept', or 'Practical scenario'.",
                "adaptive_generation": "For EVERY concept tested, generate exactly 8 variants as a Concept Cluster: 2 Easier, 4 Standard, 2 Harder variants. Ensure they target the exact same concept but use distinct sentences, phrasing, and scenarios."
            }
        }
        return json.dumps(payload, indent=2)

    def parse_question_response(self, raw_response: str) -> List[ParsedQuestion]:
        parsed_questions = []
        match = re.search(r'\[.*\]', raw_response, re.DOTALL)
        if not match: return []
        json_str = match.group(0)
        try:
            raw_list = json.loads(json_str)
        except json.JSONDecodeError: return []
        if not isinstance(raw_list, list): return []
        
        for item in raw_list:
            # Clean up unclosed parentheses in TRUE_FALSE questions
            if item.get("question_type") == "TRUE_FALSE":
                correct = item.get("correct_option")
                if isinstance(correct, str):
                    c_lower = correct.lower()
                    if "हाँ" in correct or "true" in c_lower:
                        if "नहीं" not in correct and "false" not in c_lower:
                            item["correct_option"] = "हाँ (True)"
                    elif "नहीं" in correct or "false" in c_lower:
                        if "हाँ" not in correct and "true" not in c_lower:
                            item["correct_option"] = "नहीं (False)"
                            
                # expected_answer must exactly match correct_option
                item["expected_answer"] = item["correct_option"]

                acc_ans = item.get("acceptable_answers")
                if isinstance(acc_ans, list):
                    cleaned_acc = []
                    for val in acc_ans:
                        if isinstance(val, str):
                            # Replace (true or (false with closed brackets
                            val = re.sub(r'\(true\b(?!\))', '(true)', val, flags=re.IGNORECASE)
                            val = re.sub(r'\(false\b(?!\))', '(false)', val, flags=re.IGNORECASE)
                        cleaned_acc.append(val)
                    item["acceptable_answers"] = cleaned_acc

            try:
                pq = ParsedQuestion(**item)
                parsed_questions.append(pq)
            except ValidationError as e:
                logger.warning(f"Pydantic schema mismatch: {e}")
                
        return parsed_questions

    def _process_single_unit(self, system_prompt: str, payload_str: str, unit_dict: Dict[str, Any]) -> Tuple[List[ParsedQuestion], int]:
        unit_id = unit_dict.get("id", unit_dict.get("learning_unit_id", ""))
        
        # 1. AI Generation
        ai_start = time.time()
        try:
            raw_text = self.ai_provider.generate_text(system_prompt=system_prompt, content=payload_str)
        except Exception as e:
            logger.error(f"AI Generation Failed: {e}")
            return [], 0
            
        # 2. Parsing
        parsed_list = self.parse_question_response(raw_text)
        
        # Difficulty Progression Sorting & Validation
        # Assign a basic progression score based on Bloom / Difficulty
        def get_progression(q: ParsedQuestion) -> int:
            b = str(q.bloom_level).upper() if q.bloom_level else ""
            t = str(q.question_type).upper()
            d = q.difficulty
            
            if t == "DEFINITION": return 1
            if b == "REMEMBER" or t == "RECALL": return max(1, d)
            if b == "UNDERSTAND": return max(2, d)
            if b == "APPLY": return max(3, d)
            if b in ["ANALYZE", "EVALUATE"]: return max(4, d)
            if b == "CREATE" or d >= 5: return 5
            return d
            
        parsed_list.sort(key=get_progression)
        
        # Gap validation: Reject batch if there's a huge difficulty gap
        if parsed_list:
            levels = [get_progression(q) for q in parsed_list]
            for i in range(1, len(levels)):
                if levels[i] - levels[i-1] > 2:
                    logger.error(f"Sudden difficulty jump detected: Level {levels[i-1]} -> Level {levels[i]}. Rejecting batch.")
                    return [], len(parsed_list)
        
        validated_questions = []
        total_failures = 0
        
        unit_diversity_count = 0
        
        lu_stats = {
            "Generated": len(parsed_list),
            "Accepted": 0,
            "Rejected": 0,
            "Duplicates": 0,
            "Warnings": 0,
            "Voice_Scores": [],
            "Quality_Scores": [],
            "rejections_reasons": {}
        }
        
        for q in parsed_list:
            q_dict = q.model_dump()
            
            # Structural check
            if not self.schema_validator.validate(q_dict):
                total_failures += 1
                lu_stats["Rejected"] += 1
                continue
                
            # Quality Engine Validation
            val_result = self.quality_engine.validate(q_dict, unit_diversity_count)
            if val_result.valid:
                try:
                    intel = self.intelligence_engine.enrich_question(q_dict, val_result.quality_score, unit_dict)
                except ValueError as e:
                    logger.warning(f"Metadata rejected: {e}")
                    total_failures += 1
                    lu_stats["Rejected"] += 1
                    continue
                    
                # Apply deterministic overrides from intelligence engine
                q.question_hash = intel.question_hash
                q.bloom_level = intel.bloom_level.value
                q.cognitive_level = intel.cognitive_level.value
                q.intent = intel.intent.value
                q.voice_score = intel.voice_score
                q.speaking_time = intel.speaking_time
                q.thinking_time = intel.thinking_time
                q.cluster_id = intel.cluster_id
                q.session_tags = intel.session_tags
                q.production_score = intel.production_score
                q.coverage_weight = intel.coverage_weight
                q.metadata_score = intel.metadata_score
                q.estimated_time = intel.estimated_time
                q.normalized_concept = intel.normalized_concept
                q.cluster_name = intel.cluster_name
                q.question_purpose = intel.question_purpose
                q.progression_level = intel.progression_level
                q.prerequisite_concepts = intel.prerequisite_concepts
                q.misconception_tags = intel.misconception_tags
                
                # Sync any structural repairs made by validators
                q.expected_answer = q_dict.get("expected_answer", q.expected_answer)
                q.acceptable_answers = q_dict.get("acceptable_answers", q.acceptable_answers)
                q.hint_level_1 = q_dict.get("hint_level_1", q.hint_level_1)
                q.hint_level_2 = q_dict.get("hint_level_2", q.hint_level_2)
                q.full_explanation = q_dict.get("full_explanation", q.full_explanation)
                q.keywords = q_dict.get("keywords", q.keywords)
                q.question = q_dict.get("question", q.question)
                q.evaluation_method = q_dict.get("evaluation_method", q.evaluation_method)
                
                validated_questions.append(q)
                unit_diversity_count += 1
                lu_stats["Accepted"] += 1
                lu_stats["Quality_Scores"].append(val_result.quality_score)
                lu_stats["Voice_Scores"].append(intel.voice_score)
                
                self.statistics.add_question(q_dict)
            else:
                total_failures += 1
                lu_stats["Rejected"] += 1
                
                for issue in val_result.issues:
                    if issue.severity == ValidationSeverity.CRITICAL:
                        if issue.type == "DUPLICATE": lu_stats["Duplicates"] += 1
                        lu_stats["rejections_reasons"][issue.type] = lu_stats["rejections_reasons"].get(issue.type, 0) + 1
                        
            # Track warnings
            for issue in val_result.issues:
                if issue.severity == ValidationSeverity.WARNING:
                    lu_stats["Warnings"] += 1
                    
        # Coverage Analysis
        accepted_dicts = [q.model_dump() for q in validated_questions]
        cov_pct, _, _, dist, is_balanced = self.coverage_analyzer.analyze(unit_dict, accepted_dicts)
        
        # If deeply unbalanced, we should flag it (or reject the batch). 
        # For now, we will log a warning and let the reporter handle it, or reject if we strictly enforce.
        if not is_balanced and len(validated_questions) > 5:
            logger.warning(f"Unit {unit_id} has unbalanced question distribution: {dist}")
            # If we enforce strict rejection of the batch:
            # validated_questions = []
            # total_failures += len(accepted_dicts)
        
        avg_voice = sum(lu_stats["Voice_Scores"]) / len(lu_stats["Voice_Scores"]) if lu_stats["Voice_Scores"] else 0
        avg_qual = sum(lu_stats["Quality_Scores"]) / len(lu_stats["Quality_Scores"]) if lu_stats["Quality_Scores"] else 0
        
        self.reporter.record_lu_stats(unit_id, unit_dict.get("title", "Unknown"), {
            "Generated": lu_stats["Generated"],
            "Accepted": len(validated_questions), # Update in case we cleared it
            "Rejected": lu_stats["Rejected"],
            "Duplicates": lu_stats["Duplicates"],
            "Warnings": lu_stats["Warnings"],
            "Coverage": cov_pct,
            "Quality": avg_qual,
            "Voice": avg_voice,
            "rejections_reasons": lu_stats["rejections_reasons"],
            "distribution": dist,
            "is_balanced": is_balanced
        })
        
        print(self.reporter.generate_lu_report(unit_id))
        
        return validated_questions, total_failures

    def generate_question_bank(
        self, subject: str, grade: int, board: str, chapter: str, topic: str, sub_topic: str, learning_units: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        start_time = time.time()
        system_prompt = self.prompt_builder.build("question_generator.md")
        
        if subject.lower() in ("hindi", "gujarati"):
            lang_name = "Hindi" if subject.lower() == "hindi" else "Gujarati"
            tf_options = '["हाँ (True)", "नहीं (False)"]' if subject.lower() == "hindi" else '["સાચું (True)", "ખોટું (False)"]'
            system_prompt += (
                f"\n\n--- {lang_name.upper()} COMPREHENSIVE GENERATION RULE ---\n"
                f"IMPORTANT: Since the subject is {lang_name}, you MUST generate ONLY MCQ and TRUE_FALSE question types. "
                "No other question types are allowed. "
                "For MCQ questions, include 'mcq_options' (exactly 4 options) and 'correct_option'.\n"
                f"For TRUE_FALSE questions, you MUST include 'mcq_options' with exactly 2 options: {tf_options}, and set both 'correct_option' and 'expected_answer' to exactly match one of these two options.\n"
                f"GRAMMAR PRIORITY: Because this is a language subject ({lang_name}), GRAMMAR IS CRITICAL. "
                "Ensure at least 40% of the generated questions directly test grammar, vocabulary, case markers (कारक/विभक्ति), synonyms/antonyms (समानार्थी/विरोधी), prefixes/suffixes, and sentence correction from the chapter text and chapter-end exercises.\n"
                f"For {lang_name}, you MUST generate three types of content questions:\n"
                "1. Exact textbook exercise questions: Generate questions using the exact sentences, terms, and options from the textbook exercises verbatim (do not alter them).\n"
                "2. Parallel practice questions: Generate new, simple practice questions testing the same grammatical concepts (like noun types, case markers) or vocabulary terms using other simple, direct sentences and words from the story text.\n"
                "3. Simple Story Recall (Reading Comprehension): For units covering the story text, generate simple, direct recall questions about the main events, characters, and settings. All story recall questions MUST be simple, direct factual recall of the text, and must not use complex grammar, figures of speech, or abstract analysis. Keep them very simple and accessible for Grade 6 students.\n"
                "CRITICAL: NEVER alter or hallucinate the name of the chapter, story, characters, or key concepts in the questions, options, or explanations (e.g., do NOT change 'सोनकंठी गौरैया' to 'सोनकंठ कबूतर' or similar). Always use the exact terminology from the chapter content verbatim.\n"
                "QUANTITY & COVERAGE: Generate exactly 15-20 questions in total for this learning unit. Ensure full coverage of all sub-topics. Focus heavily on textbook end-of-chapter exercises (verbatim) and grammar practice (synonyms, antonyms, noun types, case markers/कारक, suffixes/प्रत्यय) using simple story sentences."
            )
        else:
            grammar_note = ""
            if subject.lower() == "english":
                grammar_note = (
                    "GRAMMAR PRIORITY: Since this is English, GRAMMAR IS CRITICAL. "
                    "Ensure at least 50% of the generated questions test English grammar and vocabulary. "
                    "For EACH learning unit, you MUST generate grammar-focused questions (MCQ, FILL_BLANK, TRUE_FALSE, or RECALL) "
                    "testing the following 6 core topics using the sentences, phrases, and vocabulary from the current learning unit:\n"
                    "1. Countable and Uncountable Nouns\n"
                    "2. Pronouns (Personal, Possessive, and Reflexive)\n"
                    "3. Vocabulary\n"
                    "4. Antonyms and Synonyms\n"
                    "5. Subject and Predicate\n"
                    "6. Simple and Continuous tenses\n"
                    "Even if the learning unit is about story comprehension, extract sentences from it and generate questions asking the student to identify pronouns, tenses, subject/predicate, countable/uncountable nouns, or synonyms/antonyms in those sentences.\n"
                )
            
            science_note = ""
            if subject.lower() in ["science", "social science"]:
                science_note = (
                    f"{subject.upper()} GENERATION RULES:\n"
                    f"1. ONLY CONTENT-BASED QUESTIONS: Do NOT generate any grammar, vocabulary, or language-based questions. All questions must test core {subject} concepts, terms, facts, timelines, or observations from the text.\n"
                    "2. STRICT QUESTION TYPE RESTRICTION: You MUST generate ONLY the following question types: MCQ, TRUE_FALSE, FILL_BLANK, and RECALL (Short Answer). Avoid any other question types. Do NOT generate long answer questions. For RECALL (Short Answer) and FILL_BLANK, the 'expected_answer' MUST be extremely concise, consisting of exactly 1 to 2 words (maximum 3 words). Never use full sentences or long phrases as answers. Keep them highly voice-friendly.\n"
                    "3. NO REPETITION / DUPLICATE TYPES: Do NOT generate the same question statement across multiple types (e.g. do not ask the same question statement as both True/False and MCQ). Each question must be completely distinct.\n"
                    "4. TEXTBOOK EXERCISE FOCUS: Ensure all textbook chapter-end exercises and questions are represented verbatim.\n"
                    "5. COMPREHENSIVE ACCEPTABLE ANSWERS: Ensure 'acceptable_answers' includes all likely 1-to-2 word correct variations, natural language short phrases, synonyms, and key terminology combinations that a student might say to answer the question correctly.\n"
                )
            
            system_prompt += (
                f"\n\n--- {subject.upper()} COMPREHENSIVE GENERATION RULE ---\n"
                "IMPORTANT: You MUST generate a comprehensive mix of different question types: MCQ, TRUE_FALSE, FILL_BLANK, and RECALL (Short Answer) "
                "covering the ENTIRE chapter content (prioritizing the exercises, questions, and assignments at the end of the textbook chapter).\n"
                f"{grammar_note}"
                f"{science_note}"
                "Generate ALL of the following question types for each Learning Unit:\n"
                "1. Textbook Exercises (MCQ / TRUE_FALSE / FILL_BLANK / RECALL): Verbatim representation of questions from the chapter-end exercises.\n"
                "2. Parallel Practice (MCQ / TRUE_FALSE / FILL_BLANK): For every concept, generate 4-6 additional practice questions using new simple sentences.\n"
                "For MCQ questions, you MUST include 'mcq_options' (exactly 4 options) and 'correct_option'.\n"
                "For TRUE_FALSE questions, you MUST include 'mcq_options' with exactly 2 options: [\"True\", \"False\"], and set both 'correct_option' and 'expected_answer' to match one of these two options exactly.\n"
                "QUANTITY & COVERAGE: Generate exactly 15-20 questions in total for this learning unit. Ensure full coverage of all concepts. Focus heavily on textbook exercises (verbatim) and content practice."
            )
        
        all_validated = []
        total_fail = 0
        total_gen = 0
        
        for idx, unit in enumerate(learning_units, 1):

            payload_str = self.build_question_generation_payload(subject, grade, board, chapter, topic, sub_topic, [unit])
            validated, failures = self._process_single_unit(system_prompt, payload_str, unit)
            
            all_validated.extend(validated)
            total_fail += failures
            total_gen += (len(validated) + failures)
            
        # --- Batch Normalization of Coverage Weights ---
        # Group questions by learning_objective
        from collections import defaultdict
        lo_groups = defaultdict(list)
        for q in all_validated:
            lo_groups[q.learning_objective].append(q)
            
        for lo, qs in lo_groups.items():
            total_weight = sum(q.coverage_weight for q in qs)
            if total_weight > 0:
                current_sum = 0.0
                for i, q in enumerate(qs):
                    if i == len(qs) - 1:
                        # Give the remainder to the last item to guarantee sum=1.000
                        q.coverage_weight = round(1.0 - current_sum, 3)
                    else:
                        val = round(q.coverage_weight / total_weight, 3)
                        q.coverage_weight = val
                        current_sum += val
            else:
                # Fallback if all weights are 0 (shouldn't happen)
                fallback = round(1.0 / len(qs), 3)
                current_sum = 0.0
                for i, q in enumerate(qs):
                    if i == len(qs) - 1:
                        q.coverage_weight = round(1.0 - current_sum, 3)
                    else:
                        q.coverage_weight = fallback
                        current_sum += fallback
                    
        execution_time = time.time() - start_time
        chapter_title = f"{chapter} - {topic} - {sub_topic}"
        chapter_summary = self.reporter.generate_chapter_report(chapter_title, execution_time)
        
        return {
            "execution_time_seconds": execution_time,
            "learning_units_processed": len(learning_units),
            "total_generated": total_gen,
            "total_validated": len(all_validated),
            "total_failures_or_dupes": total_fail,
            "questions": all_validated,
            "quality_report": chapter_summary
        }

    def save_question_bank(self, validated_questions: List[ParsedQuestion], db_session, question_bank_id: str = None) -> int:
        saved_count = 0
        for pq in validated_questions:
            try:
                merged_keywords = list(set(pq.keywords + pq.voice_expected_keywords))
                
                values = {
                    "learning_unit_id": pq.learning_unit_id,
                    "question_type": pq.question_type,
                    "concept": pq.concept,
                    "text": pq.question,
                    "mcq_options": pq.mcq_options,
                    "correct_option": pq.correct_option,
                    "answer_complexity": pq.answer_complexity,
                    "evaluation_method": pq.evaluation_method,
                    "learning_objective": pq.learning_objective,
                    "keywords": merged_keywords,
                    "difficulty": pq.difficulty,
                    "estimated_time": pq.estimated_time,
                    "hint_level_1": pq.hint_level_1,
                    "hint_level_2": pq.hint_level_2,
                    "full_explanation": pq.full_explanation,
                    "source_pages": pq.source_pages,
                    "supported_answer_modes": pq.supported_answer_modes,
                    "expected_answer": pq.expected_answer,
                    "acceptable_answers": pq.acceptable_answers,
                    "question_hash": pq.question_hash,
                    "bloom_level": pq.bloom_level,
                    "cognitive_level": pq.cognitive_level,
                    "intent": pq.intent,
                    "voice_score": pq.voice_score,
                    "speaking_time": pq.speaking_time,
                    "thinking_time": pq.thinking_time,
                    "cluster_id": pq.cluster_id,
                    "session_tags": pq.session_tags,
                    "production_score": pq.production_score,
                    "coverage_weight": pq.coverage_weight,
                    "metadata_score": pq.metadata_score,
                    "normalized_concept": pq.normalized_concept,
                    "cluster_name": pq.cluster_name,
                    "question_purpose": pq.question_purpose,
                    "progression_level": pq.progression_level,
                    "prerequisite_concepts": pq.prerequisite_concepts,
                    "misconception_tags": pq.misconception_tags,
                    "question_bank_id": question_bank_id
                }
                
                stmt = insert(Question).values(**values)
                
                # Perform UPSERT based on unique question_hash
                update_dict = {
                    c.name: c for c in stmt.excluded 
                    if not c.primary_key and c.name != 'question_hash'
                }
                
                stmt = stmt.on_conflict_do_update(
                    index_elements=['question_hash'],
                    set_=update_dict
                )
                
                db_session.execute(stmt)
                db_session.commit()
                saved_count += 1
            except Exception as e:
                db_session.rollback()
                logger.error(f"Database Mapping Failed for question {pq.question_hash}: {e}")
                
        return saved_count
