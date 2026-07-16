import pytest
from app.services.content.question_intelligence.time_estimator import TimeEstimator
from app.services.content.question_intelligence.voice_analyzer import VoiceAnalyzer
from app.services.content.question_intelligence.purpose_generator import PurposeGenerator
from app.services.content.question_intelligence.coverage_weight import CoverageWeightCalculator
from app.services.content.question_intelligence.session_tags import SessionTagGenerator
from app.services.content.question_intelligence.data_cleaner import DataCleaner
from app.services.content.question_intelligence.hint_validator import HintValidator
from app.services.content.question_intelligence.answer_validator import AnswerValidator
from app.services.content.question_intelligence.scientific_validator import ScientificValidator
from app.services.content.question_intelligence.metadata_validator import MetadataValidationPipeline
from app.services.content.question_intelligence.prerequisite_generator import PrerequisiteGenerator
from app.services.content.question_intelligence.concept_normalizer import ConceptNormalizer
from app.services.content.question_intelligence.diversity_cluster import DiversityClusterer
from app.services.content.question_intelligence.educational_validator import EducationalValidator
from app.services.content.question_intelligence.models import QuestionIntelligence, BloomLevel, CognitiveLevel, EducationalIntent

class MockConfig:
    def __init__(self):
        self.optimal_voice_score_threshold = 80

def test_time_estimator():
    estimator = TimeEstimator()
    # Difficulty 2 -> buffer 2
    res = estimator.estimate_total_time({"difficulty": 2}, speaking_time=4.5, thinking_time=2.5)
    assert res == 9  # 4.5 + 2.5 + 2 = 9
    # Difficulty 4 -> buffer 3
    res = estimator.estimate_total_time({"difficulty": 4}, speaking_time=5.0, thinking_time=3.0)
    assert res == 11

def test_voice_analyzer():
    analyzer = VoiceAnalyzer(MockConfig())
    # Single word -> base 100
    q = {"question_type": "CONCEPT", "text": "What is it?", "expected_answer": "Science"}
    score, _, _ = analyzer.analyze(q, CognitiveLevel.RECALL)
    assert score >= 95
    
    # Complex explanation -> base 80
    q = {"question_type": "REASONING", "text": "Explain this long process?", "expected_answer": "This is a very long and complex explanation that takes many words to fully describe."}
    score, _, _ = analyzer.analyze(q, CognitiveLevel.REASONING)
    assert score <= 80

def test_purpose_generator():
    gen = PurposeGenerator()
    assert gen.generate({"difficulty": 1, "question_type": "CONCEPT"}, None) == "Warmup"
    assert gen.generate({"difficulty": 4, "question_type": "CONCEPT"}, None) == "Challenge"

def test_coverage_weight():
    calc = CoverageWeightCalculator()
    intel = QuestionIntelligence(
        bloom_level=BloomLevel.REMEMBER, cognitive_level=CognitiveLevel.RECALL,
        intent=EducationalIntent.REASON, voice_score=100, speaking_time=1.0, 
        thinking_time=1.0, cluster_id="1", question_hash="hash"
    )
    # Reason -> 0.40
    res = calc.calculate_weight({"question_type": "REASONING"}, intel)
    assert res == 0.40
    # Concept -> 0.15
    res = calc.calculate_weight({"question_type": "CONCEPT"}, intel)
    assert res == 0.15

def test_session_tags():
    gen = SessionTagGenerator(MockConfig())
    intel = QuestionIntelligence(
        bloom_level=BloomLevel.REMEMBER, cognitive_level=CognitiveLevel.RECALL,
        intent=EducationalIntent.CONCEPT, voice_score=100, speaking_time=1.0, 
        thinking_time=1.0, cluster_id="1", question_hash="hash"
    )
    tags = gen.generate({"difficulty": 1, "question_type": "DEFINITION"}, intel)
    # tags should be easy, warmup, definition, remember, voice_friendly (if score >80)
    assert "easy" in tags
    assert "definition" in tags
    assert "remember" in tags

def test_data_cleaner():
    cleaner = DataCleaner()
    # Test evaluation override
    q = {"question_type": "CONCEPT", "answer_complexity": "SINGLE_WORD"}
    cleaner._clean_evaluation_method(q)
    assert q["evaluation_method"] == "WORD_MATCH"
    
    # Test keyword cleanup (Task 8)
    q = {"keywords": ["Wires", "wires", "Battery ", " bulb"]}
    cleaner._clean_keywords(q)
    assert q["keywords"] == ["battery", "bulb", "wires"]

def test_hint_validator():
    validator = HintValidator()
    q = {"hint_level_1": "starts with letter A", "concept": "science"}
    valid, msg = validator.validate_and_repair(q)
    assert valid is True
    assert "Repaired" in msg
    assert "science" in q["hint_level_1"].lower()

def test_answer_validator():
    validator = AnswerValidator()
    q = {
        "text": "Name a place?",
        "expected_answer": "New York",
        "acceptable_answers": ["everything", "it is new york", "other scientists", "tokyo"]
    }
    validator.validate_and_repair(q)
    acceptable = [a.lower() for a in q["acceptable_answers"]]
    assert "everything" not in acceptable
    assert not any("it is " in a for a in acceptable) # stripped conversational
    assert "tokyo" in acceptable

def test_scientific_validator():
    validator = ScientificValidator()
    # Test repair (Task 4)
    q = {"text": "A theory is proved correct."}
    status, msg = validator.validate(q)
    assert status == "WARNING"
    assert "supported by repeated testing" in q["text"]
    
def test_educational_validator():
    validator = EducationalValidator()
    # Test Task 12 & 13
    q = {"text": "What are wires?", "concept": "Wires"}
    unit = {"learning_objective": "Illustrate troubleshooting"}
    valid, msg = validator.validate(q, unit)
    assert valid is False
    assert "Mismatch" in msg
    
    q = {"text": "How do you do troubleshooting of wires?", "concept": "Wires"}
    valid, msg = validator.validate(q, unit)
    assert valid is True

def test_metadata_validation_pipeline():
    pipeline = MetadataValidationPipeline()
    intel = QuestionIntelligence(
        bloom_level=BloomLevel.REMEMBER, 
        cognitive_level=CognitiveLevel.RECALL,
        intent=EducationalIntent.FACT,
        voice_score=100,
        speaking_time=1.0,
        thinking_time=1.0,
        cluster_id="1",
        question_hash="hash",
        session_tags=["tag"],
        prerequisite_concepts=["Concept"]
    )
    # Valid Question
    q = {
        "question_type": "DEFINITION",
        "full_explanation": "Explained.",
        "expected_answer": "ans",
        "hint_level_1": "Hint",
        "answer_complexity": "SINGLE_WORD",
        "evaluation_method": "WORD_MATCH"
    }
    unit = {"learning_objective": "definition"}
    valid, intel, msg = pipeline.validate(intel, q, unit)
    assert valid is True
    assert intel.metadata_score == 100
    
    # Invalid Question (Bloom mismatch)
    q["question_type"] = "REASONING"
    valid, intel, msg = pipeline.validate(intel, q)
    # Wait, reasoning vs remember is a penalty in my code, not an error!
    assert valid is True
    assert intel.metadata_score < 100

def test_prerequisite_generator():
    gen = PrerequisiteGenerator()
    # Mocking graph for test
    gen.graph = {"dependencies": {"theory": ["hypothesis", "testing"]}}
    q = {"concept": "Theory"}
    prereqs = gen.generate(q, None)
    assert "Hypothesis" in prereqs

def test_concept_normalizer():
    norm = ConceptNormalizer()
    res = norm.normalize({"concept": "Torch Components"})
    assert res == "torch_components"

def test_diversity_cluster():
    clusterer = DiversityClusterer()
    c_id, c_name = clusterer.cluster({"concept": "scientific method", "question_type": "mcq"}, BloomLevel.REMEMBER, EducationalIntent.FACT)
    assert c_name == "Scientific Method - Mcq"
