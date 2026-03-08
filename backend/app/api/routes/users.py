from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User, UserProfile
from app.schemas.user import UserProfileResponse, UserProfileUpdate, UserResponse

router = APIRouter(prefix='/users', tags=['users'])


@router.get('/me', response_model=UserResponse)
def get_me(user: User = Depends(get_current_user)):
    return user


@router.get('/me/profile', response_model=UserProfileResponse)
def get_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    if not profile:
        profile = UserProfile(user_id=user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


@router.patch('/me/profile', response_model=UserProfileResponse)
def update_profile(payload: UserProfileUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    if not profile:
        profile = UserProfile(user_id=user.id)

    for key, value in payload.model_dump(exclude_none=True).items():
        setattr(profile, key, value)

    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile
