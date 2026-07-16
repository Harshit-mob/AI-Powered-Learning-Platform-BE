import logging
from typing import Dict, Any, List

from .models import QuestionIntelligence
from .config import IntelligenceConfig
from .bloom_classifier import BloomClassifier
from .cognitive_classifier import CognitiveClassifier
from .intent_classifier import IntentClassifier
from .voice_analyzer import VoiceAnalyzer
from .question_hash import QuestionHasher
from .diversity_cluster import DiversityClusterer
from .session_tags import SessionTagGenerator
from .production_ranker import ProductionRanker
from .coverage_matrix import CoverageMatrix
from .metadata_scorer import MetadataScorer
from .coverage_weight import CoverageWeightCalculator
from .concept_normalizer import ConceptNormalizer
from .voice_keyword_generator import VoiceKeywordGenerator
from .time_estimator import TimeEstimator
from .answer_mode_validator import AnswerModeValidator
from .purpose_generator import PurposeGenerator
from .progression_calculator import ProgressionCalculator
from .prerequisite_generator import PrerequisiteGenerator
from .misconception_generator import MisconceptionGenerator
from .metadata_validator import MetadataValidationPipeline
from .data_cleaner import DataCleaner
import os
import json

logger = logging.getLogger(__name__)

class IntelligenceEngine:
    """
    Master Orchestrator for the Question Intelligence Engine.
    Enriches validated questions with deep deterministic metadata.
    """
    def __init__(self):
        self.config = IntelligenceConfig()
        
        self.bloom_classifier = BloomClassifier()
        self.cognitive_classifier = CognitiveClassifier()
        self.intent_classifier = IntentClassifier()
        self.voice_analyzer = VoiceAnalyzer(self.config)
        self.hasher = QuestionHasher()
        self.clusterer = DiversityClusterer()
        self.tag_generator = SessionTagGenerator(self.config)
        self.ranker = ProductionRanker(self.config)
        self.coverage_matrix = CoverageMatrix()
        self.metadata_scorer = MetadataScorer()
        self.weight_calculator = CoverageWeightCalculator()
        self.concept_normalizer = ConceptNormalizer()
        self.voice_keyword_generator = VoiceKeywordGenerator()
        self.time_estimator = TimeEstimator()
        self.mode_validator = AnswerModeValidator()
        self.purpose_generator = PurposeGenerator()
        self.progression_calculator = ProgressionCalculator()
        self.prereq_generator = PrerequisiteGenerator()
        self.misconception_generator = MisconceptionGenerator()
        self.validator = MetadataValidationPipeline()
        self.cleaner = DataCleaner()
        
        # Load dependency graph
        self.dependency_graph = {}
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
            dep_path = os.path.join(base_dir, "data", "dependency_graph.json")
            if os.path.exists(dep_path):
                with open(dep_path, "r") as f:
                    self.dependency_graph = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load dependency graph: {e}")

    def enrich_question(self, question: Dict[str, Any], quality_score: int, unit: Dict[str, Any] = None) -> QuestionIntelligence:
        # 0. Clean data fields
        self.cleaner.clean(question)
        
        # 1. Base Classifications
        bloom = self.bloom_classifier.classify(question)
        cognitive = self.cognitive_classifier.classify(question, bloom.value if bloom else None)
        intent = self.intent_classifier.classify(question)
        
        # 2. Voice & Time Analytics
        v_score, s_time, _ = self.voice_analyzer.analyze(question, cognitive)
        
        # Override with dynamic deterministic time calculations
        t_time = self.time_estimator.estimate_thinking_time(question, bloom, intent)
        est_time = int(t_time + s_time + 1)
        
        # 3. Hash & Clustering
        q_hash = self.hasher.generate_hash(question, intent)
        cluster_id, cluster_name = self.clusterer.cluster(question, bloom, intent)
        
        # Build partial intelligence object
        intel = QuestionIntelligence(
            bloom_level=bloom,
            cognitive_level=cognitive,
            intent=intent,
            voice_score=v_score,
            speaking_time=s_time,
            thinking_time=t_time,
            cluster_id=cluster_id,
            cluster_name=cluster_name,
            question_hash=q_hash,
            normalized_concept=self.concept_normalizer.normalize(question),
            voice_expected_keywords=self.voice_keyword_generator.generate(question),
            supported_answer_modes=self.mode_validator.validate(question),
            prerequisite_concepts=self.prereq_generator.generate(question, unit),
            misconception_tags=self.misconception_generator.generate(question),
            estimated_time=est_time
        )
        
        # Override prerequisites with deterministic graph if available
        concept_key = intel.normalized_concept.lower()
        if concept_key in self.dependency_graph:
            intel.prerequisite_concepts = self.dependency_graph[concept_key].get("requires", [])
            # We could also attach builds_into/related to a new field, but sticking to existing DB schema so we just use prereqs.
        
        # 4. Tags, Ranking, Weight, Purpose, Progression
        intel.coverage_weight = self.weight_calculator.calculate_weight(question, intel)
        intel.session_tags = self.tag_generator.generate(question, intel)
        intel.production_score = self.ranker.rank(question, quality_score, intel)
        
        # Human Review Mode Mapping
        # Note: Since DB doesn't have review_status, we store it in session_tags or purpose as metadata
        if intel.production_score >= 95:
            intel.session_tags.append("STATUS: Auto Approved")
        elif intel.production_score >= 90:
            intel.session_tags.append("STATUS: Needs Review")
        else:
            intel.session_tags.append("STATUS: Rejected")
            
        intel.question_purpose = self.purpose_generator.generate(question, intel)
        intel.progression_level = self.progression_calculator.calculate(question, intel)
        
        # 6. Validation step
        # Note that the pipeline calculates the final score inside, so we don't need MetadataScorer
        is_valid, intel, warns = self.validator.validate(intel, question, unit)
        if not is_valid:
            raise ValueError(f"Metadata Validation Failed: {warns}")
            
        return intel
        
    def generate_coverage_matrix(self, learning_unit: Dict[str, Any], questions: List[Dict[str, Any]], intelligence_list: List[QuestionIntelligence]) -> Dict[str, Any]:
        """
        Delegates generation of the advanced learning unit coverage analytics.
        """
        return self.coverage_matrix.generate(learning_unit, questions, intelligence_list)
