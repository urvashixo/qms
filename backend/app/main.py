from __future__ import annotations

import io
import json
import re
from datetime import datetime
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pypdf import PdfReader
from sqlalchemy.orm import Session
from .agent import process_request
from .database import Base, engine, get_db
from .models import Complaint
from .schemas import CommitRequest, ComplaintForm, CopilotRequest, CopilotResponse

Base.metadata.create_all(bind=engine)
app = FastAPI(title="AIVOA Complaint Copilot", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.get("/api/health")
def health():
    return {"status": "healthy", "service": "aivoa-copilot"}


@app.post("/api/copilot", response_model=CopilotResponse)
def copilot(request: CopilotRequest):
    return process_request(request)


@app.post("/api/documents", response_model=CopilotResponse)
async def document_extract(file: UploadFile = File(...)):
    content = await file.read()
    if len(content) > 8_000_000:
        raise HTTPException(413, "Document must be smaller than 8MB")
    try:
        if file.filename.lower().endswith(".pdf"):
            text = "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(content)).pages)
        else:
            text = content.decode("utf-8", errors="ignore")
    except Exception as exc:
        raise HTTPException(422, "AIVOA could not read this document") from exc
    if not text.strip():
        raise HTTPException(422, "No readable complaint text was found")
    response = process_request(CopilotRequest(message=text, current_form=ComplaintForm()), mode="extracted")
    response.message = f"Extracted complaint details from {file.filename}. Review the AI-populated QMS record and continue editing through the copilot."
    return response


@app.post("/api/complaints")
def commit(request: CommitRequest, db: Session = Depends(get_db)):
    ref = f"CMP-{datetime.utcnow():%Y%m%d}-{datetime.utcnow().microsecond:06d}"
    complaint = Complaint(reference=ref, customer_name=request.form.customer_name, product_name=request.form.product_name, batch_number=request.form.batch_number, payload=json.dumps(request.model_dump()))
    db.add(complaint)
    db.commit()
    return {"reference": ref, "status": "Committed to QMS ledger"}


@app.get("/api/complaints")
def ledger(db: Session = Depends(get_db)):
    return [{"reference": c.reference, "customer_name": c.customer_name, "product_name": c.product_name, "batch_number": c.batch_number, "created_at": c.created_at.isoformat()} for c in db.query(Complaint).order_by(Complaint.id.desc()).limit(20)]

