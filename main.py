from fastapi import FastAPI
import uvicorn
from app.v1.routers.detail_extraction import router as detail_router

app = FastAPI(title="Invoice Extractor")

app.include_router(detail_router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "Async Invoice Extraction API Ready"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)