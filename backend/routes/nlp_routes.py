from fastapi import APIRouter
from pydantic import BaseModel
from services.nlp_service import NlpService

router = APIRouter()
nlp_service = NlpService()

class TextRequest(BaseModel):
    text: str

@router.post("/api/extract_entities")
async def extract_entities(request: TextRequest):
    # Get the list of extracted entities with their PFS values
    entities = nlp_service.extract_entities(request.text)
    
    # Optionally, aggregate PFS values if needed (e.g., averaging MY, MN, H)
    avg_MY = sum([entity['MY'] for entity in entities]) / len(entities) if entities else 0
    avg_MN = sum([entity['MN'] for entity in entities]) / len(entities) if entities else 0
    avg_H = sum([entity['H'] for entity in entities]) / len(entities) if entities else 0

    aggregated_result = {
        "entities": entities,
        "avg_MY": avg_MY,
        "avg_MN": avg_MN,
        "avg_H": avg_H
    }

    return aggregated_result


def aggregate_pfs_values(entities_list):
    """
    Aggregate PFS values (MY, MN, H) across multiple entities or chunks.
    """
    total_MY = sum([entity['MY'] for entity in entities_list])
    total_MN = sum([entity['MN'] for entity in entities_list])
    total_H = sum([entity['H'] for entity in entities_list])

    avg_MY = total_MY / len(entities_list) if entities_list else 0
    avg_MN = total_MN / len(entities_list) if entities_list else 0
    avg_H = total_H / len(entities_list) if entities_list else 0

    return avg_MY, avg_MN, avg_H



"""
example JSON output

{
    "entities": [
        {
            "text": "BRCA1",
            "label": "GENE",
            "score": 0.9987,
            "MY": 0.9987,
            "MN": 0.0464,
            "H": 0.0109
        },
        {
            "text": "Tamoxifen",
            "label": "DRUG",
            "score": 0.9876,
            "MY": 0.9876,
            "MN": 0.1578,
            "H": 0.0304
        }
    ],
    "avg_MY": 0.99315,
    "avg_MN": 0.1021,
    "avg_H": 0.0207
}

"""