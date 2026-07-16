from typing import Dict, Any, List
from .concept_normalizer import ConceptNormalizer

import os
import json

class PrerequisiteGenerator:
    """
    Deterministically infers prerequisite concepts required to answer the question.
    """
    def __init__(self):
        graph_path = os.path.join(os.path.dirname(__file__), "config", "concept_graph.json")
        try:
            with open(graph_path, "r") as f:
                self.graph = json.load(f)
        except Exception:
            self.graph = {
                "theory": ["hypothesis", "evidence", "testing"],
                "experiment": ["observation", "question"],
                "reasoning": ["observation", "evidence"]
            }
        self.normalizer = ConceptNormalizer()
        
    def generate(self, question: Dict[str, Any], unit: Dict[str, Any]) -> List[str]:
        q_concept = self.normalizer.normalize(question)
        
        prereqs = set()
        concept_lower = str(q_concept).lower()
        deps = self.graph.get("dependencies", {})
        if concept_lower in deps:
            for dep in deps[concept_lower]:
                prereqs.add(dep.title())
                
        intent = str(question.get("intent", "")).lower()
        if intent in self.graph:
            for dep in self.graph[intent]:
                prereqs.add(dep.title())
                
        return sorted(list(prereqs))
