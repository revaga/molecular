from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import upload_router, nlp_router
from sqlalchemy.orm import Session
from typing import List
import fitz  # PyMuPDF

# Import your SQLAlchemy models, engine, and Base
from models import MolecularTarget, Therapy, get_db, Base, engine
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

# Drop + recreate tables on startup
@app.on_event("startup")
def startup_event():
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("Creating all tables...")
    Base.metadata.create_all(bind=engine)
    print("Database init complete.")

# Include routers with /api prefix
app.include_router(upload_router, prefix="/api")
app.include_router(nlp_router, prefix="/api")
