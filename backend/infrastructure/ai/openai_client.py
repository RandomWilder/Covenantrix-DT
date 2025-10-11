"""
OpenAI Client
Centralized OpenAI API interaction with proper error handling and retry logic
"""
import logging
from typing import Dict, Any, Optional, List
from openai import AsyncOpenAI, OpenAIError
import asyncio
from functools import wraps

from core.config import get_settings
from core.exceptions import ExternalServiceError

logger = logging.getLogger(__name__)


def with_retry(max_retries: int = 3, backoff_factor: float = 1.5):
    """Decorator for retry logic with exponential backoff"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except OpenAIError as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        wait_time = backoff_factor ** attempt
                        logger.warning(
                            f"OpenAI API error (attempt {attempt + 1}/{max_retries}): {str(e)}. "
                            f"Retrying in {wait_time:.1f}s..."
                        )
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(f"OpenAI API failed after {max_retries} attempts")
            raise ExternalServiceError(
                f"OpenAI API failed: {str(last_exception)}",
                service="openai"
            )
        return wrapper
    return decorator


class OpenAIClient:
    """
    Clean OpenAI client wrapper with error handling and logging
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenAI client
        
        Args:
            api_key: OpenAI API key (optional, falls back to config)
        """
        settings = get_settings()
        self.api_key = api_key or settings.openai_api_key
        
        if not self.api_key:
            raise ValueError("OpenAI API key not configured")
        
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.default_model = "gpt-4o-mini"
        self.logger = logging.getLogger(__name__)
    
    @with_retry(max_retries=3)
    async def create_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Create chat completion
        
        Args:
            messages: List of message dictionaries
            model: Model to use (optional)
            temperature: Sampling temperature
            max_tokens: Max tokens to generate
            response_format: Response format specification
            
        Returns:
            Completion text
        """
        try:
            kwargs = {
                "model": model or self.default_model,
                "messages": messages,
                "temperature": temperature
            }
            
            if max_tokens:
                kwargs["max_tokens"] = max_tokens
            
            if response_format:
                kwargs["response_format"] = response_format
            
            response = await self.client.chat.completions.create(**kwargs)
            
            content = response.choices[0].message.content
            self.logger.debug(f"Completion generated: {len(content)} chars")
            
            return content
            
        except Exception as e:
            self.logger.error(f"Completion failed: {str(e)}")
            raise
    
    @with_retry(max_retries=2)
    async def create_embedding(
        self,
        text: str,
        model: str = "text-embedding-3-small"
    ) -> List[float]:
        """
        Create text embedding
        
        Args:
            text: Text to embed
            model: Embedding model
            
        Returns:
            Embedding vector
        """
        try:
            response = await self.client.embeddings.create(
                model=model,
                input=text
            )
            
            embedding = response.data[0].embedding
            self.logger.debug(f"Embedding created: {len(embedding)} dimensions")
            
            return embedding
            
        except Exception as e:
            self.logger.error(f"Embedding failed: {str(e)}")
            raise
    
    async def extract_structured_data(
        self,
        text: str,
        extraction_prompt: str,
        schema: Dict[str, Any],
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract structured data from text using JSON mode
        
        Args:
            text: Text to extract from
            extraction_prompt: Extraction instructions
            schema: Expected JSON schema
            model: Model to use
            
        Returns:
            Extracted data as dictionary
        """
        import json
        
        messages = [
            {
                "role": "system",
                "content": f"{extraction_prompt}\n\nRespond with valid JSON matching this schema: {json.dumps(schema)}"
            },
            {
                "role": "user",
                "content": text
            }
        ]
        
        response = await self.create_completion(
            messages=messages,
            model=model,
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON response: {str(e)}")
            # Return empty structure matching schema
            return {key: [] if isinstance(value, list) else None 
                    for key, value in schema.items()}