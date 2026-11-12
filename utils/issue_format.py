"""
CircuitMind - Issue rendering helpers
utils/issue_format.py

Turns diagnose findings into uniform rows for the UI. The diagnose module
returns structured issues, while older callers and saved results still carry
plain 'Error: ...' strings; both shapes must render.
"""

_SUPPORTED_SEVERITIES = {"error", "warning", "info"}

_LEGACY_PREFIXES = (
    ("Error:", "error"),
    ("Warning:", "warning"),
    ("Info:", "info"),
)


def _legacy_row(text: str) -> dict:
    severity, message = "info", text.strip()
    for prefix, mapped in _LEGACY_PREFIXES:
        if text.startswith(prefix):
            severity, message = mapped, text[len(prefix):].strip()
            break
    return {"severity": severity, "code": None, "text": message or "Unspecified issue."}


def issue_rows(issues) -> list[dict]:
    """Normalise structured and legacy issues into {'severity','code','text'} rows."""
    rows = []
    for issue in issues or []:
        if isinstance(issue, str):
            rows.append(_legacy_row(issue))
            continue
        if not isinstance(issue, dict):
            continue

        severity = str(issue.get("severity") or "info").lower()
        if severity not in _SUPPORTED_SEVERITIES:
            severity = "info"

        message = str(issue.get("message") or "").strip()
        suggestion = str(issue.get("suggestion") or "").strip()
        text = f"{message} {suggestion}".strip() or "Unspecified issue."

        rows.append({"severity": severity, "code": issue.get("code"), "text": text})
    return rows
