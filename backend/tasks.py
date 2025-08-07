"""Background tasks for processing bank statements."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .db import SessionLocal
from .models import Extrato, Movimentacao
from .parsers import parse

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


def parse_sicoob(filepath: str, contrato_id: Optional[int] = None) -> Dict[str, Any]:
    """Parse a Sicoob PDF and persist its data to the database.

    On success an ``Extrato`` record is created with status ``importado`` and all
    extracted ``Movimentacao`` rows are associated with it. If parsing fails the
    ``Extrato`` is marked as ``pendente revisão``. Any unexpected database errors
    mark the ``Extrato`` as ``erro``.
    """

    pdf_bytes = Path(filepath).read_bytes()
    session = SessionLocal()

    try:
        try:
            data = parse("sicoob", pdf_bytes)
        except Exception as exc:
            logger.error("Falha ao interpretar extrato %s: %s", filepath, exc)
            extrato = Extrato(
                contrato_id=contrato_id,
                filepath=filepath,
                status="pendente revisão",
                metadata={"error": str(exc)},
            )
            session.add(extrato)
            session.commit()
            return {"status": "pendente revisão", "error": str(exc)}

        extrato = Extrato(
            contrato_id=contrato_id,
            filepath=filepath,
            status="importado",
            metadata={"header": data.get("header")},
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
        logger.exception("Erro ao salvar extrato %s", filepath)
        extrato = Extrato(
            contrato_id=contrato_id,
            filepath=filepath,
            status="erro",
            metadata={"error": str(exc)},
        )
        session.add(extrato)
        session.commit()
        return {"status": "erro", "error": str(exc)}
    finally:
        session.close()

