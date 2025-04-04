from fastapi import APIRouter, UploadFile, HTTPException, Depends
from sqlalchemy.orm import Session
import fitz  # PyMuPDF
import os
from typing import List, Dict
from models import MolecularTarget, Therapy, get_db
from services.nlp_service import NlpService
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
nlp_service = NlpService()

# Maximum file size (20MB in bytes)
MAX_FILE_SIZE = 20 * 1024 * 1024

def split_text_into_segments(text: str, words_per_segment: int = 50) -> List[str]:
    """Split text into segments of approximately words_per_segment words."""
    words = text.split()
    segments = []
    for i in range(0, len(words), words_per_segment):
        segment = " ".join(words[i:i + words_per_segment])
        segments.append(segment)
    return segments

@router.post("/upload")
async def upload_pdf(file: UploadFile, db: Session = Depends(get_db)):
    """Upload and process a PDF file."""
    try:
        logger.info(f"[UPLOAD] Starting processing for file: {file.filename}")
        
        if not file.filename.lower().endswith('.pdf'):
            logger.warning("[UPLOAD] Invalid file type.")
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        content = await file.read()
        logger.info(f"[UPLOAD] File size: {len(content)} bytes")
        
        if len(content) > MAX_FILE_SIZE:
            logger.warning("[UPLOAD] File too large.")
            raise HTTPException(status_code=400, detail="File size exceeds 20MB limit")
        
        # Open and read PDF content
        try:
            doc = fitz.open(stream=content, filetype="pdf")
            text_content = []

            logger.info(f"[PDF] Total pages: {len(doc)}")

            for i, page in enumerate(doc):
                page_text = page.get_text()
                logger.info(f"[PDF] Extracted text from page {i+1}: {repr(page_text[:200])}...")
                text_content.append(page_text)

            full_text = " ".join(text_content).strip()

            if not full_text:
                logger.warning("[PDF] No text extracted from PDF.")
                raise HTTPException(status_code=400, detail="No text found in PDF")

            segments = split_text_into_segments(full_text)
            logger.info(f"[TEXT] Total segments: {len(segments)}")

            all_entities = []
            true_labels = []
            pred_labels = []

            for i, segment in enumerate(segments):
                logger.info(f"[NLP] Processing segment {i+1}: {repr(segment[:150])}...")

                entities = nlp_service.extract_entities(segment)
                logger.info(f"[NLP] Found {len(entities)} entities in segment {i+1}")

                for entity in entities:
                    logger.info(f"[NLP] Entity: {json.dumps(entity)}")
                    if entity['entity_type'] in ('DISEASE', 'ANATOMICAL'):
                        db.add(MolecularTarget(
                            name=entity['text'],
                            my=entity['my'],
                            mn=entity['mn'],
                            hesitancy=entity['hesitancy'],
                            confidence=entity['confidence'],
                            entity_type=entity['entity_type']
                        ))
                    elif entity['entity_type'] == 'DRUG':
                        db.add(Therapy(
                            name=entity['text'],
                            entity_type=entity["entity_type"],
                            my=entity['my'],
                            mn=entity['mn'],
                            hesitancy=entity['hesitancy'],
                            confidence=entity['confidence']                        ))

                all_entities.extend(entities)
                pred_labels.extend([e['entity_type'] for e in entities])
                true_labels.extend(['UNKNOWN'] * len(entities))

            db.commit()
            logger.info(f"[DB] Committed {len(all_entities)} entities to database.")

            metrics = {}
            if all_entities:
                metrics = nlp_service.calculate_metrics(true_labels, pred_labels)
                logger.info(f"[METRICS] Calculated metrics: {metrics}")
            else:
                logger.warning("[NLP] No entities found in any segment.")

            return {
                "message": "PDF processed successfully",
                "filename": file.filename,
                "segment_count": len(segments),
                "entities": all_entities,
                "metrics": metrics
            }

        except Exception as e:
            logger.exception("[ERROR] Failed to process PDF")
            raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

    except Exception as e:
        logger.exception("[ERROR] Upload handling failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/guidelines")
async def get_guidelines(target: str, type: str, db: Session = Depends(get_db)):
    """Generate handling guidelines for a target."""
    try:
        guidelines = nlp_service.generate_guidelines(target, type)
        return {"guidelines": guidelines}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating guidelines: {str(e)}")

@router.get("/results")
async def get_results(db: Session = Depends(get_db)):
    """Get all stored molecular targets and therapies with their PFS metrics."""
    try:
        molecular_targets = db.query(MolecularTarget).all()
        therapies = db.query(Therapy).all()
        
        return {
            "molecular_targets": [target.to_dict() for target in molecular_targets],
            "therapies": [therapy.to_dict() for therapy in therapies]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching results: {str(e)}")
