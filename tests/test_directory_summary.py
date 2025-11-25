import json
from pathlib import Path


def test_directory_summary():
    """
    Validate that the latest directory scrape looks sane and
    print a human-readable summary of the profile count.

    This test assumes you have already run the directory scraper, e.g.:
        python -m src.rets.scrape_directory
    """
    latest_path = Path("data/directory/latest.json")

    assert latest_path.exists(), (
        "latest directory snapshot not found. "
        "Run `python -m src.rets.scrape_directory` before running this test."
    )

    data = json.loads(latest_path.read_text(encoding="utf-8"))

    # Basic shape checks
    assert isinstance(data, list), "latest.json should contain a list of profiles"
    assert len(data) > 0, "No profiles found in data/directory/latest.json"

    # Minimal field sanity checks
    for profile in data:
        assert "id" in profile, "Profile missing 'id'"
        assert "name" in profile, "Profile missing 'name'"
        assert "profileUrl" in profile, "Profile missing 'profileUrl'"

    # Human-readable summary (shown when pytest is run without output capture)
    print(f"[summary] latest scrape contains {len(data)} profiles")
