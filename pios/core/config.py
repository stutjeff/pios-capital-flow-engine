from __future__ import annotations
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[2]
def load_yaml(name: str):
    with (ROOT/'config'/name).open(encoding='utf-8') as f:return yaml.safe_load(f) or {}
