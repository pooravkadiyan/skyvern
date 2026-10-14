"""Copy the organization token from credentials.toml into .env without printing it."""

from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]
cred = (root / ".skyvern" / "credentials.toml").read_text(encoding="utf-8")
match = re.search(r'cred\s*=\s*"([^"]+)"', cred)
if not match:
    raise SystemExit("credentials.toml has no cred")
key = match.group(1)
env_path = root / ".env"
text = env_path.read_text(encoding="utf-8") if env_path.exists() else ""
lines = [line for line in text.splitlines() if not line.startswith("SKYVERN_API_KEY=")]
lines.append("SKYVERN_API_KEY=" + key)
env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"wrote SKYVERN_API_KEY length={len(key)}")
