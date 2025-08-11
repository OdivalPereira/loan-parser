import os
import uuid
import csv
import logging
from datetime import datetime, date, timedelta
from io import StringIO
from typing import List, Iterable

from fastapi import Depends, FastAPI, UploadFile, File, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from rq import Queue
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from passlib.context import CryptContext

from backend.config import get_redis
from .db import SessionLocal
from .models import Contrato, Movimentacao, Extrato
from .rules import classify


class ContractBase(BaseModel):
    empresa_id: int
    numero: str
    bank: str
    balance: float
    cet: float
    dueDate: date


class ContractResponse(BaseModel):
    id: str
    bank: str
    balance: float
    cet: float
    dueDate: date

    class Config:
        orm_mode = True


class ContractCreate(ContractBase):
    pass


class ContractUpdate(BaseModel):
    empresa_id: int | None = None
    numero: str | None = None
    bank: str | None = None
    balance: float | None = None
    cet: float | None = None
    dueDate: date | None = None


class ExtratoResponse(BaseModel):
    id: int
    status: str
    meta: dict | None = None

    class Config:
        orm_mode = True


app = FastAPI()
logger = logging.getLogger(__name__)

redis_conn = get_redis()
queue = Queue("uploads", connection=redis_conn)

storage_path = os.environ.get("UPLOAD_DIR", "storage")
os.makedirs(storage_path, exist_ok=True)
MAX_UPLOAD_SIZE = int(os.environ.get("MAX_UPLOAD_SIZE", 10 * 1024 * 1024))

SECRET_KEY = os.environ.get("SECRET_KEY", "secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

fake_user = {"username": "admin", "hashed_password": pwd_context.hash("admin")}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def authenticate_user(username: str, password: str):
    if username != fake_user["username"]:
        return False
    if not verify_password(password, fake_user["hashed_password"]):
        return False
    return fake_user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        if username != fake_user["username"]:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return {"username": username}


@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}


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


@app.post("/contracts", response_model=ContractResponse, status_code=201)
def create_contract(contract: ContractCreate, db: Session = Depends(get_db)):
    model = Contrato(
        empresa_id=contract.empresa_id,
        numero=contract.numero,
        banco=contract.bank,
        saldo=contract.balance,
        taxa_anual=contract.cet,
        data_inicio=contract.dueDate,
    )
    db.add(model)
    db.commit()
    db.refresh(model)
    return ContractResponse(
        id=str(model.id),
        bank=model.banco,
        balance=model.saldo,
        cet=model.taxa_anual,
        dueDate=model.data_inicio,
    )


@app.put("/contracts/{contract_id}", response_model=ContractResponse)
def update_contract(
    contract_id: int, data: ContractUpdate, db: Session = Depends(get_db)
):
    contract = db.get(Contrato, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    if data.empresa_id is not None:
        contract.empresa_id = data.empresa_id
    if data.numero is not None:
        contract.numero = data.numero
    if data.bank is not None:
        contract.banco = data.bank
    if data.balance is not None:
        contract.saldo = data.balance
    if data.cet is not None:
        contract.taxa_anual = data.cet
    if data.dueDate is not None:
        contract.data_inicio = data.dueDate
    db.commit()
    db.refresh(contract)
    return ContractResponse(
        id=str(contract.id),
        bank=contract.banco,
        balance=contract.saldo,
        cet=contract.taxa_anual,
        dueDate=contract.data_inicio,
    )


@app.delete("/contracts/{contract_id}")
def delete_contract(contract_id: int, db: Session = Depends(get_db)):
    contract = db.get(Contrato, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    db.delete(contract)
    db.commit()
    return {"ok": True}


@app.get(
    "/contracts/{contract_id}/extratos", response_model=List[ExtratoResponse]
)
def list_extratos(contract_id: int, db: Session = Depends(get_db)):
    extratos = (
        db.query(Extrato)
        .filter(Extrato.contrato_id == contract_id)
        .all()
    )
    return extratos

@app.post("/uploads")
async def upload_pdf(
    contract_id: int,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
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
def export_accruals(
    start_date: str,
    end_date: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
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

        contracts = (
            db.query(Contrato)
            .filter(Contrato.data_inicio <= end)
            .yield_per(100)
        )
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
    current_user: dict = Depends(get_current_user),
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
