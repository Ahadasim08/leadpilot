from fastapi import FastAPI

from app.routers import score, draft

app = FastAPI(title="LeadPilot API")

app.include_router(score.router)
app.include_router(draft.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "leadpilot"}
