"""Background tasks for processing bank statements."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

from .db import SessionLocal
from .models import Contrato, Extrato, Movimentacao
from .parsers import ParserNotFoundError, parse
from fastapi import HTTPException

logger = logging.getLogger(__name__)


def _parse_date(value: Optional[str]):
    """Convert a ``dd/mm/YYYY`` string to ``date``.

    Returns ``None`` for falsy values or malformed strings.
    """

    if not value:
        return None
    try:
        return datetime.strptime(value, "%d/%m/%Y").date()
    except ValueError:  # pragma: no cover - defensive
        return None


def parse_sicoob(filepath: str, contract_id: Optional[int] = None) -> Dict[str, Any]:
    """Parse a Sicoob PDF and persist its data to the database.

    On success an ``Extrato`` record is created with status ``importado`` and all
    extracted ``Movimentacao`` rows are associated with it. If parsing fails the
    ``Extrato`` is marked as ``pendente revisão``. Any unexpected database errors
    mark the ``Extrato`` as ``erro``.
    """

    session = SessionLocal()

    try:
        if contract_id is not None:
            contrato = session.get(Contrato, contract_id)
            if contrato is None:
                logger.error("Contrato %s não encontrado", contract_id)
                extrato = Extrato(
                    contrato_id=None,
                    filepath=filepath,
                    status="erro",
                    meta={"error": "Contrato não encontrado", "contract_id": contract_id},
                )
                session.add(extrato)
                session.commit()
                return {"status": "erro", "error": "Contrato não encontrado"}

        try:
            with open(filepath, "rb") as f:
                def _iter_file(file_obj, chunk_size: int = 65536) -> Iterable[bytes]:
                    while chunk := file_obj.read(chunk_size):
                        yield chunk

                data = parse("sicoob", _iter_file(f))
        except ParserNotFoundError as exc:
            logger.error("Parser não encontrado: %s", exc)
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            logger.error("Falha ao interpretar extrato %s: %s", filepath, exc)
            extrato = Extrato(
                contrato_id=contract_id,
                filepath=filepath,
                status="pendente revisão",
                meta={"error": str(exc)},
            )
            session.add(extrato)
            session.commit()
            return {"status": "pendente revisão", "error": str(exc)}

        extrato = Extrato(
            contrato_id=contract_id,
            filepath=filepath,
            status="importado",
            meta={"header": data.get("header")},
        )
        session.add(extrato)
        session.flush()  # obtain extrato.id

        transactions: List[Dict[str, Any]] = data.get("transactions", [])
        for tx in transactions:
            mov = Movimentacao(
                extrato_id=extrato.id,
                data_ref=_parse_date(tx.get("data_ref")),
                data_lanc=_parse_date(tx.get("data_lanc")),
                descricao=tx.get("descricao"),
                valor_debito=tx.get("valor_debito"),
                valor_credito=tx.get("valor_credito"),
                saldo=tx.get("saldo"),
            )
            session.add(mov)

        session.commit()
        logger.info(
            "Extrato %s importado com %d movimentacoes", filepath, len(transactions)
        )
        return data

    except Exception as exc:  # pragma: no cover - defensive
        session.rollback()
        if isinstance(exc, HTTPException):
            raise
        logger.exception("Erro ao salvar extrato %s", filepath)
        extrato = Extrato(
            contrato_id=contract_id,
            filepath=filepath,
            status="erro",
            meta={"error": str(exc)},
        )
        session.add(extrato)
        session.commit()
        return {"status": "erro", "error": str(exc)}
    finally:
        session.close()

