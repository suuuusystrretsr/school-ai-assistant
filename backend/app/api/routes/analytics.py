from collections import defaultdict
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
from app.models.user import StudyBuddyState, User
from app.schemas.analytics import DashboardAnalyticsResponse, LearningSignalRequest
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
    snapshot.distraction_risk = 'low'

    db.add(snapshot)
    db.commit()

    confusion_detector = {
        'status': 'monitoring',
        'message': 'Need a hint? appears only when confusion signals are detected.',
    }
    focus_mode = {
        'enabled': False,
        'suggestion': 'Start a 25/5 focus cycle for deeper work.',
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

