from fastapi import APIRouter

from app.models.schemas import Lead, ScoreResponse
from app.services.scoring import score_lead

router = APIRouter()


@router.post("/score", response_model=ScoreResponse)
def score(lead: Lead) -> ScoreResponse:
    return score_lead(lead)
