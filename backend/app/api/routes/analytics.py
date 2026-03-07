
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.analytics import AnalyticsSnapshot
from app.models.knowledge import KnowledgeGraphNode, MemoryReviewSchedule
from app.models.user import StudyBuddyState, User
from app.schemas.analytics import DashboardAnalyticsResponse, LearningSignalRequest
from app.services.analytics.signals import detect_confusion
from app.services.planner.memory import compute_memory_strength, next_review_from_strength

router = APIRouter(prefix='/analytics', tags=['analytics'])


@router.get('/dashboard', response_model=DashboardAnalyticsResponse)
def dashboard(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    snapshot = (
        db.query(AnalyticsSnapshot)
        .filter(AnalyticsSnapshot.user_id == user.id)
        .order_by(AnalyticsSnapshot.created_at.desc())
        .first()
    )
    if not snapshot:
        snapshot = AnalyticsSnapshot(
            user_id=user.id,
            subject_progress={'Math': 64, 'Biology': 58, 'History': 72},
            mastery_by_topic={'Linear equations': 0.8, 'Quadratics': 0.43, 'Polynomials': 0.2},
            recent_performance={'last_7_days': [65, 70, 72, 68, 74, 76, 78]},
            practice_accuracy=71,
            readiness_score=69,
            learning_consistency=62,
            streak_days=5,
            retention_forecast={'next_3_days_risk': ['Quadratics', 'Cell respiration']},
            distraction_risk='medium',
        )
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)

    buddy = db.query(StudyBuddyState).filter(StudyBuddyState.user_id == user.id).first()
    if not buddy:
        db.add(StudyBuddyState(user_id=user.id, streak_days=3, consistency_score=60, mood='motivated', nudges=[]))
        db.commit()

    confusion_detector = {'status': 'monitoring', 'message': 'Need a hint? prompt appears only when confusion is detected.'}
    focus_mode = {'enabled': False, 'suggestion': 'Start a 25/5 focus cycle for deeper work.'}

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
def upsert_knowledge_node(subject: str, topic: str, mastery_score: float, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    node = (
        db.query(KnowledgeGraphNode)
        .filter(KnowledgeGraphNode.user_id == user.id, KnowledgeGraphNode.subject == subject, KnowledgeGraphNode.topic == topic)
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
        buddy = StudyBuddyState(user_id=user.id, streak_days=0, consistency_score=50, mood='focused', nudges=[])
        db.add(buddy)
        db.commit()
        db.refresh(buddy)

    return {
        'streak_days': buddy.streak_days,
        'consistency_score': buddy.consistency_score,
        'mood': buddy.mood,
        'nudges': buddy.nudges,
    }
