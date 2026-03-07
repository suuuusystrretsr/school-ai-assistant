from datetime import datetime, timedelta, timezone


def compute_memory_strength(days_since_review: int, quality_score: int = 3) -> float:
    base = max(0.1, 1 - (days_since_review * 0.08))
    quality_boost = (quality_score - 3) * 0.05
    return max(0.05, min(1.0, base + quality_boost))


def next_review_from_strength(memory_strength: float) -> tuple[datetime, str]:
    now = datetime.now(timezone.utc)
    if memory_strength < 0.3:
        return now + timedelta(hours=12), 'high'
    if memory_strength < 0.6:
        return now + timedelta(days=2), 'medium'
    return now + timedelta(days=5), 'low'
