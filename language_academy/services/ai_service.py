import json
import requests
from django.conf import settings
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class AIService:

    OLLAMA_URL = getattr(settings, 'OLLAMA_URL', 'http://localhost:11434')
    MODEL = getattr(settings, 'OLLAMA_MODEL', 'qwen:3-4b')

    @classmethod
    def evaluate_speaking(cls, prompt: str, user_response: str) -> Dict[str, Any]:
        system_prompt = """You are an English language evaluator for A1-B1 level learners.
        Evaluate the user's speaking response and return ONLY valid JSON in this exact format:
        {
            "acceptable": true/false,
            "pronunciation_score": 0-10,
            "fluency_score": 0-10,
            "grammar_score": 0-10,
            "vocabulary_score": 0-10,
            "overall_score": 0-10,
            "corrections": [
                {
                    "original": "incorrect phrase",
                    "corrected": "correct phrase",
                    "explanation": "brief explanation"
                }
            ],
            "positive_feedback": "what they did well",
            "improvement_suggestions": "how to improve"
        }"""

        user_prompt = f"""Prompt: {prompt}
        User's response: {user_response}

        Evaluate this response for an A1-B1 level English learner."""

        return cls._call_ollama(system_prompt, user_prompt)

    @classmethod
    def evaluate_writing(cls, prompt: str, user_response: str) -> Dict[str, Any]:
        system_prompt = """You are an English language evaluator for A1-B1 level learners.
        Evaluate the user's writing and return ONLY valid JSON in this exact format:
        {
            "acceptable": true/false,
            "grammar_score": 0-10,
            "vocabulary_score": 0-10,
            "coherence_score": 0-10,
            "overall_score": 0-10,
            "corrections": [
                {
                    "original": "incorrect text",
                    "corrected": "corrected text",
                    "error_type": "grammar/spelling/vocabulary",
                    "explanation": "brief explanation"
                }
            ],
            "better_examples": [
                "example of better phrasing"
            ],
            "positive_feedback": "what they did well",
            "areas_for_improvement": ["area1", "area2"]
        }"""

        user_prompt = f"""Writing Prompt: {prompt}
        User's submission: {user_response}

        Evaluate this writing for an A1-B1 level English learner."""

        return cls._call_ollama(system_prompt, user_prompt)

    @classmethod
    def correct_grammar(cls, text: str) -> Dict[str, Any]:
        system_prompt = """You are an English grammar expert.
        Return ONLY valid JSON in this format:
        {
            "has_errors": true/false,
            "corrected_text": "fully corrected text",
            "errors": [
                {
                    "original": "error text",
                    "correction": "correction",
                    "rule": "grammar rule broken",
                    "suggestion": "how to avoid this error"
                }
            ],
            "confidence_score": 0-10
        }"""

        user_prompt = f"Correct the grammar in this text: {text}"
        return cls._call_ollama(system_prompt, user_prompt)

    @classmethod
    def generate_vocabulary_suggestions(cls, user_level: str, weak_categories: list) -> Dict[str, Any]:
        system_prompt = """You are a vocabulary expert for English learners.
        Return ONLY valid JSON in this format:
        {
            "suggested_words": [
                {
                    "word": "example",
                    "reason": "why this word is recommended",
                    "difficulty": "A1/A2/B1",
                    "category": "category name",
                    "example_sentence": "sentence using the word"
                }
            ]
        }"""

        user_prompt = f"""User's English level: {user_level}
        Weak categories: {', '.join(weak_categories)}

        Suggest 5 vocabulary words to help improve."""

        return cls._call_ollama(system_prompt, user_prompt)

    @classmethod
    def generate_learning_analytics(cls, user_data: Dict) -> Dict[str, Any]:
        system_prompt = """You are a learning analytics expert.
        Return ONLY valid JSON in this format:
        {
            "weak_areas": ["area1", "area2"],
            "recommended_focus": "primary recommendation",
            "study_strategy": "specific study advice",
            "predicted_readiness": {
                "A1_completion": "percentage",
                "A2_completion": "percentage",
                "B1_readiness": "percentage"
            },
            "next_milestone_estimate_days": 7
        }"""

        user_prompt = f"""Analyze this learner's data and provide recommendations:
        {json.dumps(user_data, indent=2)}"""

        return cls._call_ollama(system_prompt, user_prompt)

    @classmethod
    def _call_ollama(cls, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        try:
            response = requests.post(
                f"{cls.OLLAMA_URL}/api/generate",
                json={
                    "model": cls.MODEL,
                    "system": system_prompt,
                    "prompt": user_prompt,
                    "stream": False,
                    "format": "json"
                },
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()

                content = result.get('response', '{}')

                if '```json' in content:
                    content = content.split('```json')[1].split('```')[0]
                elif '```' in content:
                    content = content.split('```')[1].split('```')[0]

                return json.loads(content)
            else:
                logger.error(f"Ollama API error: {response.status_code}")
                return cls._get_default_response()

        except Exception as e:
            logger.error(f"Ollama call failed: {str(e)}")
            return cls._get_default_response()

    @staticmethod
    def _get_default_response() -> Dict[str, Any]:
        return {
            "acceptable": True,
            "overall_score": 7,
            "corrections": [],
            "positive_feedback": "Good effort! Keep practicing.",
            "improvement_suggestions": "Continue studying regularly."
        }
