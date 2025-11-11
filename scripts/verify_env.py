# scripts/verify_env.py
import sys, json
mods = {
    "bs4": None,
    "lxml": None,
    "requests": None,
    "tqdm": None,
    "tenacity": None,
    "dotenv": None,
    "jsonschema": None,
}
results = { "python": sys.version.split()[0], "modules": {} }
for name in mods:
    try:
        m = __import__(name)
        ver = getattr(m, "__version__", "ok")
        results["modules"][name] = ver
    except Exception as e:
        results["modules"][name] = f"ERROR: {e.__class__.__name__}: {e}"
print(json.dumps(results, indent=2))
