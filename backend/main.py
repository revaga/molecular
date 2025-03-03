from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.nlp_routes import router as nlp_router
from routes.upload import router as upload_router

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
async def root():
    return {
        "message": "Molecular API is running",
        "endpoints": {
            "Entity Extraction": "/api/extract_entities",
            "PDF Upload": "/api/upload"
        }
    }

app.include_router(nlp_router)
app.include_router(upload_router)