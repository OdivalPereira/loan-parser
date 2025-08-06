import os
import uuid
import csv
from datetime import datetime, date
from io import StringIO
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from redis import Redis
from rq import Queue

app = FastAPI()

redis_host = os.environ.get("REDIS_HOST", "redis")
redis_port = int(os.environ.get("REDIS_PORT", 6379))
redis_conn = Redis(host=redis_host, port=redis_port)
queue = Queue("uploads", connection=redis_conn)

storage_path = os.environ.get("UPLOAD_DIR", "storage")
os.makedirs(storage_path, exist_ok=True)


# Sample in-memory contract data used for accrual calculations.
# In a real application this would come from a database.
CONTRACTS = [
    {
        "id": "1",
        "principal": 10000.0,
        "annual_rate": 0.12,
        "start_date": date(2024, 1, 1),
    },
    {
        "id": "2",
        "principal": 20000.0,
        "annual_rate": 0.15,
        "start_date": date(2024, 2, 15),
    },
]


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


@app.get("/accruals/export")
def export_accruals(start_date: str, end_date: str):
    """Export pro-rata interest accruals for contracts within a period.

    The interest is calculated using the formula:
    interest = principal * annual_rate * days / 365
    """

    try:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid date format. Use YYYY-MM-DD"
        )

    if start > end:
        raise HTTPException(
            status_code=400, detail="start_date must be before end_date"
        )

    def iter_rows():
        header_buffer = StringIO()
        writer = csv.writer(header_buffer)
        writer.writerow(["contract_id", "principal", "annual_rate", "days", "interest"])
        yield header_buffer.getvalue()

        for contract in CONTRACTS:
            contract_start = contract["start_date"]
            period_start = max(start, contract_start)
            if period_start > end:
                continue
            days = (end - period_start).days + 1
            interest = contract["principal"] * contract["annual_rate"] * days / 365

            row_buffer = StringIO()
            writer = csv.writer(row_buffer)
            writer.writerow(
                [
                    contract["id"],
                    f"{contract['principal']:.2f}",
                    contract["annual_rate"],
                    days,
                    f"{interest:.2f}",
                ]
            )
            yield row_buffer.getvalue()

    headers = {"Content-Disposition": "attachment; filename=accruals.csv"}
    return StreamingResponse(iter_rows(), media_type="text/csv", headers=headers)
