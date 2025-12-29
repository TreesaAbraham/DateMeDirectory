import json
import sys
from pathlib import Path


def load_json(path: Path):
    if not path.exists():
        print(f"[error] File not found: {path}")
        sys.exit(1)
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    # Usage: python scripts/filter_unusable_profiles.py data/processed/20251125
    if len(sys.argv) != 2:
        print(
            "Usage:\n"
            "  python scripts/filter_unusable_profiles.py data/processed/20251125"
        )
        sys.exit(1)

    base_dir = Path(sys.argv[1])
    profiles_path = base_dir / "profiles.json"
    skipped_path = base_dir / "profiles_skipped.json"
    output_path = base_dir / "profiles_accessible.json"

    print(f"[info] base dir: {base_dir}")

    profiles = load_json(profiles_path)

    # If there is no skipped file, just copy profiles.json to profiles_accessible.json
    if not skipped_path.exists():
        print("[warn] profiles_skipped.json not found; copying all profiles as accessible")
        output_path.write_text(
            json.dumps(profiles, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"[done] wrote {len(profiles)} profiles to {output_path}")
        sys.exit(0)

    skipped = load_json(skipped_path)

    # Build sets of IDs and URLs to remove
    ids_to_drop = set()
    urls_to_drop = set()

    for entry in skipped:
        pid = entry.get("id")
        url = entry.get("url")
        if pid:
            ids_to_drop.add(pid)
        if url:
            urls_to_drop.add(url)

    print(f"[info] {len(ids_to_drop)} IDs marked as unusable")
    print(f"[info] {len(urls_to_drop)} URLs marked as unusable")

    # Filter profiles: keep only those NOT in skipped
    filtered = []
    dropped = 0

    for p in profiles:
        pid = p.get("id")
        url = p.get("profileUrl")

        if pid in ids_to_drop or url in urls_to_drop:
            dropped += 1
            continue

        filtered.append(p)

    print(f"[info] total profiles in profiles.json: {len(profiles)}")
    print(f"[info] dropped (unusable): {dropped}")
    print(f"[info] kept (accessible): {len(filtered)}")

    # Write out filtered list
    output_path.write_text(
        json.dumps(filtered, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[done] wrote filtered profiles to: {output_path}")


if __name__ == "__main__":
    main()
