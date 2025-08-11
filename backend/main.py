import os
import uuid
import csv
import logging
from datetime import datetime, date
from io import StringIO
from typing import List, Iterable

from fastapi import Depends, FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from rq import Queue
from sqlalchemy.orm import Session

from backend.config import get_redis
from .db import SessionLocal
from .models import Contrato, Movimentacao, Extrato
from .rules import classify


class ContractResponse(BaseModel):
    id: str
    bank: str
    balance: float
    cet: float
    dueDate: date

    class Config:
        orm_mode = True


app = FastAPI()
logger = logging.getLogger(__name__)

redis_conn = get_redis()
queue = Queue("uploads", connection=redis_conn)

storage_path = os.environ.get("UPLOAD_DIR", "storage")
os.makedirs(storage_path, exist_ok=True)
MAX_UPLOAD_SIZE = int(os.environ.get("MAX_UPLOAD_SIZE", 10 * 1024 * 1024))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/contracts", response_model=List[ContractResponse])
def list_contracts(db: Session = Depends(get_db)):
    contracts = db.query(Contrato).all()
    return [
        ContractResponse(
            id=str(contract.id),
            bank=contract.banco,
            balance=contract.saldo,
            cet=contract.taxa_anual,
            dueDate=contract.data_inicio,
        )
        for contract in contracts
    ]

@app.post("/uploads")
async def upload_pdf(contract_id: int, file: UploadFile = File(...)):
    logger.info("Upload started for file '%s'", file.filename)
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    file_id = f"{uuid.uuid4()}.pdf"
    dest = os.path.join(storage_path, file_id)
    content = await file.read(MAX_UPLOAD_SIZE + 1)
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="File too large")
    try:
        with open(dest, "wb") as f:
            f.write(content)
    except OSError as e:
        logger.exception("Failed to save uploaded file '%s'", file.filename)
        raise HTTPException(status_code=500, detail="Failed to save file") from e
    queue.enqueue("tasks.parse_sicoob", dest, contract_id)
    logger.info("Upload finished for file '%s' as '%s'", file.filename, file_id)
    return {"id": file_id, "filename": file.filename}


@app.get("/accruals/export")
def export_accruals(start_date: str, end_date: str, db: Session = Depends(get_db)):
    """Export pro-rata interest accruals for contracts within a period.

    The interest is calculated using the formula:
    interest = principal * annual_rate * days / 365
    """

    try:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    if start > end:
        raise HTTPException(status_code=400, detail="start_date must be before end_date")

    def iter_rows():
        header_buffer = StringIO()
        writer = csv.writer(header_buffer)
        writer.writerow(["contract_id", "principal", "annual_rate", "days", "interest"])
        yield header_buffer.getvalue()

        contracts = db.query(Contrato).all()
        for contract in contracts:
            contract_start = contract.data_inicio
            period_start = max(start, contract_start)
            if period_start > end:
                continue
            days = (end - period_start).days + 1
            interest = contract.saldo * contract.taxa_anual * days / 365

            row_buffer = StringIO()
            writer = csv.writer(row_buffer)
            writer.writerow(
                [
                    contract.id,
                    f"{contract.saldo:.2f}",
                    contract.taxa_anual,
                    days,
                    f"{interest:.2f}",
                ]
            )
            yield row_buffer.getvalue()

    headers = {"Content-Disposition": "attachment; filename=accruals.csv"}
    return StreamingResponse(iter_rows(), media_type="text/csv", headers=headers)


@app.get("/transactions/export")
def export_transactions(
    empresa_id: int,
    start_date: str,
    end_date: str,
    db: Session = Depends(get_db),
):
    """Export bank statement movements as accounting entries in SCI TXT layout."""

    try:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    if start > end:
        raise HTTPException(status_code=400, detail="start_date must be before end_date")


    def iter_lines() -> Iterable[str]:
        q = (
            db.query(Movimentacao)
            .join(Extrato)
            .join(Contrato)
            .filter(
                Contrato.empresa_id == empresa_id,
                Movimentacao.data_lanc >= start,
                Movimentacao.data_lanc <= end,
            )
            .order_by(Movimentacao.data_lanc)
        )

        for mov in q.all():
            debito, credito = classify(mov.descricao or "")
            valor = mov.valor_debito or mov.valor_credito or 0
            data = (mov.data_lanc or mov.data_ref or start).strftime("%d/%m/%Y")
            historico = mov.descricao or ""
            line = f"{data};{debito};{credito};{valor:.2f};{historico}\n"
            yield line

    headers = {"Content-Disposition": "attachment; filename=transactions.txt"}
    return StreamingResponse(iter_lines(), media_type="text/plain", headers=headers)
