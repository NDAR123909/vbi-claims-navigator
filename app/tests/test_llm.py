"""Tests for LLM service."""
import pytest
from app.services.llm import llm_service


def test_get_embedding():
    """Test embedding generation."""
    text = "Test text"
    embedding = llm_service.get_embedding(text)
    assert isinstance(embedding, list)
    assert len(embedding) > 0


def test_call_chat():
    """Test chat completion."""
    messages = [
        {"role": "user", "content": "Say hello"}
    ]
    response = llm_service.call_chat(messages)
    assert "choices" in response
    assert len(response["choices"]) > 0
    assert "message" in response["choices"][0]
    assert "content" in response["choices"][0]["message"]


def test_summarize_text():
    """Test text summarization."""
    text = "This is a long text that needs to be summarized. " * 10
    summary = llm_service.summarize_text(text)
    assert isinstance(summary, str)
    assert len(summary) > 0

