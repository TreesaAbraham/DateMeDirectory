# scripts/report_fulltext_changes.py
import argparse
import csv
import json
import re
from pathlib import Path

def wc(text: str) -> int:
    if not text:
        return 0
    return len(re.findall(r"\b\w+\b", text))

def fulltext(p: dict) -> str:
    d = p.get("profileDetails") or {}
    return (d.get("fullText") or "").strip()

def main() -> None:
    ap = argparse.ArgumentParser(description="Report which profiles improved fullText between two JSON files.")
    ap.add_argument("before_json", type=Path)
    ap.add_argument("after_json", type=Path)
    ap.add_argument("--out", type=Path, default=Path("data/archive/rescrape_changes.csv"))
    ap.add_argument("--min-gain", type=int, default=1, help="Only report if new_wc >= old_wc + min_gain")
    args = ap.parse_args()

    before = json.loads(args.before_json.read_text(encoding="utf-8"))
    after = json.loads(args.after_json.read_text(encoding="utf-8"))
    if not isinstance(before, list) or not isinstance(after, list):
        raise SystemExit("Both JSON files must be lists of profiles")

    before_by_id = {p.get("id"): p for p in before if p.get("id")}
    after_by_id = {p.get("id"): p for p in after if p.get("id")}

    rows = []
    for pid, a in after_by_id.items():
        b = before_by_id.get(pid)
        if not b:
            continue

        old = fulltext(b)
        new = fulltext(a)
        old_wc = wc(old)
        new_wc = wc(new)

        expanded_before = b.get("expandedUrl")
        expanded_after = a.get("expandedUrl")

        improved = new_wc >= old_wc + args.min_gain
        expanded_changed = (expanded_before or "") != (expanded_after or "")

        if improved or expanded_changed:
            rows.append({
                "id": pid,
                "name": a.get("name", ""),
                "docPlatform": a.get("docPlatform", ""),
                "profileUrl": a.get("profileUrl", ""),
                "expandedUrl": expanded_after or "",
                "old_wc": old_wc,
                "new_wc": new_wc,
                "delta_wc": new_wc - old_wc,
                "expanded_changed": expanded_changed,
            })

    rows.sort(key=lambda r: (r["delta_wc"], r["new_wc"]), reverse=True)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else [
            "id","name","docPlatform","profileUrl","expandedUrl","old_wc","new_wc","delta_wc","expanded_changed"
        ])
        w.writeheader()
        for r in rows:
            w.writerow(r)

    print(f"[done] wrote {len(rows)} changed profiles -> {args.out}")
    if rows:
        print("[top 10 improvements]")
        for r in rows[:10]:
            print(f"- {r['id']} | +{r['delta_wc']} words | {r['docPlatform']} | {r['profileUrl']}")

if __name__ == "__main__":
    main()
