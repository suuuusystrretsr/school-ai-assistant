from fastapi import APIRouter

from app.services.ai.factory import get_ai_provider

router = APIRouter(prefix='/debug', tags=['debug'])


@router.get('/ai')
def ai_debug() -> dict:
    provider = get_ai_provider()
    provider_name = provider.__class__.__name__

    probe = None
    if hasattr(provider, '_invoke_model'):
        try:
            probe_raw = provider._invoke_model('Reply with exactly: OK', max_new_tokens=32)  # type: ignore[attr-defined]
            probe = {
                'ok': bool(probe_raw),
                'raw_preview': (probe_raw or '')[:180],
            }
        except Exception as exc:  # pragma: no cover
            probe = {'ok': False, 'error': str(exc)}

    return {
        'provider': provider_name,
        'has_hf_endpoint': bool(getattr(provider, 'endpoint', '')),
        'has_hf_key': bool(getattr(provider, 'api_key', '')),
        'probe': probe,
        'hf_last_error': getattr(provider, 'last_error', ''),
    }

