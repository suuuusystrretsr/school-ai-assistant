from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.flashcard import Flashcard, FlashcardDeck
from app.models.user import User
from app.schemas.flashcards import FlashcardDeckResponse, FlashcardGenerateRequest, FlashcardItem
from app.services.ai.factory import get_ai_provider

router = APIRouter(prefix='/flashcards', tags=['flashcards'])
ai = get_ai_provider()


@router.post('/generate', response_model=FlashcardDeckResponse)
def generate_flashcards(payload: FlashcardGenerateRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    deck = FlashcardDeck(
        user_id=user.id,
        title=payload.title,
        source_text=payload.source_text,
        source_type=payload.source_type,
    )
    db.add(deck)
    db.flush()

    cards_data = ai.generate_flashcards(payload.source_text)
    for item in cards_data:
        db.add(
            Flashcard(
                deck_id=deck.id,
                question=item['question'],
                answer=item['answer'],
                topic_tags=item['topic_tags'],
                difficulty_tag=item['difficulty_tag'],
                spaced_repetition_ready=True,
            )
        )

    db.commit()
    return FlashcardDeckResponse(deck_id=deck.id, title=deck.title, cards=[FlashcardItem(**item) for item in cards_data])
