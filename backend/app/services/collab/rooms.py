import secrets

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.study_room import RoomInvite, RoomMembership, StudyRoom

MAX_PARTICIPANTS = 5


def create_room(db: Session, host_user_id: int, title: str, subject: str) -> StudyRoom:
    room = StudyRoom(host_user_id=host_user_id, title=title, subject=subject, max_participants=MAX_PARTICIPANTS)
    db.add(room)
    db.flush()
    db.add(RoomMembership(room_id=room.id, user_id=host_user_id, role='host', is_present=True))
    db.commit()
    db.refresh(room)
    return room


def current_participant_count(db: Session, room_id: int) -> int:
    return int(db.query(func.count(RoomMembership.id)).filter(RoomMembership.room_id == room_id).scalar() or 0)


def ensure_capacity(db: Session, room_id: int) -> bool:
    count = current_participant_count(db, room_id)
    room = db.get(StudyRoom, room_id)
    if not room:
        return False
    return count < room.max_participants


def create_invite(db: Session, room_id: int, invited_by_user_id: int, invited_user_id: int) -> RoomInvite:
    token = secrets.token_urlsafe(16)
    invite = RoomInvite(
        room_id=room_id,
        invited_by_user_id=invited_by_user_id,
        invited_user_id=invited_user_id,
        status='pending',
        invite_token=token,
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return invite


def accept_invite(db: Session, invite: RoomInvite) -> RoomMembership:
    if not ensure_capacity(db, invite.room_id):
        raise ValueError('Room already at max capacity (5 participants).')
    membership = RoomMembership(room_id=invite.room_id, user_id=invite.invited_user_id, role='participant', is_present=True)
    invite.status = 'accepted'
    db.add(membership)
    db.commit()
    db.refresh(membership)
    return membership
