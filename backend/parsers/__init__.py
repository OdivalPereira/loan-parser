from importlib import import_module
import pkgutil
from typing import Callable, Dict


class ParserNotFoundError(ValueError):
    """Raised when a requested parser is not registered."""


_parsers: Dict[str, Callable[[bytes], dict]] = {}


def register(name: str):
    def decorator(func: Callable[[bytes], dict]):
        _parsers[name] = func
        return func

    return decorator


def get(name: str) -> Callable[[bytes], dict]:
    try:
        return _parsers[name]
    except KeyError as exc:  # pragma: no cover - defensive
        raise ParserNotFoundError(f"Parser '{name}' not found") from exc


def parse(name: str, pdf_bytes: bytes) -> dict:
    parser = get(name)
    return parser(pdf_bytes)


def _load_plugins() -> None:
    for _, module_name, _ in pkgutil.iter_modules(__path__):
        import_module(f"{__name__}.{module_name}")


_load_plugins()
