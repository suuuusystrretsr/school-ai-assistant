from app.core.config import get_settings
from app.services.ai.base import AIProvider
from app.services.ai.huggingface_provider import HuggingFaceProvider
from app.services.ai.mock_provider import MockAIProvider


def get_ai_provider() -> AIProvider:
    settings = get_settings()
    if settings.ai_provider == 'huggingface' and settings.hf_api_key and settings.hf_model_id:
        return HuggingFaceProvider()

    if settings.ai_provider == 'mock':
        return MockAIProvider()

    return MockAIProvider()

