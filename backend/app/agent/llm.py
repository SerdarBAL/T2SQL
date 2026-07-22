"""Provider-agnostic LLM factory.

Groq is the active provider (fast, generous free tier); Gemini stays as a
drop-in fallback. Adding OpenAI/Anthropic is just another branch here —
call sites (nodes) never change.
"""
from langchain_core.language_models.chat_models import BaseChatModel

from app.config import get_settings


def get_llm() -> BaseChatModel:
    settings = get_settings()

    if settings.llm_provider == "groq":
        from langchain_groq import ChatGroq

        return ChatGroq(
            model=settings.llm_model,
            api_key=settings.groq_api_key,
            temperature=0,
        )

    if settings.llm_provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=settings.llm_model,
            google_api_key=settings.google_api_key,
        )

    raise ValueError(f"Unsupported LLM_PROVIDER: {settings.llm_provider}")
