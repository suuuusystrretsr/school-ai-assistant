from pydantic import BaseModel, Field


class StudyRoomCreateRequest(BaseModel):
    title: str = Field(min_length=2)
    subject: str


class StudyRoomResponse(BaseModel):
    id: int
    title: str
    subject: str
    host_user_id: int
    max_participants: int
    participant_count: int


class RoomInviteRequest(BaseModel):
    invited_user_email: str


class RoomMessageRequest(BaseModel):
    content: str


class RoomMessageResponse(BaseModel):
    id: int
    room_id: int
    user_id: int
    content: str
    message_type: str
