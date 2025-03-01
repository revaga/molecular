from fastapi import FastAPI
from routes.nlp_routes import router as nlp_router

app = FastAPI()

app.include_router(nlp_router)