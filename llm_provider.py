"""
LLM Provider Abstraction Layer
Supports: Claude (Anthropic), Gemini (Google), OpenAI
Switch providers via LLM_PROVIDER env variable
"""

from config import settings
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain.llms.base import BaseLLM


def get_llm() -> BaseLLM:
    """
    Factory function to get the configured LLM based on LLM_PROVIDER env var.

    Returns:
        BaseLLM: Configured language model instance

    Raises:
        ValueError: If provider not configured properly
    """
    provider = settings.llm_provider.lower()

    if provider == "claude":
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY not set in environment")
        return ChatAnthropic(
            model="claude-opus-5",
            anthropic_api_key=settings.anthropic_api_key,
            max_tokens=2048,
            # langchain-anthropic 0.1.0 predates extended thinking and assumes
            # content[0] is always a text block; thinking is on by default on
            # Claude Opus 5, so disable it to keep text[0] first.
            model_kwargs={"thinking": {"type": "disabled"}},
        )

    elif provider == "gemini":
        if not settings.google_api_key:
            raise ValueError("GOOGLE_API_KEY not set in environment")
        return ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=settings.google_api_key,
            temperature=0.7,
        )

    elif provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY not set in environment")
        return ChatOpenAI(
            model="gpt-4-turbo",
            api_key=settings.openai_api_key,
            temperature=0.7,
            max_tokens=2048,
        )

    else:
        raise ValueError(
            f"Unknown LLM provider: {provider}. "
            f"Must be 'claude', 'gemini', or 'openai'"
        )


def get_llm_name() -> str:
    """Get the current LLM provider name."""
    return settings.llm_provider.lower()
