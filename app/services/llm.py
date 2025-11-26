"""LLM wrapper for OpenAI API calls."""
import os
from typing import List, Optional, Dict, Any
from openai import OpenAI
from app.core.config import settings


class MockLLM:
    """Mock LLM for local development and testing."""

    @staticmethod
    def get_embedding(text: str) -> List[float]:
        """Return a mock embedding vector."""
        # Return a 1536-dimensional vector (text-embedding-3-small dimension)
        import random
        random.seed(hash(text) % 2**32)
        return [random.gauss(0, 0.1) for _ in range(1536)]

    @staticmethod
    def call_chat(messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Return a mock chat response."""
        return {
            "id": "mock-chat-id",
            "object": "chat.completion",
            "created": 1234567890,
            "model": settings.OPENAI_MODEL,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "This is a mock response. Set OPENAI_API_KEY to use real API."
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
        }

    @staticmethod
    def summarize_text(text: str) -> str:
        """Return a mock summary."""
        return f"Mock summary of text (length: {len(text)} chars)"


class LLMService:
    """Service for LLM operations."""

    def __init__(self):
        """Initialize LLM service with OpenAI client or mock."""
        # Check if API key is empty or is a placeholder
        api_key = settings.OPENAI_API_KEY or ""
        self.use_mock = (
            not api_key or 
            api_key == "" or 
            "your_openai_api_key" in api_key.lower() or
            "change" in api_key.lower() or
            not api_key.startswith("sk-")  # Real keys start with sk-
        )
        if self.use_mock:
            self.client = MockLLM()
        else:
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
        self.embedding_model = settings.OPENAI_EMBEDDING_MODEL

    def get_embedding(self, text: str) -> List[float]:
        """
        Get embedding vector for text.

        Args:
            text: Input text to embed

        Returns:
            List of floats representing the embedding vector
        """
        if self.use_mock:
            return self.client.get_embedding(text)

        try:
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            # Fallback to mock on error
            print(f"Error getting embedding: {e}, using mock")
            return MockLLM.get_embedding(text)

    def call_chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Call chat completion API.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            **kwargs: Additional parameters

        Returns:
            API response dict
        """
        if self.use_mock:
            return self.client.call_chat(messages, **kwargs)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            return {
                "id": response.id,
                "object": response.object,
                "created": response.created,
                "model": response.model,
                "choices": [
                    {
                        "index": choice.index,
                        "message": {
                            "role": choice.message.role,
                            "content": choice.message.content
                        },
                        "finish_reason": choice.finish_reason
                    }
                    for choice in response.choices
                ],
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
        except Exception as e:
            print(f"Error calling chat API: {e}, falling back to mock")
            # Fall back to mock on error
            return MockLLM.call_chat(messages, **kwargs)

    def stream_chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        **kwargs
    ):
        """
        Stream chat completion (generator).

        Args:
            messages: List of message dicts
            temperature: Sampling temperature
            **kwargs: Additional parameters

        Yields:
            Chunks of the response
        """
        if self.use_mock:
            yield {"choices": [{"delta": {"content": "Mock streaming response"}}]}
            return

        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                stream=True,
                **kwargs
            )
            for chunk in stream:
                yield {
                    "choices": [
                        {
                            "delta": {
                                "content": chunk.choices[0].delta.content if chunk.choices[0].delta.content else ""
                            }
                        }
                    ]
                }
        except Exception as e:
            print(f"Error streaming chat: {e}")
            raise

    def summarize_text(self, text: str, max_length: int = 200) -> str:
        """
        Summarize text using LLM.

        Args:
            text: Text to summarize
            max_length: Maximum length of summary

        Returns:
            Summary string
        """
        if self.use_mock:
            return self.client.summarize_text(text)

        messages = [
            {
                "role": "system",
                "content": f"Summarize the following text in {max_length} characters or less."
            },
            {
                "role": "user",
                "content": text
            }
        ]

        response = self.call_chat(messages, temperature=0.3, max_tokens=100)
        return response["choices"][0]["message"]["content"]


# Global instance
llm_service = LLMService()

