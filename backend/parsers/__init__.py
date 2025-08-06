from importlib import import_module
import pkgutil
from typing import Callable, Dict

_parsers: Dict[str, Callable[[bytes], dict]] = {}


def register(name: str):
    def decorator(func: Callable[[bytes], dict]):
        _parsers[name] = func
        return func

    return decorator


def get(name: str) -> Callable[[bytes], dict]:
    return _parsers[name]


def parse(name: str, pdf_bytes: bytes) -> dict:
    parser = get(name)
    return parser(pdf_bytes)


def _load_plugins() -> None:
    for _, module_name, _ in pkgutil.iter_modules(__path__):
        import_module(f"{__name__}.{module_name}")


_load_plugins()
