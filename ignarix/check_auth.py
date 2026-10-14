"""Check the local UI key against the API. Prints statuses only."""

import json
import re
import urllib.error
import urllib.request
from pathlib import Path

root = Path(__file__).resolve().parents[1]
cred = (root / ".skyvern" / "credentials.toml").read_text(encoding="utf-8")
match = re.search(r'cred\s*=\s*"([^"]+)"', cred)
if not match:
    raise SystemExit("no cred")
key = match.group(1)


def call(url: str, method: str = "GET", headers: dict | None = None) -> tuple[int, str]:
    request = urllib.request.Request(url, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status, response.read().decode("utf-8", errors="replace")[:300]
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode("utf-8", errors="replace")[:300]


status, body = call(
    "http://localhost:8000/api/v1/workflows",
    headers={"x-api-key": key, "accept": "application/json"},
)
print(f"workflows {status} {body}")

status, body = call(
    "http://localhost:8000/api/v1/internal/auth/status",
    headers={"x-api-key": key, "accept": "application/json"},
)
print(f"diagnostics {status} {body}")

status, body = call("http://localhost:8081/ui-session", method="POST")
print(f"ui-session {status} {body}")
