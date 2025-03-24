from fastapi import APIRouter, UploadFile, HTTPException, Depends
from sqlalchemy.orm import Session
import fitz  # PyMuPDF
import os
from typing import List, Dict
from models import MolecularTarget, Therapy, get_db
from services.nlp_service import NlpService
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
nlp_service = NlpService()

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
        
        # Read file content
        content = await file.read()
        logger.info("File read successfully")
        
        try:
            # Open PDF with PyMuPDF
            doc = fitz.open(stream=content, filetype="pdf")
            text_content = []
            
            # Extract text from each page
            for page in doc:
                text = page.get_text()
                text_content.append(text)
                logger.info(f"Extracted text from page, length: {len(text)}")
            
            # Close the document
            doc.close()
            
            # Combine all text and split into segments
            full_text = " ".join(text_content)
            segments = split_text_into_segments(full_text)
            logger.info(f"Split text into {len(segments)} segments")
            
            # Process each segment with NLP
            all_entities = []
            for i, segment in enumerate(segments):
                try:
                    logger.info(f"Processing segment {i+1}/{len(segments)}")
                    logger.info(f"Segment text: {segment[:100]}...")  # Log first 100 chars
                    
                    entities = nlp_service.extract_entities_with_pfs(segment)
                    logger.info(f"Found {len(entities)} entities in segment {i+1}")
                    
                    if entities:
                        logger.info(f"Entities found: {[e['text'] for e in entities]}")
                    all_entities.extend(entities)
                except Exception as e:
                    logger.error(f"Error processing segment {i+1}: {str(e)}")
                    continue
            
            logger.info(f"Total entities found: {len(all_entities)}")
            
            # Store entities in database
            stored_targets = 0
            stored_therapies = 0
            
            for entity in all_entities:
                try:
                    if entity['type'] in {'GENE', 'PROTEIN', 'PATHWAY'}:
                        target = MolecularTarget(
                            name=entity['text'],
                            my=entity['MY'],
                            mn=entity['MN'],
                            hesitancy=entity['hesitancy'],
                            confidence=entity['confidence']
                        )
                        db.add(target)
                        stored_targets += 1
                    elif entity['type'] in {'DRUG', 'INHIBITOR', 'ANTIBODY'}:
                        therapy = Therapy(
                            name=entity['text'],
                            my=entity['MY'],
                            mn=entity['MN'],
                            hesitancy=entity['hesitancy'],
                            confidence=entity['confidence']
                        )
                        db.add(therapy)
                        stored_therapies += 1
                except Exception as e:
                    logger.error(f"Error storing entity {entity['text']}: {str(e)}")
                    continue
            
            try:
                db.commit()
                logger.info(f"Stored {stored_targets} targets and {stored_therapies} therapies")
            except Exception as e:
                db.rollback()
                logger.error(f"Database commit error: {str(e)}")
                raise HTTPException(status_code=500, detail="Error saving to database")
            
            response_data = {
                "filename": file.filename,
                "segment_count": len(segments),
                "text_segments": segments,
                "entities": all_entities,
                "stats": {
                    "total_entities": len(all_entities),
                    "stored_targets": stored_targets,
                    "stored_therapies": stored_therapies
                }
            }
            logger.info("Upload processing completed successfully")
            return response_data
            
        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")
            
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/results")
def get_results(db: Session = Depends(get_db)):
    """Get all stored molecular targets and therapies with their PFS metrics"""
    try:
        targets = db.query(MolecularTarget).all()
        therapies = db.query(Therapy).all()
        return {
            "molecular_targets": [target.to_dict() for target in targets],
            "therapies": [therapy.to_dict() for therapy in therapies]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving results: {str(e)}")

@router.get("/guidelines/{target_name}")
def get_guidelines(target_name: str, db: Session = Depends(get_db)):
    """Get NLP-generated handling guidelines for a specific target"""
    try:
        target = db.query(MolecularTarget).filter(MolecularTarget.name == target_name).first()
        if not target:
            raise HTTPException(status_code=404, detail=f"Target {target_name} not found")
        
        guidelines = nlp_service.generate_guidelines(target_name)
        return {"guidelines": guidelines}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating guidelines: {str(e)}")
