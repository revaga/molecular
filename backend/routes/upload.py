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
        logger.info(f"Processing upload for file: {file.filename}")
        
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
            
        # Check file size
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File size exceeds 20MB limit")
            
        logger.info("File read successfully")
        
        try:
            # Open PDF with PyMuPDF
            doc = fitz.open(stream=content, filetype="pdf")
            text_content = []
            
            # Extract text from each page
            for page in doc:
                text_content.append(page.get_text())
                
            # Join all text and split into segments
            full_text = " ".join(text_content)
            segments = split_text_into_segments(full_text)
            
            # Process each segment with NLP service
            all_entities = []
            true_labels = []  # For metrics calculation
            pred_labels = []
            
            for segment in segments:
                # Extract entities with PFS metrics
                entities = nlp_service.extract_entities(segment)
                
                # Store entities in database
                for entity in entities:
                    if entity['entity_type'] == 'DISEASE' or entity['entity_type'] == 'ANATOMICAL':
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
                            my=entity['my'],
                            mn=entity['mn'],
                            hesitancy=entity['hesitancy'],
                            confidence=entity['confidence'],
                            entity_type=entity['entity_type']
                        ))
                
                all_entities.extend(entities)
                
                # Collect labels for metrics (simplified example)
                pred_labels.extend([e['entity_type'] for e in entities])
                true_labels.extend(['UNKNOWN'] * len(entities))  # Replace with actual labels if available
            
            db.commit()
            
            # Only calculate metrics if we have entities
            metrics = {}
            if all_entities:
                metrics = nlp_service.calculate_metrics(true_labels, pred_labels)
            
            return {
                "message": "PDF processed successfully",
                "filename": file.filename,
                "segment_count": len(segments),
                "entities": all_entities,
                "metrics": metrics
            }
            
        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")
            
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
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
