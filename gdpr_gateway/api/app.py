from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from gdpr_gateway import core
from gdpr_gateway.core.processing import process_text

app = FastAPI(
    title="GDPR Gateway API",
    description="API for GDPR Layer between clients and chat applications",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get('/health', tags=["Health Check"])
async def health_check():
    return JSONResponse(content={"status": "ok"}, status_code=200)


class ClassifyRequest(BaseModel):
    text: Optional[str] = None




@app.post("/process_prompt")
async def process_prompt(req: ClassifyRequest):
    if not req.text:
        raise HTTPException(status_code=400, detail="Missing 'text'")

    return process_text(req.text)

@app.post('/classify')
async def classify(req: ClassifyRequest):
    """Classify text using the combined regex + NER classifier."""
    if not req.text:
        raise HTTPException(status_code=400, detail="Missing 'text' in request body")

    try:
        result = core.classifier.classify_text(req.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return JSONResponse(content=result)


@app.post('/detect_regex', tags=["Classifier"])
async def detect_regex(req: ClassifyRequest):
    """Return only regex-based PII detections."""
    if not req.text:
        raise HTTPException(status_code=400, detail="Missing 'text' in request body")

    try:
        result = core.classifier.detect_pii_regex(req.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return JSONResponse(content=result)

