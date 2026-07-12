from pathlib import Path

FORBIDDEN_ROOT_FILES = {
    "engine.py",
    "history.py",
    "http.py",
    "models.py",
    "report.py",
    "scoring.py",
    "telegram.py",
    "providers.py",
    "official_providers.py",
    "capital_flow_engine.py",
    "provider_health.py",
}

root = Path(__file__).resolve().parent
found = sorted(name for name in FORBIDDEN_ROOT_FILES if (root / name).exists())
if found:
    raise SystemExit(
        "Legacy root modules detected; remove them before deployment: " + ", ".join(found)
    )

required = [
    root / "main.py",
    root / "pios" / "core" / "engine.py",
    root / "pios" / "core" / "http.py",
    root / "pios" / "providers" / "registry.py",
    root / ".github" / "workflows" / "pios-capital-flow-engine.yml",
]
missing = [str(path.relative_to(root)) for path in required if not path.exists()]
if missing:
    raise SystemExit("Required files missing: " + ", ".join(missing))

print("Repository sanity check passed: clean modular layout detected.")
