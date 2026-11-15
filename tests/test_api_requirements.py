"""Guards the API-only requirements file used by the Vercel deployment.

`README.md` and `vercel.json` both describe `api/requirements.txt` as the
dependency set for the serverless API, but importing the API without an
extra file must not silently fall back to the full (Streamlit) requirements.
"""

import ast
import re
from pathlib import Path

API_DIR = Path(__file__).resolve().parents[1] / "api"
REQUIREMENTS = API_DIR / "requirements.txt"

# Third-party import names reachable from api/app.py → PyPI distribution name.
IMPORT_TO_DISTRIBUTION = {
    "fastapi": "fastapi",
    "pydantic": "pydantic",
    "slowapi": "slowapi",
    "groq": "groq",
    "schemdraw": "schemdraw",
    "dotenv": "python-dotenv",
    "redis": "redis",
}


def _requirement_names() -> set:
    names = set()
    for line in REQUIREMENTS.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        name = re.split(r"[<>=!~\[; ]", line, maxsplit=1)[0]
        names.add(name.lower())
    return names


def _top_level_imports(path: Path) -> set:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            found.add(node.module.split(".")[0])
    return found


def test_api_requirements_exists():
    assert REQUIREMENTS.is_file(), "api/requirements.txt is missing"


def test_covers_every_third_party_import_of_the_api_entrypoint():
    declared = _requirement_names()
    imported = _top_level_imports(API_DIR / "app.py")

    third_party = imported & set(IMPORT_TO_DISTRIBUTION)
    missing = {
        IMPORT_TO_DISTRIBUTION[name]
        for name in third_party
        if IMPORT_TO_DISTRIBUTION[name].lower() not in declared
    }

    assert not missing, f"api/requirements.txt is missing: {sorted(missing)}"


def test_excludes_ui_only_dependencies():
    declared = _requirement_names()
    for ui_only in ("streamlit", "requests"):
        assert ui_only not in declared
