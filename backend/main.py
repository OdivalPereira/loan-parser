import os
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException
from redis import Redis
from rq import Queue

app = FastAPI()

redis_host = os.environ.get("REDIS_HOST", "redis")
redis_port = int(os.environ.get("REDIS_PORT", 6379))
redis_conn = Redis(host=redis_host, port=redis_port)
queue = Queue("uploads", connection=redis_conn)

storage_path = os.environ.get("UPLOAD_DIR", "storage")
os.makedirs(storage_path, exist_ok=True)

@app.post("/uploads")
async def upload_pdf(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    file_id = f"{uuid.uuid4()}.pdf"
    dest = os.path.join(storage_path, file_id)
    content = await file.read()
    with open(dest, "wb") as f:
        f.write(content)
    queue.enqueue("tasks.parse_sicoob", dest)
    return {"id": file_id, "filename": file.filename}
