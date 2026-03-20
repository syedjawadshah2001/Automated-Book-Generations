from fastapi import FastAPI

from app.api import router

app = FastAPI(title="Automated Book Generation System", version="0.1.0")
app.include_router(router)
