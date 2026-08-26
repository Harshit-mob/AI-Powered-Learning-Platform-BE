import os
from dotenv import load_dotenv
load_dotenv()

import time
import json
import logging
import re
from pathlib import Path
from typing import Type, TypeVar, Protocol, List, Any, Callable
from pydantic import BaseModel
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)

class PromptBuilder:
    def __init__(self, prompts_dir: str = None):
        if prompts_dir is None:
            # Default to app/prompts/
            self.prompts_dir = Path(__file__).parent.parent / "prompts"
        else:
            self.prompts_dir = Path(prompts_dir)
            
    def build(self, template_name: str, db_session = None, **kwargs) -> str:
        template_key = template_name.replace(".md", "")
        
        if db_session:
            try:
                from app.models.prompt import SystemPrompt
                db_prompt = db_session.query(SystemPrompt).filter(SystemPrompt.name == template_key).first()
                if db_prompt:
                    template_content = db_prompt.content
                    try:
                        return template_content.format(**kwargs)
                    except KeyError as e:
                        logger.warning(f"Missing formatting key in database prompt: {e}")
                        return template_content
            except Exception as e:
                logger.error(f"Failed to read prompt from database: {e}")

        template_path = self.prompts_dir / template_name
        if not template_path.exists():
            raise FileNotFoundError(f"Prompt template '{template_name}' not found at {template_path}")
            
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
            
        # Basic variable interpolation using {var_name}
        try:
            return template_content.format(**kwargs)
        except KeyError as e:
            logger.warning(f"Missing formatting key in prompt: {e}")
            return template_content


class TokenEstimator:
    @staticmethod
    def estimate_tokens(text: str) -> int:
        # A common rule of thumb is 1 token ~= 4 chars in English
        return len(text) // 4


class BatchManager:
    @staticmethod
    def create_batches(items: List[Any], max_tokens: int, serialize_func: Callable[[Any], str]) -> List[List[Any]]:
        """
        Groups items into batches such that each batch's token count does not exceed max_tokens.
        Items are never split internally.
        """
        batches = []
        current_batch = []
        current_tokens = 0
        
        for item in items:
            serialized_item = serialize_func(item)
            item_tokens = TokenEstimator.estimate_tokens(serialized_item)
            
            if current_tokens + item_tokens > max_tokens and current_batch:
                batches.append(current_batch)
                current_batch = [item]
                current_tokens = item_tokens
            else:
                current_batch.append(item)
                current_tokens += item_tokens
                
        if current_batch:
            batches.append(current_batch)
            
        return batches


class JsonValidator:
    @staticmethod
    def validate_and_parse(json_str: str, schema: Type[T]) -> T:
        try:
            # Strip markdown wrapping if present
            cleaned_str = json_str.strip()
            if cleaned_str.startswith("```json"):
                cleaned_str = cleaned_str[7:-3]
            elif cleaned_str.startswith("```"):
                cleaned_str = cleaned_str[3:-3]
                
            parsed_json = json.loads(cleaned_str.strip())
            return schema(**parsed_json)
        except (json.JSONDecodeError, ValueError) as e:
            raise ValueError(f"JSON validation failed: {e}")


class RetryManager:
    @staticmethod
    def extract_retry_delay(error_msg: str) -> int:
        """Parses the 'retrydelay' or 'retry in Xs' hints from the error message."""
        # e.g., "retry in 22.342s"
        match = re.search(r"retry in ([\d\.]+)s", error_msg, re.IGNORECASE)
        if match:
            return int(float(match.group(1))) + 1
            
        # e.g., "'retrydelay': '22s'"
        match = re.search(r"'retrydelay': '(\d+)s'", error_msg, re.IGNORECASE)
        if match:
            return int(match.group(1)) + 1
            
        return None

    @staticmethod
    def execute_with_retry(func: Callable, max_attempts: int = 3, base_delay: int = 5):
        for attempt in range(1, max_attempts + 1):
            try:
                return func()
            except Exception as e:
                error_msg = str(e).lower()
                logger.warning(f"Attempt {attempt}/{max_attempts} failed: {error_msg}")
                
                if attempt == max_attempts:
                    raise RuntimeError(f"Operation failed after {max_attempts} attempts: {error_msg}")
                
                # Check if it's a rate limit or a temporary server issue
                if any(x in error_msg for x in ["429", "503", "500", "rate limit", "quota", "unavailable"]):
                    hint_delay = RetryManager.extract_retry_delay(error_msg)
                    if hint_delay:
                        sleep_time = hint_delay
                        logger.info(f"API provided retry delay hint: {sleep_time}s")
                    else:
                        sleep_time = base_delay * (2 ** (attempt - 1))
                        logger.info(f"Using exponential backoff delay: {sleep_time}s")
                        
                    logger.info(f"Rate limited. Sleeping for {sleep_time} seconds before retrying...")
                    time.sleep(sleep_time)
                else:
                    time.sleep(base_delay)


class AIProviderInterface(Protocol):
    """
    Abstract interface for all AI interactions.
    """
    def generate_structured_data(self, system_prompt: str, content: str, schema: Type[T]) -> T:
        pass


class GoogleGeminiProvider:
    """
    Concrete implementation using Google Gemini 2.5 Flash, highly optimized with Retries and PromptBuilder.
    """
    def __init__(self, model_name: str = None):
        self.model_name = model_name or os.environ.get("GEMINI_MODEL_NAME", "gemini-3.1-flash-lite")
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            logger.warning("GEMINI_API_KEY environment variable is not set. The AI Provider will fail.")
            
        self.client = genai.Client(api_key=api_key)
        
    def _do_generate(self, system_prompt: str, content: str, schema: Type[T]) -> T:
        logger.info(f"Executing AI request using {self.model_name}...")
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=content,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                response_schema=schema,
            ),
        )
        return JsonValidator.validate_and_parse(response.text, schema)

    def generate_structured_data(self, system_prompt: str, content: str, schema: Type[T]) -> T:
        return RetryManager.execute_with_retry(
            func=lambda: self._do_generate(system_prompt, content, schema),
            max_attempts=10,
            base_delay=5
        )

    def generate_text(self, system_prompt: str, content: str) -> str:
        """Raw text generation, benefiting from exponential backoff retries."""
        def _generate():
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=content,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                ),
            )
            return response.text
            
        return RetryManager.execute_with_retry(
            func=_generate,
            max_attempts=10,
            base_delay=5
        )

# Expose a default instance for dependency injection
default_ai_provider = GoogleGeminiProvider()
