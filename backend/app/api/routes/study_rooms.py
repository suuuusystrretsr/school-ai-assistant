
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.study_room import RoomInvite, RoomMembership, RoomMessage, StudyRoom
from app.models.user import User
from app.schemas.study_room import RoomInviteRequest, RoomMessageRequest, RoomMessageResponse, StudyRoomCreateRequest, StudyRoomResponse
from app.services.collab.rooms import accept_invite, create_invite, create_room, current_participant_count, ensure_capacity

router = APIRouter(prefix='/study-rooms', tags=['study-rooms'])


@router.post('', response_model=StudyRoomResponse)
def create_study_room(payload: StudyRoomCreateRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    room = create_room(db, host_user_id=user.id, title=payload.title, subject=payload.subject)
    return StudyRoomResponse(
        id=room.id,
        title=room.title,
        subject=room.subject,
        host_user_id=room.host_user_id,
        max_participants=room.max_participants,
        participant_count=current_participant_count(db, room.id),
    )


@router.get('', response_model=list[StudyRoomResponse])
def list_rooms(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rooms = db.query(StudyRoom).filter(StudyRoom.is_active.is_(True)).all()
    return [
        StudyRoomResponse(
            id=room.id,
            title=room.title,
            subject=room.subject,
            host_user_id=room.host_user_id,
            max_participants=room.max_participants,
            participant_count=current_participant_count(db, room.id),
        )
        for room in rooms
    ]


@router.post('/{room_id}/invite')
def invite_to_room(room_id: int, payload: RoomInviteRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    room = db.get(StudyRoom, room_id)
    if not room:
        raise HTTPException(status_code=404, detail='Room not found')
    if room.host_user_id != user.id:
        raise HTTPException(status_code=403, detail='Only host can send invites')

    target = db.query(User).filter(User.email == payload.invited_user_email).first()
    if not target:
        raise HTTPException(status_code=404, detail='Invited user not found')
    if not ensure_capacity(db, room.id):
        raise HTTPException(status_code=400, detail='Room reached max capacity (5 participants)')

    invite = create_invite(db, room.id, user.id, target.id)
    return {'invite_token': invite.invite_token, 'status': invite.status}


@router.post('/invites/{invite_token}/accept')
def accept_room_invite(invite_token: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    invite = db.query(RoomInvite).filter(RoomInvite.invite_token == invite_token).first()
    if not invite or invite.invited_user_id != user.id:
        raise HTTPException(status_code=404, detail='Invite not found')
    if invite.status != 'pending':
        raise HTTPException(status_code=400, detail='Invite already processed')

    try:
        membership = accept_invite(db, invite)
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err)) from err

    return {'room_id': membership.room_id, 'status': 'joined'}


@router.get('/{room_id}/messages', response_model=list[RoomMessageResponse])
def list_messages(room_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(RoomMessage).filter(RoomMessage.room_id == room_id).order_by(RoomMessage.created_at.asc()).all()
    return [
        RoomMessageResponse(
            id=row.id,
            room_id=row.room_id,
            user_id=row.user_id,
            content=row.content,
            message_type=row.message_type,
        )
        for row in rows
    ]


@router.post('/{room_id}/messages', response_model=RoomMessageResponse)
def post_message(room_id: int, payload: RoomMessageRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    member = db.query(RoomMembership).filter(RoomMembership.room_id == room_id, RoomMembership.user_id == user.id).first()
    if not member:
        raise HTTPException(status_code=403, detail='Join the room before posting')

    msg = RoomMessage(room_id=room_id, user_id=user.id, content=payload.content, message_type='chat')
    db.add(msg)
    db.commit()
    db.refresh(msg)

    return RoomMessageResponse(
        id=msg.id,
        room_id=msg.room_id,
        user_id=msg.user_id,
        content=msg.content,
        message_type=msg.message_type,
    )
