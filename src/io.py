"""
Data loading pipeline:
- Read config/dataset.toml and run pre_steps
- Read files from datasets section through adapters and validate schema
- Merge and return canonical dataframe
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib

from .pipeline import run_pre_steps
from .adapters import get_loader
from .schema import to_canonical, validate

def load_from_config(cfg_path: str | Path = "config/dataset.toml") -> pd.DataFrame:
    cfg_path = Path(cfg_path)
    with cfg_path.open("rb") as f:
        cfg = tomllib.load(f)

    # 1️⃣ pre_steps
    pre = cfg.get("pre_steps", [])
    if pre:
        run_pre_steps(pre)

    # 2️⃣ datasets
    entries = cfg.get("datasets", [])
    if not entries:
        raise ValueError("config file does not define datasets")

    dfs = []
    for e in entries:
        adapter_name = e["adapter"]
        path = e["path"]
        loader = get_loader(adapter_name)
        kwargs = {k: v for k, v in e.items() if k not in {"adapter", "path"}}
        df = loader(path, **kwargs)

        check = validate(df)
        if not check.ok:
            raise ValueError(f"{path} is missing columns: {check.missing}")
        dfs.append(to_canonical(df))

    merged = pd.concat(dfs, ignore_index=True).sort_values("timestamp")
    return merged