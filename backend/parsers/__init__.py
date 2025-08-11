from importlib import import_module
import pkgutil
from typing import Callable, Dict, Iterable, BinaryIO, Union, Protocol


class ParserNotFoundError(ValueError):
    """Raised when a requested parser is not registered."""


ParserInput = Union[bytes, BinaryIO, Iterable[bytes]]


class Parser(Protocol):
    def __call__(self, pdf_stream: ParserInput) -> dict:  # pragma: no cover - interface
        """Parse raw PDF data into structured information."""


_parsers: Dict[str, Parser] = {}


def register(name: str):
    def decorator(func: Parser):
        _parsers[name] = func
        return func

    return decorator


def get(name: str) -> Parser:
    try:
        return _parsers[name]
    except KeyError as exc:  # pragma: no cover - defensive
        raise ParserNotFoundError(f"Parser '{name}' not found") from exc


def parse(name: str, pdf_stream: ParserInput) -> dict:
    parser = get(name)
    return parser(pdf_stream)


def _load_plugins() -> None:
    for _, module_name, _ in pkgutil.iter_modules(__path__):
        import_module(f"{__name__}.{module_name}")


_load_plugins()
