from fastapi import APIRouter

from app.models.schemas import DraftRequest, DraftResponse
from app.services.drafting import draft_message

router = APIRouter()


@router.post("/draft", response_model=DraftResponse)
def draft(request: DraftRequest) -> DraftResponse:
    return draft_message(request)
