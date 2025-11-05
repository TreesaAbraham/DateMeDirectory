from __future__ import annotations
import json, shutil
from pathlib import Path

def ensure_snapshot_paths(stamp: str) -> dict:
    raw_dir = Path("data/raw") / stamp
    processed_dir = Path("data/processed") / stamp
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    latest = Path("data/latest")
    if latest.exists():
        if latest.is_symlink():
            latest.unlink()
        else:
            shutil.rmtree(latest)
    shutil.copytree(processed_dir, latest)
    return {"raw_dir": raw_dir, "processed_dir": processed_dir}

def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")

def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))
