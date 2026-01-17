from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
import uuid
from pathlib import Path
from redis import Redis
from rq import Queue, job
from app.v1.core.pdf_extraction import extract_invoice_data
from app.v1.models.detail_extraction import InvoiceResponse
from app.v1.common.common_uitls import create_excel_from_pdf, create_excel_file

# Redis connection
redis_conn = Redis(host='localhost', port=6379, db=0)
queue = Queue(connection=redis_conn)

# Output directory
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

router = APIRouter(prefix="/detail", tags=["extraction"])

@router.post("/extract", response_model=InvoiceResponse)
async def extract_details(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")

    content = await file.read()

    # Extract data
    data = await extract_invoice_data(content)

    # Save Excel (awaited properly)
    await create_excel_from_pdf(
        content,
        file.filename.replace(".pdf", "")
    )

    return InvoiceResponse(**data.model_dump())

@router.post("/batch-extract")
async def batch_extract(files: list[UploadFile] = File(...)):
    if not all(f.filename.lower().endswith('.pdf') for f in files):
        raise HTTPException(400, "All PDFs only")
    
    session_id = str(uuid.uuid4())
    jobs = []
    
    for file in files:
        content = await file.read()
        job = queue.enqueue(
            create_excel_from_pdf, 
            content, 
            file.filename, 
            session_id,
            job_id=f"{session_id}:{file.filename}"
        )
        jobs.append({"job_id": job.id, "filename": file.filename, "status": "queued"})
    
    redis_conn.hset(f"session:{session_id}", "jobs_count", len(jobs))
    redis_conn.expire(f"session:{session_id}", 86400)  # 24h TTL
    return {"session_id": session_id, "jobs": jobs, "output_dir": str(OUTPUT_DIR)}

@router.get("/status/{session_id}")
async def get_status(session_id: str):
    if not redis_conn.exists(f"session:{session_id}"):
        raise HTTPException(404, "Session not found")
    
    job_keys = redis_conn.keys(f"{session_id}:*")
    jobs = []
    for key in job_keys:
        job_id = key.decode()
        try:
            rq_job = job.fetch(job_id, connection=redis_conn)
            result = rq_job.result
            jobs.append({
                "job_id": job_id,
                "status": rq_job.get_status(),
                "excel_file": result if result else None
            })
        except Exception:
            jobs.append({"job_id": job_id, "status": "failed", "excel_file": None})
    
    return {"session_id": session_id, "jobs": jobs}

@router.get("/download/{session_id}/{filename}")
async def download_excel(session_id: str, filename: str):
    excel_path = OUTPUT_DIR / f"{session_id}_{filename}.xlsx"
    if not excel_path.exists():
        raise HTTPException(404, "Excel file not found")
    return FileResponse(
        excel_path, 
        filename=excel_path.name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@router.post("/to-excel")
async def export_excel(file: UploadFile = File(...)):
    content = await file.read()
    data = await extract_invoice_data(content)
    
    excel_path = OUTPUT_DIR / f"single_{file.filename}.xlsx"
    create_excel_file(data, str(file.filename), excel_path)
    
    return FileResponse(
        excel_path,
        filename=excel_path.name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
