from app.schemas.analytics import LearningSignalRequest, LearningSignalResponse


def detect_confusion(signal: LearningSignalRequest) -> LearningSignalResponse:
    score = 0.0
    score += min(signal.wrong_attempts * 0.2, 0.6)
    score += min(signal.answer_changes * 0.1, 0.2)
    score += 0.2 if signal.activity_seconds > 240 and signal.wrong_attempts > 1 else 0

    confusion_probability = min(score, 1.0)
    prompt_hint = confusion_probability >= 0.45
    focus_prompt = signal.tab_switches >= 6 or signal.activity_seconds > 900

    if focus_prompt:
        message = 'Still studying? Consider enabling a 25-minute focus session.'
    elif prompt_hint:
        message = 'Need a hint? We can reveal hints progressively.'
    else:
        message = 'Nice pace. Keep going.'

    return LearningSignalResponse(
        confusion_probability=round(confusion_probability, 2),
        prompt_hint=prompt_hint,
        focus_prompt=focus_prompt,
        suggested_message=message,
    )
