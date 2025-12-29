#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="data/processed/20251125"

FILES=(
  "$BASE_DIR/profiles_accessible.merged.after_rescraped.json"
  "$BASE_DIR/profiles_accessible.merged.json"
  "$BASE_DIR/profiles_acessible._with_text.json"
)

count_under_100 () {
  local file="$1"
  python - "$file" <<'PY'
import json, re, sys
from pathlib import Path

path = Path(sys.argv[1])
data = json.loads(path.read_text(encoding="utf-8"))

def wc(text: str) -> int:
    return len(re.findall(r"\b\w+\b", (text or "").strip()))

under = 0
total = 0
for p in data:
    total += 1
    details = p.get("profileDetails") or {}
    text = details.get("fullText") or ""
    if wc(text) <= 100:
        under += 1

print(f"{under}\t{total}")
PY
}

suggest () {
  local missing="$1"
  python - "$BASE_DIR" "$(basename "$missing")" <<'PY'
import sys, difflib
from pathlib import Path

base = Path(sys.argv[1])
target = sys.argv[2]
files = sorted([p.name for p in base.iterdir() if p.is_file()])

print(f"  Suggestions in {base}:")
for s in difflib.get_close_matches(target, files, n=8, cutoff=0.25):
    print("   - " + s)
PY
}

echo -e "under_or_equal_100\ttotal\tfile"
for f in "${FILES[@]}"; do
  if [[ ! -f "$f" ]]; then
    echo -e "MISSING\t-\t$f"
    suggest "$f"
    continue
  fi
  read -r under total < <(count_under_100 "$f")
  echo -e "${under}\t${total}\t${f}"
done
