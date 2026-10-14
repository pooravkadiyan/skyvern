"""Open a Skyvern browser session and let Browser Use finish the task on it.

Skyvern owns the Chrome and the live view in the GUI. This process only
connects over CDP and calls an Ignarix Bedrock model. The run does not pause
for a person.

Example:
    python -m ignarix.run_browser_use --url https://example.com --task "Sign up with the email on this row"
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse, urlunparse

import boto3

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL = "us.anthropic.claude-sonnet-4-6"
DEFAULT_PROFILE = "ignarix-credits"
DEFAULT_REGION = "us-east-1"


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def _cdp_url(browser_address: str) -> str:
    parsed = urlparse(browser_address)
    if parsed.fragment.startswith("pbs_"):
        return urlunparse(parsed._replace(fragment=""))
    return browser_address


def _request(method: str, url: str, api_key: str, body: dict | None = None) -> dict:
    data = None if body is None else json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "x-api-key": api_key,
            "content-type": "application/json",
            "accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise SystemExit(f"{method} {url} failed ({error.code}): {detail}") from error
    return json.loads(payload) if payload else {}


def open_skyvern_browser(base_url: str, api_key: str, url: str, timeout_minutes: int) -> tuple[str, str]:
    created = _request(
        "POST",
        f"{base_url}/v1/browser_sessions",
        api_key,
        {"url": url, "timeout": timeout_minutes},
    )
    session_id = created["browser_session_id"]
    deadline = time.time() + 120
    while time.time() < deadline:
        session = _request("GET", f"{base_url}/v1/browser_sessions/{session_id}", api_key)
        address = session.get("browser_address")
        status = session.get("status")
        if address and status == "running":
            return session_id, _cdp_url(address)
        if status in {"failed", "completed", "timeout"}:
            raise SystemExit(f"Skyvern browser session {session_id} ended before it was ready ({status})")
        time.sleep(1)
    raise SystemExit(f"Skyvern browser session {session_id} did not expose CDP within 120s")


async def run_agent(task: str, cdp_url: str, model_id: str, region: str, profile: str, max_steps: int) -> None:
    from browser_use import Agent, Browser
    from browser_use.llm import ChatAWSBedrock

    session = boto3.Session(profile_name=profile, region_name=region)
    llm = ChatAWSBedrock(
        model=model_id,
        aws_region=region,
        session=session,
        temperature=1,
    )
    browser = Browser(cdp_url=cdp_url, is_local=False, keep_alive=True, captcha_solver=False)
    agent = Agent(task=task, llm=llm, browser=browser)
    await agent.run(max_steps=max_steps)


def main() -> None:
    _load_dotenv(REPO_ROOT / ".env")
    parser = argparse.ArgumentParser(description="Run Browser Use on a Skyvern browser with an Ignarix Bedrock model")
    parser.add_argument("--url", required=True, help="Page the browser opens first")
    parser.add_argument("--task", required=True, help="What the agent should finish")
    parser.add_argument("--model", default=os.environ.get("IGNARIX_BEDROCK_MODEL_ID", DEFAULT_MODEL))
    parser.add_argument("--profile", default=os.environ.get("AWS_PROFILE", DEFAULT_PROFILE))
    parser.add_argument("--region", default=os.environ.get("AWS_REGION", DEFAULT_REGION))
    parser.add_argument("--skyvern-url", default=os.environ.get("SKYVERN_BASE_URL", "http://localhost:8000"))
    parser.add_argument("--timeout-minutes", type=int, default=60)
    parser.add_argument("--max-steps", type=int, default=50)
    args = parser.parse_args()

    api_key = os.environ.get("SKYVERN_API_KEY", "").strip()
    if not api_key:
        raise SystemExit("SKYVERN_API_KEY is missing. Start Skyvern once so it writes the local key into skyvern/.env")

    session_id, cdp_url = open_skyvern_browser(
        args.skyvern_url.rstrip("/"),
        api_key,
        args.url,
        args.timeout_minutes,
    )
    print(f"session={session_id}")
    print(f"model={args.model}")
    print(f"gui=http://localhost:8080")
    asyncio.run(run_agent(args.task, cdp_url, args.model, args.region, args.profile, args.max_steps))


if __name__ == "__main__":
    main()
