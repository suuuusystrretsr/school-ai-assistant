from pydantic import BaseModel, Field


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


class SessionSignalRequest(BaseModel):
    page: str = 'dashboard'
    event_type: str = 'interaction'
    action: str = 'view'
    topic: str | None = None
    task_difficulty: str | None = None
    energy_level: str | None = None
    self_confidence: int | None = Field(default=None, ge=0, le=100)
    was_correct: bool | None = None
    dwell_seconds: int = Field(default=0, ge=0)
    metadata: dict = Field(default_factory=dict)


class SessionSignalResponse(BaseModel):
    stored: bool
    friction_flags: list[str]
    recommendation: str


class AutopilotRequest(BaseModel):
    energy_level: str = 'medium'
    available_minutes: int = Field(default=60, ge=15, le=360)
    weak_topics: list[str] = Field(default_factory=list)
    retention_risk: list[str] = Field(default_factory=list)
    confidence_gaps: list[str] = Field(default_factory=list)
    readiness_score: int = Field(default=0, ge=0, le=100)


class AutopilotResponse(BaseModel):
    routing: str
    study_identity: str
    plan: list[dict]
    skip_for_now: list[str]
    switch_rules: list[str]


class IntelligenceResponse(BaseModel):
    confidence_map: dict
    cognitive_breakdown: dict
    why_stuck: dict
    knowledge_dependencies: list[dict]
    friction_detector: dict
    memory_forecast: dict
    mistake_pattern_intelligence: dict
    session_replay: dict
    exam_outcome_simulator: dict
    priority_distortion: dict
    study_identity_model: dict
    next_best_action: dict
