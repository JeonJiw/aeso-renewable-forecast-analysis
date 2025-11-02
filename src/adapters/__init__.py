"""
Adapter registry.

Each data source loader is registered.
io.load_from_config() calls the loader by adapter name.
"""
from . import aeso, generic_csv

REGISTRY = {
    "aeso": aeso.load,              # AESO fixed schema
    "generic_csv": generic_csv.load # arbitrary CSV (column/unit/time settings possible)
}

def get_loader(name: str):
    try:
        return REGISTRY[name]
    except KeyError as e:
        raise ValueError(
            f"Unknown adapter: {name}. Available: {list(REGISTRY)}"
        ) from e