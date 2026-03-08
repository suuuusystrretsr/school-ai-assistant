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


@router.get('/ai-exam')
def ai_exam_debug(
    subject: str = 'Math',
    topic: str = 'quadratics',
    difficulty: str = 'medium',
    style: str = 'exam-board style',
    question_count: int = 5,
) -> dict:
    provider = get_ai_provider()
    fn = getattr(provider, 'generate_exam_questions', None)

    if not callable(fn):
        return {
            'provider': provider.__class__.__name__,
            'ok': False,
            'error': 'Provider does not implement generate_exam_questions',
        }

    try:
        out = fn(subject, topic, difficulty, style, question_count)
    except Exception as exc:  # pragma: no cover
        return {
            'provider': provider.__class__.__name__,
            'ok': False,
            'error': str(exc),
            'hf_last_error': getattr(provider, 'last_error', ''),
        }

    questions = out if isinstance(out, list) else []
    return {
        'provider': provider.__class__.__name__,
        'ok': len(questions) > 0,
        'count': len(questions),
        'sample': questions[0] if questions else None,
        'hf_last_error': getattr(provider, 'last_error', ''),
    }
