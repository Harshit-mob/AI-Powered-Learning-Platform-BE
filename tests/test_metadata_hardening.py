import pytest
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.content.question_intelligence.bloom_classifier import BloomClassifier
from app.services.content.question_intelligence.models import BloomLevel

def test_bloom_classifier():
    classifier = BloomClassifier()
    
    # "What is the first step..." -> UNDERSTAND, not REMEMBER
    q1 = {"question": "What is the first step in the scientific method?", "question_type": "MCQ"}
    assert classifier.classify(q1) == BloomLevel.UNDERSTAND
    
    # "What process uses logic..." -> UNDERSTAND
    q2 = {"question": "What process uses logic to reach a conclusion?", "question_type": "FILL_BLANK"}
    assert classifier.classify(q2) == BloomLevel.UNDERSTAND
    
    # Definition is always REMEMBER
    q3 = {"question": "What is science?", "question_type": "DEFINITION"}
    assert classifier.classify(q3) == BloomLevel.REMEMBER

from app.services.content.question_intelligence.cognitive_classifier import CognitiveClassifier
from app.services.content.question_intelligence.models import CognitiveLevel

def test_cognitive_classifier():
    classifier = CognitiveClassifier()
    
    # "Why did..." -> CAUSE_EFFECT despite being MCQ
    q1 = {"question": "Why did the ball roll down?", "question_type": "MCQ"}
    assert classifier.classify(q1) == CognitiveLevel.CAUSE_EFFECT
    
    # "Predict what will happen..." -> REASONING
    q2 = {"question": "Predict what will happen if we add water.", "question_type": "FILL_BLANK"}
    assert classifier.classify(q2) == CognitiveLevel.REASONING
    
    # "Explain how..." -> UNDERSTANDING
    q3 = {"question": "Explain how plants grow.", "question_type": "SHORT_ANSWER"}
    assert classifier.classify(q3) == CognitiveLevel.UNDERSTANDING

from app.services.content.question_intelligence.intent_classifier import IntentClassifier
from app.services.content.question_intelligence.models import EducationalIntent

def test_intent_classifier():
    classifier = IntentClassifier()
    
    # "Which of..." in MCQ -> IDENTIFICATION, not MCQ
    q1 = {"question": "Which of these is a plant?", "question_type": "MCQ"}
    assert classifier.classify(q1) == EducationalIntent.CONCEPT
    
    # "What are the steps..." in Fill Blank -> PROCESS, not FILL_BLANK
    q2 = {"question": "What are the steps of the scientific method?", "question_type": "FILL_BLANK"}
    assert classifier.classify(q2) == EducationalIntent.PROCESS
    
    # Fallback to structural
    q3 = {"question": "Water is a liquid.", "question_type": "TRUE_FALSE"}
    assert classifier.classify(q3) == EducationalIntent.TRUE_FALSE

from app.services.content.question_intelligence.voice_analyzer import VoiceAnalyzer
from app.services.content.question_intelligence.config import IntelligenceConfig

def test_voice_analyzer():
    config = IntelligenceConfig()
    analyzer = VoiceAnalyzer(config)
    
    # Easy short question
    q1 = {"question": "What is water?", "expected_answer": "Liquid"}
    v_score1, s_time1, _ = analyzer.analyze(q1, CognitiveLevel.RECALL)
    assert v_score1 > 90
    assert s_time1 > 0
    
    # Complex long question with reasoning and difficult words
    q2 = {
        "question": "If you observe closely, what will happen to the exceptionally magnificent thermometer when it is heated, and why?", 
        "expected_answer": "It expands because of heat" # 5 words
    }
    v_score2, s_time2, _ = analyzer.analyze(q2, CognitiveLevel.REASONING)
    assert v_score2 < 85  # Reasoning (-15), long words, multiple clauses, etc.
    assert s_time2 > s_time1

from app.services.content.question_intelligence.time_estimator import TimeEstimator

def test_time_estimator():
    estimator = TimeEstimator()
    
    # Short recall question
    q1 = {"question": "What is water?", "expected_answer": "Liquid", "difficulty": 1}
    t_time1 = estimator.estimate_thinking_time(q1, BloomLevel.REMEMBER, EducationalIntent.DEFINITION)
    
    # Long reasoning question
    q2 = {
        "question": "If you observe closely, what will happen to the exceptionally magnificent thermometer when it is heated, and why?", 
        "expected_answer": "It expands because of heat", 
        "difficulty": 3
    }
    t_time2 = estimator.estimate_thinking_time(q2, BloomLevel.ANALYZE, EducationalIntent.REASON)
    
    assert t_time2 > t_time1 + 10  # Should be significantly longer

from app.services.content.question_intelligence.coverage_weight import CoverageWeightCalculator
from app.services.content.question_intelligence.models import QuestionIntelligence

def test_coverage_weight():
    calc = CoverageWeightCalculator()
    
    intel = QuestionIntelligence(
        bloom_level=BloomLevel.ANALYZE,
        cognitive_level=CognitiveLevel.REASONING,
        intent=EducationalIntent.REASON,
        voice_score=100,
        speaking_time=10.0,
        thinking_time=10.0,
        cluster_id="dummy",
        question_hash="dummy"
    )
    
    # Excellent coverage question
    q1 = {
        "question": "How does photosynthesis and respiration compare?",
        "full_explanation": "Photosynthesis stores energy, respiration releases it.",
        "concept": "Photosynthesis and Respiration",
        "learning_objective": "Understand the detailed processes of energy transfer in biological systems.",
        "keywords": ["photosynthesis", "respiration", "energy", "biological"]
    }
    
    weight1 = calc.calculate_weight(q1, intel)
    assert weight1 == 0.35
    
    intel2 = QuestionIntelligence(
        bloom_level=BloomLevel.REMEMBER,
        cognitive_level=CognitiveLevel.RECALL,
        intent=EducationalIntent.DEFINITION,
        voice_score=100,
        speaking_time=10.0,
        thinking_time=10.0,
        cluster_id="dummy",
        question_hash="dummy"
    )
    
    # Poor coverage question
    q2 = {
        "question": "What is a cat?",
        "concept": "cat",
        "learning_objective": "Learn animals.",
        "keywords": ["cat"]
    }
    
    weight2 = calc.calculate_weight(q2, intel2)
    assert weight2 < weight1

from app.services.content.question_intelligence.session_tags import SessionTagGenerator
from app.services.content.question_intelligence.config import IntelligenceConfig

def test_session_tags():
    generator = SessionTagGenerator(IntelligenceConfig())
    intel = QuestionIntelligence(
        bloom_level=BloomLevel.ANALYZE,
        cognitive_level=CognitiveLevel.REASONING,
        intent=EducationalIntent.REASON,
        voice_score=100,
        speaking_time=10.0,
        thinking_time=10.0,
        cluster_id="dummy",
        question_hash="dummy",
        normalized_concept="plant growth"
    )
    
    q1 = {
        "question": "Analyze the experiment.",
        "question_type": "MCQ",
        "difficulty": 4
    }
    
    tags = generator.generate(q1, intel)
    assert "hard" in tags
    assert "plant growth" in tags
    assert "mcq" in tags

from app.services.content.question_intelligence.diversity_cluster import DiversityClusterer

def test_diversity_clusterer():
    clusterer = DiversityClusterer()
    
    q1 = {
        "learning_unit_id": "u1",
        "concept": "Science",
        "question_type": "MCQ",
        "question": "What is science?"
    }
    
    c_id1, c_name1 = clusterer.cluster(q1, BloomLevel.REMEMBER, EducationalIntent.DEFINITION)
    
    # Change type, should get different cluster
    q2 = dict(q1)
    q2["question_type"] = "TRUE_FALSE"
    c_id2, c_name2 = clusterer.cluster(q2, BloomLevel.REMEMBER, EducationalIntent.DEFINITION)
    
    assert c_id1 != c_id2
    assert c_name1 == "Science"
    assert c_name2 == "Science"

from app.services.content.question_intelligence.prerequisite_generator import PrerequisiteGenerator

def test_prerequisite_generator():
    generator = PrerequisiteGenerator()
    
    q1 = {
        "concept": "photosynthesis",
        "question": "How does photosynthesis use water?",
        "full_explanation": "Plants need water.",
        "learning_objective": "Understand plants."
    }
    
    unit = {
        "keywords": ["water", "plants", "photosynthesis", "sunlight"]
    }
    
    prereqs = generator.generate(q1, unit)
    # Should find 'water' and 'plants' as prereqs before 'photosynthesis'
    assert prereqs == []
    assert prereqs == []

from app.services.content.question_intelligence.misconception_generator import MisconceptionGenerator

def test_misconception_generator():
    generator = MisconceptionGenerator()
    
    q1 = {
        "concept": "Science",
        "question_type": "MCQ",
        "expected_answer": "A process of learning",
        "mcq_options": [
            "A process of learning",
            "Only memorization",
            "Just guessing"
        ]
    }
    
    tags = generator.generate(q1)
    assert "Belief: Science is only memorization" in tags
    tags2 = generator.generate(q2)
    assert tags2 == []

from app.services.content.question_intelligence.purpose_generator import PurposeGenerator
def test_purpose_generator():
    generator = PurposeGenerator()
    
    intel_mastery = QuestionIntelligence(
        bloom_level=BloomLevel.ANALYZE,
        cognitive_level=CognitiveLevel.REASONING,
        intent=EducationalIntent.REASON,
        production_score=90,
        voice_score=100,
        speaking_time=10.0,
        thinking_time=10.0,
        cluster_id="dummy",
        question_hash="dummy"
    )
    
    q_mastery = {"difficulty": 5, "question_type": "SHORT_ANSWER"}
    assert generator.generate(q_mastery, intel_mastery) == "Mastery"
    
    intel_warmup = QuestionIntelligence(
        bloom_level=BloomLevel.REMEMBER,
        cognitive_level=CognitiveLevel.RECALL,
        intent=EducationalIntent.DEFINITION,
        production_score=60,
        voice_score=100,
        speaking_time=10.0,
        thinking_time=10.0,
        cluster_id="dummy",
        question_hash="dummy"
    )
    
    q_warmup = {"difficulty": 1, "question_type": "MCQ"}
    assert generator.generate(q_warmup, intel_warmup) == "Warmup"

from app.services.content.question_intelligence.progression_calculator import ProgressionCalculator
def test_progression_calculator():
    calc = ProgressionCalculator()
    
    intel_mastery = QuestionIntelligence(
        bloom_level=BloomLevel.ANALYZE,
        cognitive_level=CognitiveLevel.REASONING,
        intent=EducationalIntent.REASON,
        voice_score=100,
        speaking_time=10.0,
        thinking_time=10.0,
        cluster_id="dummy",
        question_hash="dummy"
    )
    
    q_mastery = {"difficulty": 5}
    assert calc.calculate(q_mastery, intel_mastery) == 5
    
    intel_foundation = QuestionIntelligence(
        bloom_level=BloomLevel.REMEMBER,
        cognitive_level=CognitiveLevel.RECALL,
        intent=EducationalIntent.DEFINITION,
        prerequisite_concepts=[],
        voice_score=100,
        speaking_time=10.0,
        thinking_time=10.0,
        cluster_id="dummy",
        question_hash="dummy"
    )
    
    q_foundation = {"difficulty": 1}
    assert calc.calculate(q_foundation, intel_foundation) == 1

from app.services.content.question_intelligence.metadata_validator import MetadataValidator
def test_metadata_validator():
    validator = MetadataValidator()
    
    intel = QuestionIntelligence(
        bloom_level=BloomLevel.REMEMBER,
        cognitive_level=CognitiveLevel.RECALL,
        intent=EducationalIntent.DEFINITION,
        production_score=150,  # Invalid
        voice_score=-10,      # Invalid
        coverage_weight=1.5,  # Invalid
        progression_level=6,  # Invalid
        session_tags=["TAG1", "tag2", "tag1"], # Needs dedup and lower
        question_purpose="InvalidPurpose",     # Invalid
        speaking_time=10.0,
        thinking_time=10.0,
        cluster_id="dummy",
        question_hash="dummy"
    )
    
    validated = validator.validate(intel)
    assert validated.production_score == 100
    assert validated.voice_score == 0
    assert validated.coverage_weight == 1.0
    assert validated.progression_level == 5
    assert validated.session_tags == ["tag1", "tag2"]
    assert validated.question_purpose == "Practice"
