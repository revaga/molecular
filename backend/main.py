from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import upload_router, nlp_router
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import fitz  # PyMuPDF

from models import MolecularTarget, Therapy, get_db
from services.nlp_service import NlpService

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "ok"}

# Include routers with /api prefix
app.include_router(upload_router, prefix="/api")
app.include_router(nlp_router, prefix="/api")