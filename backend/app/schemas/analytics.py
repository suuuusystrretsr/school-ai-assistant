from pydantic import BaseModel


class DashboardAnalyticsResponse(BaseModel):
    subject_progress: dict
    mastery_by_topic: dict
    recent_performance: dict
    practice_accuracy: int
    readiness_score: int
    learning_consistency: int
    streak_days: int
    retention_forecast: dict
    confusion_detector: dict
    focus_mode: dict


class LearningSignalRequest(BaseModel):
    activity_seconds: int
    wrong_attempts: int
    answer_changes: int
    tab_switches: int


class LearningSignalResponse(BaseModel):
    confusion_probability: float
    prompt_hint: bool
    focus_prompt: bool
    suggested_message: str
