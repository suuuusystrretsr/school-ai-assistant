from collections import Counter, defaultdict
from statistics import mean
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.analytics import AnalyticsSnapshot
from app.models.exam import ExamSimulation
from app.models.flashcard import FlashcardDeck
from app.models.homework import HomeworkRequest
from app.models.knowledge import KnowledgeGraphNode, MemoryReviewSchedule
from app.models.planner import PlannerTask
from app.models.session_signal import SessionSignal
from app.models.user import StudyBuddyState, User
from app.schemas.analytics import (
    AutopilotRequest,
    AutopilotResponse,
    DashboardAnalyticsResponse,
    IntelligenceResponse,
    LearningSignalRequest,
    SessionSignalRequest,
    SessionSignalResponse,
)
from app.services.analytics.signals import detect_confusion
from app.services.planner.memory import compute_memory_strength, next_review_from_strength

router = APIRouter(prefix='/analytics', tags=['analytics'])


def _normalize_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _collect_activity_dates(user_id: int, db: Session) -> dict:
    activity_dates: set = set()
    day_counts: dict = defaultdict(int)

    sources = [
        db.query(HomeworkRequest.created_at).filter(HomeworkRequest.user_id == user_id).all(),
        db.query(FlashcardDeck.created_at).filter(FlashcardDeck.user_id == user_id).all(),
        db.query(PlannerTask.created_at).filter(PlannerTask.user_id == user_id).all(),
        db.query(ExamSimulation.started_at).filter(ExamSimulation.user_id == user_id).all(),
        db.query(ExamSimulation.completed_at).filter(ExamSimulation.user_id == user_id).all(),
        db.query(SessionSignal.created_at).filter(SessionSignal.user_id == user_id).all(),
    ]

    for source in sources:
        for (raw_dt,) in source:
            dt = _normalize_datetime(raw_dt)
            if not dt:
                continue
            d = dt.date()
            activity_dates.add(d)
            day_counts[d] += 1

    today = datetime.now(timezone.utc).date()
    active_days_last_14 = sum(1 for d in activity_dates if d >= (today - timedelta(days=13)))

    streak = 0
    cursor = today
    while cursor in activity_dates:
        streak += 1
        cursor = cursor - timedelta(days=1)

    recent_activity = []
    for offset in range(6, -1, -1):
        day = today - timedelta(days=offset)
        recent_activity.append({'date': day.isoformat(), 'activities': day_counts.get(day, 0)})

    consistency = int(round((active_days_last_14 / 14) * 100)) if active_days_last_14 else 0

    return {
        'streak': streak,
        'active_days_last_14': active_days_last_14,
        'learning_consistency': consistency,
        'recent_activity': recent_activity,
    }


def _build_dashboard_payload(user: User, db: Session) -> dict:
    completed_exams = (
        db.query(ExamSimulation)
        .filter(ExamSimulation.user_id == user.id, ExamSimulation.actual_score.isnot(None))
        .order_by(ExamSimulation.completed_at.asc())
        .all()
    )

    exam_scores = [row.actual_score for row in completed_exams if row.actual_score is not None]
    latest_score = exam_scores[-1] if exam_scores else 0
    avg_score = int(round(sum(exam_scores) / len(exam_scores))) if exam_scores else 0

    practice_accuracy = avg_score
    readiness_score = int(round((avg_score * 0.6) + (latest_score * 0.4))) if exam_scores else 0

    subject_buckets: dict[str, list[int]] = defaultdict(list)
    for exam in completed_exams:
        if exam.actual_score is not None:
            subject_buckets[exam.subject].append(exam.actual_score)

    subject_progress = {
        subject: int(round(sum(scores) / len(scores)))
        for subject, scores in subject_buckets.items()
    }

    nodes = db.query(KnowledgeGraphNode).filter(KnowledgeGraphNode.user_id == user.id).all()
    mastery_by_topic: dict = {}
    for node in nodes:
        mastery_by_topic.setdefault(node.subject, {})[node.topic] = {
            'status': node.status,
            'score': int(round(node.mastery_score * 100)),
        }

    memory_rows = db.query(MemoryReviewSchedule).filter(MemoryReviewSchedule.user_id == user.id).all()
    now = datetime.now(timezone.utc)
    threshold = now + timedelta(days=3)

    high = [row.topic for row in memory_rows if row.urgency == 'high']
    medium = [row.topic for row in memory_rows if row.urgency == 'medium']
    low = [row.topic for row in memory_rows if row.urgency == 'low']
    next_3_days_risk = [
        row.topic
        for row in memory_rows
        if _normalize_datetime(row.next_review_at) and _normalize_datetime(row.next_review_at) <= threshold
    ]

    activity = _collect_activity_dates(user.id, db)

    homework_count = db.query(HomeworkRequest.id).filter(HomeworkRequest.user_id == user.id).count()
    flashcard_count = db.query(FlashcardDeck.id).filter(FlashcardDeck.user_id == user.id).count()
    planner_count = db.query(PlannerTask.id).filter(PlannerTask.user_id == user.id).count()

    retention_forecast = {
        'high': high,
        'medium': medium,
        'low': low,
        'next_3_days_risk': next_3_days_risk,
    }

    recent_performance = {
        'completed_exams': len(exam_scores),
        'homework_solved': homework_count,
        'flashcard_decks': flashcard_count,
        'study_plans_generated': planner_count,
        'active_days_last_14': activity['active_days_last_14'],
        'last_7_days': activity['recent_activity'],
    }

    return {
        'subject_progress': subject_progress,
        'mastery_by_topic': mastery_by_topic,
        'recent_performance': recent_performance,
        'practice_accuracy': practice_accuracy,
        'readiness_score': readiness_score,
        'learning_consistency': activity['learning_consistency'],
        'streak_days': activity['streak'],
        'retention_forecast': retention_forecast,
    }


@router.get('/dashboard', response_model=DashboardAnalyticsResponse)
def dashboard(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    signals = _load_recent_signals(user.id, db)
    computed = _build_dashboard_payload(user, db)

    snapshot = (
        db.query(AnalyticsSnapshot)
        .filter(AnalyticsSnapshot.user_id == user.id)
        .order_by(AnalyticsSnapshot.created_at.desc())
        .first()
    )

    if not snapshot:
        snapshot = AnalyticsSnapshot(user_id=user.id)

    snapshot.subject_progress = computed['subject_progress']
    snapshot.mastery_by_topic = computed['mastery_by_topic']
    snapshot.recent_performance = computed['recent_performance']
    snapshot.practice_accuracy = computed['practice_accuracy']
    snapshot.readiness_score = computed['readiness_score']
    snapshot.learning_consistency = computed['learning_consistency']
    snapshot.streak_days = computed['streak_days']
    snapshot.retention_forecast = computed['retention_forecast']
    friction = _build_friction_detector(signals)
    snapshot.distraction_risk = 'high' if friction['score'] >= 60 else 'medium' if friction['score'] >= 35 else 'low'

    db.add(snapshot)
    db.commit()

    confusion_detector = {
        'status': 'monitoring',
        'message': 'Need a hint? appears only when confusion signals are detected.',
    }
    focus_mode = {
        'enabled': friction['score'] < 60,
        'suggestion': friction['prompt'],
    }

    return DashboardAnalyticsResponse(
        subject_progress=snapshot.subject_progress,
        mastery_by_topic=snapshot.mastery_by_topic,
        recent_performance=snapshot.recent_performance,
        practice_accuracy=snapshot.practice_accuracy,
        readiness_score=snapshot.readiness_score,
        learning_consistency=snapshot.learning_consistency,
        streak_days=snapshot.streak_days,
        retention_forecast=snapshot.retention_forecast,
        confusion_detector=confusion_detector,
        focus_mode=focus_mode,
    )


@router.post('/signals')
def process_learning_signal(payload: LearningSignalRequest, user: User = Depends(get_current_user)):
    return detect_confusion(payload)


@router.post('/memory/{topic}')
def update_memory_schedule(topic: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    existing = (
        db.query(MemoryReviewSchedule)
        .filter(MemoryReviewSchedule.user_id == user.id, MemoryReviewSchedule.topic == topic)
        .first()
    )

    days_since = 1
    if existing:
        days_since = max(1, (now - existing.last_reviewed_at).days)

    strength = compute_memory_strength(days_since_review=days_since)
    next_review, urgency = next_review_from_strength(strength)

    if not existing:
        existing = MemoryReviewSchedule(
            user_id=user.id,
            topic=topic,
            memory_strength=strength,
            last_reviewed_at=now,
            next_review_at=next_review,
            urgency=urgency,
        )
    else:
        existing.memory_strength = strength
        existing.last_reviewed_at = now
        existing.next_review_at = next_review
        existing.urgency = urgency

    db.add(existing)
    db.commit()
    db.refresh(existing)

    return {
        'topic': existing.topic,
        'memory_strength': existing.memory_strength,
        'next_review_at': existing.next_review_at,
        'urgency': existing.urgency,
    }


@router.get('/memory/review-queue')
def get_review_queue(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    queue = (
        db.query(MemoryReviewSchedule)
        .filter(MemoryReviewSchedule.user_id == user.id)
        .order_by(MemoryReviewSchedule.next_review_at.asc())
        .all()
    )
    return [
        {
            'topic': item.topic,
            'memory_strength': item.memory_strength,
            'next_review_at': item.next_review_at,
            'urgency': item.urgency,
        }
        for item in queue
    ]


@router.post('/knowledge-node')
def upsert_knowledge_node(
    subject: str,
    topic: str,
    mastery_score: float,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    node = (
        db.query(KnowledgeGraphNode)
        .filter(
            KnowledgeGraphNode.user_id == user.id,
            KnowledgeGraphNode.subject == subject,
            KnowledgeGraphNode.topic == topic,
        )
        .first()
    )
    status = 'mastered' if mastery_score >= 0.75 else 'weak' if mastery_score >= 0.35 else 'not-learned'

    if not node:
        node = KnowledgeGraphNode(
            user_id=user.id,
            subject=subject,
            topic=topic,
            mastery_score=mastery_score,
            status=status,
        )
    else:
        node.mastery_score = mastery_score
        node.status = status

    db.add(node)
    db.commit()
    db.refresh(node)
    return {'subject': node.subject, 'topic': node.topic, 'mastery_score': node.mastery_score, 'status': node.status}


@router.get('/knowledge-graph')
def get_knowledge_graph(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    nodes = db.query(KnowledgeGraphNode).filter(KnowledgeGraphNode.user_id == user.id).all()
    return [
        {'subject': n.subject, 'topic': n.topic, 'status': n.status, 'mastery_score': n.mastery_score}
        for n in nodes
    ]


@router.get('/study-buddy')
def get_study_buddy_state(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    buddy = db.query(StudyBuddyState).filter(StudyBuddyState.user_id == user.id).first()
    if not buddy:
        buddy = StudyBuddyState(user_id=user.id, streak_days=0, consistency_score=0, mood='starting', nudges=[])

    activity = _collect_activity_dates(user.id, db)
    consistency = activity['learning_consistency']
    streak = activity['streak']

    if consistency >= 70 or streak >= 5:
        mood = 'focused'
    elif consistency >= 30 or streak >= 2:
        mood = 'building'
    else:
        mood = 'starting'

    nudges = []
    if activity['active_days_last_14'] == 0:
        nudges.append({'type': 'start', 'message': 'Start with one 20-minute study block today.'})
    if consistency < 40:
        nudges.append({'type': 'consistency', 'message': 'Aim for 3 short sessions this week to build momentum.'})
    if streak > 0:
        nudges.append({'type': 'streak', 'message': f'Keep your {streak}-day streak alive with one quick review.'})

    buddy.streak_days = streak
    buddy.consistency_score = consistency
    buddy.mood = mood
    buddy.nudges = nudges

    db.add(buddy)
    db.commit()
    db.refresh(buddy)

    return {
        'streak_days': buddy.streak_days,
        'consistency_score': buddy.consistency_score,
        'mood': buddy.mood,
        'nudges': buddy.nudges,
    }




COGNITIVE_TYPES = [
    'concept misunderstanding',
    'memory failure',
    'rushed reading',
    'weak logic chain',
    'poor evidence use',
    'calculation slip',
    'pattern confusion',
]


def _load_recent_signals(user_id: int, db: Session) -> list[SessionSignal]:
    return (
        db.query(SessionSignal)
        .filter(SessionSignal.user_id == user_id)
        .order_by(SessionSignal.created_at.desc())
        .limit(250)
        .all()
    )


def _build_confidence_map(signals: list[SessionSignal], fallback_score: int) -> dict:
    topic_stats: dict[str, dict[str, float]] = defaultdict(lambda: {'correct': 0, 'attempts': 0, 'confidence': 0, 'conf_count': 0})

    for signal in signals:
        topic = signal.topic or signal.page or 'general'
        if signal.was_correct is not None:
            topic_stats[topic]['attempts'] += 1
            if signal.was_correct:
                topic_stats[topic]['correct'] += 1
        if signal.self_confidence is not None:
            topic_stats[topic]['confidence'] += signal.self_confidence
            topic_stats[topic]['conf_count'] += 1

    points = []
    overconfidence = []
    hidden_strength = []
    uncertainty = []

    for topic, stats in topic_stats.items():
        attempts = int(stats['attempts'])
        conf_count = int(stats['conf_count'])
        if attempts == 0 and conf_count == 0:
            continue

        actual = int(round((stats['correct'] / attempts) * 100)) if attempts else fallback_score
        confidence = int(round(stats['confidence'] / conf_count)) if conf_count else actual
        gap = confidence - actual

        points.append({'topic': topic, 'actual': actual, 'confidence': confidence, 'gap': gap})

        if gap >= 18:
            overconfidence.append(topic)
        elif gap <= -15 and actual >= 60:
            hidden_strength.append(topic)
        elif 42 <= confidence <= 62:
            uncertainty.append(topic)

    if not points:
        points = [{'topic': 'general', 'actual': fallback_score, 'confidence': fallback_score, 'gap': 0}]

    overall_actual = int(round(mean([point['actual'] for point in points])))
    overall_confidence = int(round(mean([point['confidence'] for point in points])))

    return {
        'overall_actual': overall_actual,
        'overall_confidence': overall_confidence,
        'overconfidence': overconfidence,
        'hidden_strength': hidden_strength,
        'uncertainty_zones': uncertainty,
        'points': points,
    }


def _infer_cognitive_type(signal: SessionSignal) -> str:
    if signal.was_correct is not False:
        return 'pattern confusion'

    confidence = signal.self_confidence if signal.self_confidence is not None else 50
    topic = (signal.topic or '').lower()
    page = (signal.page or '').lower()
    action = (signal.action or '').lower()

    if (signal.task_difficulty or '').lower() == 'hard' and confidence < 40:
        return 'concept misunderstanding'
    if confidence >= 75 and (signal.dwell_seconds or 0) < 45:
        return 'rushed reading'
    if confidence >= 75 and (signal.dwell_seconds or 0) >= 45:
        return 'weak logic chain'
    if any(token in action for token in ['calc', 'equation', 'algebra']) or any(token in topic for token in ['algebra', 'equation', 'fraction']):
        return 'calculation slip'
    if any(token in topic for token in ['history', 'source', 'evidence']) or 'evidence' in action:
        return 'poor evidence use'
    if page == 'flashcards' or (signal.task_difficulty or '').lower() == 'easy':
        return 'memory failure'
    return 'pattern confusion'


def _build_cognitive_breakdown(signals: list[SessionSignal]) -> dict:
    counter = Counter({item: 0 for item in COGNITIVE_TYPES})

    for signal in signals:
        if signal.was_correct is False:
            counter[_infer_cognitive_type(signal)] += 1

    dominant = max(counter.items(), key=lambda entry: entry[1])[0] if counter else 'pattern confusion'
    total = sum(counter.values())

    return {
        'dominant': dominant,
        'total_detected_mistakes': total,
        'breakdown': [{'type': key, 'count': counter[key]} for key in COGNITIVE_TYPES],
        'recommendation': f'Focus correction drills on {dominant} for the next 2 sessions.' if total else 'No strong breakdown signal yet.',
    }


def _build_why_stuck(signals: list[SessionSignal]) -> dict:
    page_switches = sum(1 for signal in signals if signal.event_type == 'navigation')
    long_views = sum(1 for signal in signals if (signal.action or '') in {'view', 'open'} and (signal.dwell_seconds or 0) >= 120)

    wrong_by_topic: Counter = Counter()
    for signal in signals:
        if signal.was_correct is False:
            wrong_by_topic[signal.topic or 'general'] += 1

    blocked_topics = [topic for topic, count in wrong_by_topic.items() if count >= 2]
    insights = []

    if long_views >= 3:
        insights.append('You are rereading instead of solving. Do one active solve before rereading.')
    if page_switches >= 6:
        insights.append('You are switching pages repeatedly. Stay on one task block for 12 minutes.')
    if blocked_topics:
        insights.append('You are stuck because this topic depends on a missing prerequisite.')
    if not insights:
        insights.append('Progress is stable. Keep using short solve-review cycles.')

    return {
        'status': 'detected' if blocked_topics or page_switches >= 6 or long_views >= 3 else 'clear',
        'insights': insights,
        'blocked_topics': blocked_topics,
    }

def _build_knowledge_dependencies(user: User, db: Session, signals: list[SessionSignal]) -> list[dict]:
    nodes = db.query(KnowledgeGraphNode).filter(KnowledgeGraphNode.user_id == user.id).all()
    weak_nodes = [node for node in nodes if node.status in {'weak', 'not-learned'}]

    dependency_rules = {
        'quadratics': ['algebra foundations', 'linear equations'],
        'polynomials': ['fractions', 'algebra foundations'],
        'calculus': ['functions', 'algebra foundations'],
        'cell respiration': ['photosynthesis basics', 'cell structure'],
        'ww1': ['timeline basics', 'cause/effect reasoning'],
    }

    dependencies: list[dict] = []

    for node in weak_nodes[:4]:
        key = node.topic.lower()
        depends_on = dependency_rules.get(key, ['foundational prerequisites'])
        impacts = [other.topic for other in weak_nodes if other.subject == node.subject and other.topic != node.topic][:2]
        dependencies.append(
            {
                'weak_topic': node.topic,
                'subject': node.subject,
                'depends_on': depends_on,
                'impacts': impacts,
                'insight': f'Weak {node.topic} is likely reducing performance in dependent topics.',
            }
        )

    if not dependencies:
        wrong_topics = [signal.topic for signal in signals if signal.was_correct is False and signal.topic]
        if wrong_topics:
            root = wrong_topics[0]
            dependencies.append(
                {
                    'weak_topic': root,
                    'subject': 'General',
                    'depends_on': dependency_rules.get(root.lower(), ['foundational prerequisites']),
                    'impacts': wrong_topics[1:3],
                    'insight': f'{root} appears to be a root gap affecting nearby topics.',
                }
            )

    return dependencies


def _build_friction_detector(signals: list[SessionSignal]) -> dict:
    if not signals:
        return {
            'score': 0,
            'patterns': ['No friction data yet.'],
            'prompt': 'Track one full session to enable friction detection.',
        }

    page_switches = sum(1 for signal in signals if signal.event_type == 'navigation')
    idle_blocks = sum(1 for signal in signals if (signal.action or '') in {'view', 'open'} and (signal.dwell_seconds or 0) >= 90)
    easy_tasks = sum(1 for signal in signals if signal.task_difficulty == 'easy')
    hard_tasks = sum(1 for signal in signals if signal.task_difficulty == 'hard')
    abandoned = sum(1 for signal in signals if signal.event_type == 'abandon' or 'abandon' in (signal.action or ''))

    total_diff = max(1, easy_tasks + hard_tasks)
    easy_bias = easy_tasks / total_diff

    score = min(100, int(page_switches * 6 + idle_blocks * 8 + abandoned * 15 + easy_bias * 25))

    patterns = []
    if page_switches >= 5:
        patterns.append('Repeated page switching detected')
    if idle_blocks >= 2:
        patterns.append('Opening pages without meaningful actions')
    if easy_bias >= 0.65:
        patterns.append('Repeated easy-task preference during weak-topic window')
    if abandoned >= 1:
        patterns.append('Hard-task abandonment detected')
    if not patterns:
        patterns.append('Low friction pattern this cycle')

    prompt = 'Still studying?' if score >= 35 else 'Good momentum. Keep focus blocks steady.'

    return {
        'score': score,
        'patterns': patterns,
        'prompt': prompt,
    }


def _build_memory_forecast(user: User, db: Session) -> dict:
    rows = db.query(MemoryReviewSchedule).filter(MemoryReviewSchedule.user_id == user.id).all()
    now = datetime.now(timezone.utc)

    immediate = []
    soon = []
    stable = []

    for row in rows:
        next_review = _normalize_datetime(row.next_review_at)
        if row.urgency == 'high' or (next_review and next_review <= now + timedelta(days=1)):
            immediate.append(row.topic)
        elif row.urgency == 'medium' or (next_review and next_review <= now + timedelta(days=3)):
            soon.append(row.topic)
        else:
            stable.append(row.topic)

    return {
        'forget_soon': immediate,
        'review_soon': soon,
        'stable': stable,
        'summary': 'Immediate review required for high-risk topics.' if immediate else 'Memory retention is currently stable.',
    }


def _build_mistake_pattern_intelligence(signals: list[SessionSignal], cognitive: dict) -> dict:
    wrong_signals = [signal for signal in signals if signal.was_correct is False]
    total_attempts = len([signal for signal in signals if signal.was_correct is not None])
    wrong_rate = (len(wrong_signals) / total_attempts) if total_attempts else 0

    by_page = Counter(signal.page for signal in wrong_signals)
    common_error_types = [item['type'] for item in cognitive['breakdown'] if item['count'] > 0][:3]

    if not common_error_types:
        common_error_types = ['No strong repeated error type yet']

    drills = [
        {'title': 'Correction Drill: error log replay', 'focus': common_error_types[0]},
        {'title': 'Timed accuracy drill', 'focus': 'decision speed + verification'},
    ]

    return {
        'common_error_types': common_error_types,
        'where_they_appear': [{'page': page, 'count': count} for page, count in by_page.items()],
        'likely_grade_impact': f'-{int(round(wrong_rate * 22))}% if unchanged this month' if wrong_rate else 'Low immediate impact',
        'correction_drills': drills,
    }


def _build_session_replay(signals: list[SessionSignal]) -> dict:
    if not signals:
        return {
            'strongest_moment': 'No session data yet',
            'most_wasted_time': 'No session data yet',
            'most_valuable_concept': 'No session data yet',
            'most_fragile_concept': 'No session data yet',
            'recommended_next_action': 'Complete one focused block to generate replay insights.',
        }

    strongest = None
    strongest_score = -1
    fragile_counter = Counter()
    value_counter = Counter()

    for signal in signals:
        topic = signal.topic or 'general'
        if signal.was_correct is True:
            value_counter[topic] += 1
            difficulty_weight = 2 if signal.task_difficulty == 'hard' else 1
            score = difficulty_weight * 100 + (signal.self_confidence or 50)
            if score > strongest_score:
                strongest_score = score
                strongest = signal
        elif signal.was_correct is False:
            fragile_counter[topic] += 1

    wasted = max(signals, key=lambda signal: signal.dwell_seconds or 0)
    valuable_topic = value_counter.most_common(1)[0][0] if value_counter else 'general'
    fragile_topic = fragile_counter.most_common(1)[0][0] if fragile_counter else 'general'

    return {
        'strongest_moment': f'Strong execution on {strongest.topic or strongest.page}.' if strongest else 'No correct-attempt signal yet.',
        'most_wasted_time': f'{wasted.page}: {wasted.dwell_seconds or 0}s without clear progress.',
        'most_valuable_concept': valuable_topic,
        'most_fragile_concept': fragile_topic,
        'recommended_next_action': f'Do one targeted correction drill on {fragile_topic}.',
    }
def _build_exam_outcome_simulator(exams: list[ExamSimulation], memory_forecast: dict) -> dict:
    scored = [exam.actual_score for exam in exams if exam.actual_score is not None]
    today_score = int(round(mean(scored))) if scored else 58
    retention_penalty = min(10, len(memory_forecast.get('forget_soon', [])) * 2)
    return {
        'if_exam_today': max(0, today_score - retention_penalty),
        'if_study_30_more_minutes': min(100, today_score + 7),
        'if_fix_one_weak_area': min(100, today_score + 11),
        'if_ignore_retention_risk': max(0, today_score - max(8, retention_penalty + 4)),
    }

def _build_priority_distortion(signals: list[SessionSignal]) -> dict:
    easy_actions = [signal for signal in signals if signal.task_difficulty == 'easy']
    hard_actions = [signal for signal in signals if signal.task_difficulty == 'hard']
    passive = [signal for signal in signals if (signal.action or '') in {'view', 'open'}]
    total = max(1, len(easy_actions) + len(hard_actions))
    easy_ratio = len(easy_actions) / total
    distorted = easy_ratio >= 0.65 and len(hard_actions) <= 1 and len(passive) >= 3

    return {
        'distorted': distorted,
        'false_productivity_signals': [
            'High easy-task repetition',
            'Low high-value challenge attempts',
            'High passive-view time',
        ] if distorted else ['Priority alignment currently stable'],
        'message': 'You are working on what feels productive, not what moves exam outcomes fastest.' if distorted else 'Task priority is aligned with high-value outcomes.',
    }

def _build_study_identity(signals: list[SessionSignal], activity: dict) -> dict:
    easy = sum(1 for signal in signals if signal.task_difficulty == 'easy')
    hard = sum(1 for signal in signals if signal.task_difficulty == 'hard')
    nav = sum(1 for signal in signals if signal.event_type == 'navigation')
    test_actions = sum(1 for signal in signals if signal.page == 'exams')
    passive = sum(1 for signal in signals if (signal.action or '') in {'view', 'open'})

    if activity['learning_consistency'] < 30 and test_actions >= 2:
        return {
            'identity': 'crammer',
            'confidence': 0.72,
            'evidence': ['Low consistency with burst testing behavior'],
            'adaptation': 'Planner adds short high-yield exam-prep blocks.',
        }
    if hard >= easy and hard >= 3:
        return {
            'identity': 'grinder',
            'confidence': 0.72,
            'evidence': ['High hard-task share and sustained execution'],
            'adaptation': 'Planner emphasizes deep-work sprints and challenge sets.',
        }
    if passive >= 4 and easy >= hard:
        return {
            'identity': 'rereader',
            'confidence': 0.72,
            'evidence': ['High passive review compared to active attempts'],
            'adaptation': 'Planner enforces active-recall checkpoints.',
        }
    if nav >= 6 and easy >= 3:
        return {
            'identity': 'avoider',
            'confidence': 0.72,
            'evidence': ['Frequent switches away from challenging tasks'],
            'adaptation': 'Planner locks one hard block before optional tasks.',
        }
    return {
        'identity': 'tester',
        'confidence': 0.72,
        'evidence': ['Frequent assessment-driven behavior'],
        'adaptation': 'Planner uses quiz-feedback loops.',
    }

@router.post('/session-signal', response_model=SessionSignalResponse)
def record_session_signal(payload: SessionSignalRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    signal = SessionSignal(
        user_id=user.id,
        page=payload.page,
        event_type=payload.event_type,
        action=payload.action,
        topic=payload.topic,
        task_difficulty=payload.task_difficulty,
        energy_level=payload.energy_level,
        self_confidence=payload.self_confidence,
        was_correct=payload.was_correct,
        dwell_seconds=payload.dwell_seconds,
        metadata_json=payload.metadata,
    )
    db.add(signal)
    db.commit()

    friction_flags = []
    if payload.event_type == 'navigation' and payload.dwell_seconds < 30:
        friction_flags.append('rapid-page-switching')
    if payload.task_difficulty == 'easy' and payload.action in {'start-task', 'complete-task'}:
        friction_flags.append('easy-task-loop')
    if payload.was_correct is False and (payload.self_confidence or 0) >= 70:
        friction_flags.append('overconfidence-error')

    recommendation = 'Stay on one high-value task for 12 minutes before switching.' if friction_flags else 'Signal logged.'
    return SessionSignalResponse(stored=True, friction_flags=friction_flags, recommendation=recommendation)

@router.post('/autopilot', response_model=AutopilotResponse)
def generate_autopilot(payload: AutopilotRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    signals = _load_recent_signals(user.id, db)
    identity = _build_study_identity(signals, _collect_activity_dates(user.id, db))
    energy = payload.energy_level.lower().strip()
    weak_topic = (payload.weak_topics or ['current weak topic'])[0]
    retention_topic = (payload.retention_risk or ['retention-risk topic'])[0]
    confidence_topic = (payload.confidence_gaps or ['confidence gap area'])[0]

    if energy in {'very low', 'low'}:
        routing = 'Low energy routing: lightweight review first, then one short challenge.'
        plan = [
            {'block_minutes': 15, 'activity': f'Flashcards on {retention_topic}', 'reason': 'prevent immediate forgetting'},
            {'block_minutes': 15, 'activity': f'Error-log replay for {weak_topic}', 'reason': 'target weak area'},
            {'block_minutes': 10, 'activity': f'One medium problem on {confidence_topic}', 'reason': 'close confidence gap'},
            {'block_minutes': 5, 'activity': 'Session reflection + next action commit', 'reason': 'lock consistency'},
        ]
        skip_for_now = ['Hard timed mock exam', 'Long mixed-problem set']
    elif energy in {'high', 'very high'}:
        routing = 'High energy routing: deep work first, then retention stabilization.'
        plan = [
            {'block_minutes': 25, 'activity': f'Hard problem sprint on {weak_topic}', 'reason': 'attack weak core'},
            {'block_minutes': 20, 'activity': f'Timed mini-test on {confidence_topic}', 'reason': 'calibrate confidence'},
            {'block_minutes': 15, 'activity': f'Spaced recall on {retention_topic}', 'reason': 'protect memory stability'},
            {'block_minutes': 10, 'activity': 'Quick replay + update tomorrow target', 'reason': 'close feedback loop'},
        ]
        skip_for_now = ['Passive rereading only']
    else:
        routing = 'Medium energy routing: balanced challenge and retention mix.'
        plan = [
            {'block_minutes': 20, 'activity': f'Medium practice on {weak_topic}', 'reason': 'steady skill build'},
            {'block_minutes': 15, 'activity': f'Concept checks on {confidence_topic}', 'reason': 'reduce uncertainty'},
            {'block_minutes': 10, 'activity': f'Flashcard review on {retention_topic}', 'reason': 'memory reinforcement'},
            {'block_minutes': 10, 'activity': 'Short self-quiz and adjust', 'reason': 'adaptive control'},
        ]
        skip_for_now = ['Low-value busywork with no feedback']

    return AutopilotResponse(
        routing=routing,
        study_identity=identity['identity'],
        plan=plan,
        skip_for_now=skip_for_now,
        switch_rules=[
            'Switch task if two consecutive errors occur on same step.',
            'Switch to review if confidence falls below 35%.',
            'Finish with one retrieval check before ending session.',
        ],
    )

@router.get('/intelligence', response_model=IntelligenceResponse)
def intelligence(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    signals = _load_recent_signals(user.id, db)
    activity = _collect_activity_dates(user.id, db)
    exams = db.query(ExamSimulation).filter(ExamSimulation.user_id == user.id).order_by(ExamSimulation.created_at.desc()).all()

    scored = [exam.actual_score for exam in exams if exam.actual_score is not None]
    fallback_score = int(round(mean(scored))) if scored else 55

    confidence_map = _build_confidence_map(signals, fallback_score)
    cognitive = _build_cognitive_breakdown(signals)
    why_stuck = _build_why_stuck(signals)
    dependencies = _build_knowledge_dependencies(user, db, signals)
    friction = _build_friction_detector(signals)
    memory_forecast = _build_memory_forecast(user, db)
    mistake_intel = _build_mistake_pattern_intelligence(signals, cognitive)
    replay = _build_session_replay(signals)
    outcome_sim = _build_exam_outcome_simulator(exams, memory_forecast)
    priority = _build_priority_distortion(signals)
    identity = _build_study_identity(signals, activity)

    next_best_action = {
        'title': f"Prioritize {memory_forecast['forget_soon'][0]}" if memory_forecast['forget_soon'] else 'Prioritize one weak-area deep block',
        'why': 'Highest impact from retention risk + cognitive weakness alignment.',
        'duration_minutes': 20,
    }

    return IntelligenceResponse(
        confidence_map=confidence_map,
        cognitive_breakdown=cognitive,
        why_stuck=why_stuck,
        knowledge_dependencies=dependencies,
        friction_detector=friction,
        memory_forecast=memory_forecast,
        mistake_pattern_intelligence=mistake_intel,
        session_replay=replay,
        exam_outcome_simulator=outcome_sim,
        priority_distortion=priority,
        study_identity_model=identity,
        next_best_action=next_best_action,
    )





