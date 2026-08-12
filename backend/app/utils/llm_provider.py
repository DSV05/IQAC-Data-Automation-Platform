"""
Shared provider helpers for LangChain chat models and embeddings.
Used by the RAG Chatbot (Module 7). Kept separate from Module 6's
inline provider selection so neither module can break the other.
"""
from app.core.config import get_settings

settings = get_settings()


class LLMProviderError(Exception):
    """User-facing error — safe to show verbatim in API responses."""


def get_chat_llm(temperature: float = 0):
    if settings.AI_PROVIDER == "ollama":
        from langchain_community.chat_models import ChatOllama
        return ChatOllama(base_url=settings.OLLAMA_BASE_URL, model=settings.AI_MODEL_OLLAMA, temperature=temperature)

    if not settings.OPENAI_API_KEY:
        raise LLMProviderError(
            "AI features aren't configured yet. Ask your administrator to set OPENAI_API_KEY "
            "(or switch AI_PROVIDER to 'ollama') in the environment."
        )
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(api_key=settings.OPENAI_API_KEY, model=settings.AI_MODEL_OPENAI, temperature=temperature)


def get_embeddings():
    """
    Returns a LangChain embeddings instance for the configured provider.
    Note: for Ollama, this requires an embedding-capable model (e.g. `ollama pull
    nomic-embed-text`) — a chat-only model like a Llama fine-tune will not work here.
    """
    if settings.AI_PROVIDER == "ollama":
        from langchain_community.embeddings import OllamaEmbeddings
        return OllamaEmbeddings(base_url=settings.OLLAMA_BASE_URL, model=settings.RAG_EMBEDDING_MODEL_OLLAMA)

    if not settings.OPENAI_API_KEY:
        raise LLMProviderError(
            "AI features aren't configured yet. Ask your administrator to set OPENAI_API_KEY "
            "(or switch AI_PROVIDER to 'ollama') in the environment."
        )
    from langchain_openai import OpenAIEmbeddings
    return OpenAIEmbeddings(api_key=settings.OPENAI_API_KEY, model=settings.RAG_EMBEDDING_MODEL_OPENAI)
