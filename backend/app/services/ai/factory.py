from app.core.config import get_settings
from app.services.ai.base import AIProvider
from app.services.ai.mock_provider import MockAIProvider


def get_ai_provider() -> AIProvider:
    settings = get_settings()
    if settings.ai_provider == 'mock':
        return MockAIProvider()

    # Placeholder for future providers (OpenAI, Azure OpenAI, local LLMs).
    return MockAIProvider()
