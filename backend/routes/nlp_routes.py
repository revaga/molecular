from fastapi import APIRouter
from services.nlp_service import NlpService

router = APIRouter()

nlp_service = NlpService()

@router.post("/extract_entities")
async def extract_entities(text: str):
    entities = nlp_service.extract_entities(text)
    return {"entities": entities}
