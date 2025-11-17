from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple
import numpy as np
import pandas as pd

def read_csv_np(path: str | Path, delimiter: str = ",") -> np.ndarray:
    df = pd.read_csv(path, delimiter=delimiter)
    return df.to_numpy()

def save_npy(path: str | Path, arr: np.ndarray) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    np.save(str(path), arr)

def save_json(path: str | Path, obj: Dict[str, Any]) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, sort_keys=True)

def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p
