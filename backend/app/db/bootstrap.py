from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


def _safe_add_column(engine: Engine, table: str, column_sql: str) -> None:
    stmt = text(f'ALTER TABLE {table} ADD COLUMN {column_sql}')
    with engine.begin() as conn:
        try:
            conn.execute(stmt)
        except Exception:
            # Best-effort runtime compatibility for old MVP databases.
            pass


def ensure_runtime_schema(engine: Engine) -> None:
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    dialect = engine.dialect.name

    json_type = 'JSON' if dialect == 'postgresql' else 'TEXT'
    bool_default_false = 'FALSE' if dialect == 'postgresql' else '0'

    if 'user_profiles' in tables:
        columns = {col['name'] for col in inspector.get_columns('user_profiles')}
        if 'grade_level' not in columns:
            _safe_add_column(engine, 'user_profiles', "grade_level VARCHAR(64)")
        if 'preferred_learning_style' not in columns:
            _safe_add_column(engine, 'user_profiles', "preferred_learning_style VARCHAR(64) DEFAULT 'explanation-first'")
        if 'weak_topics' not in columns:
            _safe_add_column(engine, 'user_profiles', f"weak_topics {json_type} DEFAULT '[]'")
        if 'target_exam_date' not in columns:
            _safe_add_column(engine, 'user_profiles', 'target_exam_date DATE')
        if 'study_minutes_per_day' not in columns:
            _safe_add_column(engine, 'user_profiles', 'study_minutes_per_day INTEGER DEFAULT 90')
        if 'focus_mode_enabled' not in columns:
            _safe_add_column(engine, 'user_profiles', f'focus_mode_enabled BOOLEAN DEFAULT {bool_default_false}')

    if 'study_buddy_state' in tables:
        columns = {col['name'] for col in inspector.get_columns('study_buddy_state')}
        if 'consistency_score' not in columns:
            _safe_add_column(engine, 'study_buddy_state', 'consistency_score INTEGER DEFAULT 50')
        if 'last_check_in' not in columns:
            _safe_add_column(engine, 'study_buddy_state', 'last_check_in DATE')
        if 'mood' not in columns:
            _safe_add_column(engine, 'study_buddy_state', "mood VARCHAR(32) DEFAULT 'focused'")
        if 'nudges' not in columns:
            _safe_add_column(engine, 'study_buddy_state', f"nudges {json_type} DEFAULT '[]'")

    if 'session_signals' in tables:
        columns = {col['name'] for col in inspector.get_columns('session_signals')}
        if 'page' not in columns:
            _safe_add_column(engine, 'session_signals', "page VARCHAR(120) DEFAULT 'dashboard'")
        if 'event_type' not in columns:
            _safe_add_column(engine, 'session_signals', "event_type VARCHAR(64) DEFAULT 'interaction'")
        if 'action' not in columns:
            _safe_add_column(engine, 'session_signals', "action VARCHAR(120) DEFAULT 'view'")
        if 'topic' not in columns:
            _safe_add_column(engine, 'session_signals', 'topic VARCHAR(160)')
        if 'task_difficulty' not in columns:
            _safe_add_column(engine, 'session_signals', 'task_difficulty VARCHAR(32)')
        if 'energy_level' not in columns:
            _safe_add_column(engine, 'session_signals', 'energy_level VARCHAR(32)')
        if 'self_confidence' not in columns:
            _safe_add_column(engine, 'session_signals', 'self_confidence FLOAT')
        if 'was_correct' not in columns:
            _safe_add_column(engine, 'session_signals', 'was_correct BOOLEAN')
        if 'dwell_seconds' not in columns:
            _safe_add_column(engine, 'session_signals', 'dwell_seconds INTEGER DEFAULT 0')
        if 'metadata' not in columns:
            _safe_add_column(engine, 'session_signals', f"metadata {json_type} DEFAULT '{{}}'")
