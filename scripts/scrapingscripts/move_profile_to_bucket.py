# scripts/move_profile_to_bucket.py
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

def load_list(path: Path) -> list:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise SystemExit(f"[error] {path} is not a JSON list")
    return data

def write_list(path: Path, data: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def main() -> None:
    ap = argparse.ArgumentParser(
        description="Move a profile (by id) from a source JSON list into a bucket JSON list."
    )
    ap.add_argument("--id", required=True, help="Profile id (e.g., usr_abcdef1234)")
    ap.add_argument("--source", required=True, type=Path, help="Source JSON list file")
    ap.add_argument("--bucket", required=True, type=Path, help="Bucket JSON list file (appended to)")
    ap.add_argument("--reason", required=True, help="Why you're moving it (e.g. deleted / not looking)")
    ap.add_argument("--in-place", action="store_true", help="Overwrite source file (default)")
    ap.add_argument("--out", type=Path, help="Write remaining profiles to this file instead of overwriting source")
    ap.add_argument("--dry-run", action="store_true", help="Show what would happen without writing files")
    args = ap.parse_args()

    source = load_list(args.source)
    bucket = load_list(args.bucket)

    pid = args.id.strip()

    # find in source
    match = None
    remaining = []
    for p in source:
        if p.get("id") == pid and match is None:
            match = p
        else:
            remaining.append(p)

    if match is None:
        print(f"[error] id not found in source: {pid}")
        sys.exit(1)

    # avoid duplicates in bucket
    if any(p.get("id") == pid for p in bucket):
        print(f"[warn] id already exists in bucket; removing from source anyway: {pid}")
    else:
        match = dict(match)  # copy
        match["reviewStatus"] = "closed"
        match["reviewReason"] = args.reason.strip()
        match["reviewTimestamp"] = datetime.now(timezone.utc).isoformat()
        bucket.append(match)

    # decide where "remaining" goes
    out_path = args.out if args.out else args.source

    print(f"[info] source: {args.source}  ({len(source)} -> {len(remaining)})")
    print(f"[info] bucket: {args.bucket}  (will be {len(bucket)})")
    print(f"[info] moved: {pid}  reason='{args.reason}'")

    if args.dry_run:
        print("[dry-run] no files written")
        return

    write_list(args.bucket, bucket)
    write_list(out_path, remaining)
    print(f"[done] wrote bucket -> {args.bucket}")
    print(f"[done] wrote remaining -> {out_path}")

if __name__ == "__main__":
    main()
