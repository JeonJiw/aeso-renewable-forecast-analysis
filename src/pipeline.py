"""
Pre-step runner.
Read [[pre_steps]] definitions from dataset.toml and run only if outputs are missing or stale.
"""
from pathlib import Path
import importlib

def _is_stale(inputs, outputs):
    ins = [Path(p) for p in inputs]
    outs = [Path(p) for p in outputs]
    if not outs:
        return True
    for o in outs:
        if not o.exists():
            return True
        for i in ins:
            if not i.exists() or o.stat().st_mtime < i.stat().st_mtime:
                return True
    return False

def run_pre_steps(pre_steps_cfg):
    for step in pre_steps_cfg:
        module = step["module"]
        func = step["func"]
        inputs = step.get("inputs", [])
        outputs = step.get("outputs", [])
        if _is_stale(inputs, outputs):
            mod = importlib.import_module(module)
            getattr(mod, func)(inputs=inputs, outputs=outputs)