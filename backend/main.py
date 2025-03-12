from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.nlp_routes import router as nlp_router
from routes.upload import router as upload_router
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import fitz  # PyMuPDF

from models import MolecularTarget, Therapy, get_db
from services.nlp_service import NlpService

app = FastAPI()
nlp_service = NlpService()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "Molecular API is running",
        "endpoints": {
            "Entity Extraction": "/api/extract_entities",
            "PDF Upload": "/api/upload",
            "Molecular Target and Therapy Extraction": "/upload/",
            "Get Results": "/results/",
            "Get Guidelines": "/guidelines/{target}"
        }
    }

@app.post("/upload/")
async def upload_pdf(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        content = await file.read()
        doc = fitz.open(stream=content, filetype="pdf")
        text = " ".join([page.get_text() for page in doc])

        # Extract and process entities
        entities = nlp_service.extract_entities_with_pfs(text)

        # Store entities in database
        for entity in entities:
            if entity['type'] in {'GENE', 'PROTEIN', 'PATHWAY'}:
                db.add(MolecularTarget(**entity))
            else:
                db.add(Therapy(**entity))
        db.commit()

        return {"message": "Processing complete", "total_extracted": len(entities)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/results/")
def get_results(db: Session = Depends(get_db)):
    targets = db.query(MolecularTarget).all()
    therapies = db.query(Therapy).all()
    return {"molecular_targets": targets, "therapies": therapies}

@app.get("/guidelines/{target}")
def get_guidelines(target: str, db: Session = Depends(get_db)):
    # Find target in database
    db_target = db.query(MolecularTarget).filter(MolecularTarget.name == target).first()
    if not db_target:
        raise HTTPException(status_code=404, detail="Target not found")
    
    # Generate context from target information
    context = f"Target {target} with confidence {db_target.confidence:.2f}, " \
              f"MY: {db_target.my:.2f}, MN: {db_target.mn:.2f}, Hesitancy: {db_target.hesitancy:.2f}"
    
    # Generate guidelines
    guidelines = nlp_service.generate_guidelines(target, context)
    
    return {
        "target": target,
        "context": context,
        "guidelines": guidelines
    }

app.include_router(nlp_router)
app.include_router(upload_router)