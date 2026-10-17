"""Checks that your machine is ready to run MöbiusPilot.

Run (CMD):  .venv\\Scripts\\python scripts\\check_setup.py
Each check prints OK / FAIL / SKIP so you know exactly what to fix.
"""
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

# Load .env from the repo root (one folder above this script)
ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

results = []  # list of (status, name, detail)


def report(status, name, detail=""):
    results.append(status)
    print(f"[{status:4}] {name}" + (f" - {detail}" if detail else ""))


def is_placeholder(value):
    # Values copied from .env.example still contain "your-" placeholders
    return not value or value.startswith("your-")


# 1. Python version
ok = sys.version_info >= (3, 10)
report("OK" if ok else "FAIL", "Python version", sys.version.split()[0])

# 2. .env file exists
report("OK" if (ROOT / ".env").exists() else "FAIL", ".env file",
       "" if (ROOT / ".env").exists() else "copy .env.example to .env")

# 3. LLM env vars + one tiny real call
base = os.getenv("LLM_BASE_URL", "")
key = os.getenv("LLM_API_KEY", "")
model = os.getenv("LLM_MODEL", "")
if is_placeholder(key) or not base or not model:
    report("FAIL", "LLM settings", "set LLM_BASE_URL, LLM_API_KEY, LLM_MODEL in .env")
else:
    try:
        r = httpx.post(
            f"{base.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {key}"},
            json={"model": model, "max_tokens": 5,
                  "messages": [{"role": "user", "content": "Reply with: ok"}]},
            timeout=20,
        )
        if r.status_code == 200:
            reply = r.json()["choices"][0]["message"]["content"]
            report("OK", "LLM reachable", f"{model} replied: {reply!r}")
        else:
            report("FAIL", "LLM reachable", f"HTTP {r.status_code}: {r.text[:150]}")
    except Exception as e:  # network errors, timeouts, bad JSON
        report("FAIL", "LLM reachable", repr(e)[:150])

# 4. Messaging platform credentials (presence only; the real test is Phase 1)
platform = os.getenv("MESSAGING_PLATFORM", "")
if platform == "google_chat":
    cred = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    cred_ok = bool(cred) and (ROOT / cred).exists() or Path(cred).exists()
    report("OK" if cred_ok else "FAIL", "Google service-account JSON", cred or "not set")
    for var in ("GOOGLE_PROJECT_ID", "GOOGLE_PUBSUB_SUBSCRIPTION_ID"):
        report("FAIL" if is_placeholder(os.getenv(var, "")) else "OK", var)
elif platform == "telegram":
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not token:
        report("FAIL", "TELEGRAM_BOT_TOKEN", "not set")
    else:
        try:
            r = httpx.get(f"https://api.telegram.org/bot{token}/getMe", timeout=15)
            ok = r.status_code == 200 and r.json().get("ok")
            report("OK" if ok else "FAIL", "Telegram bot token",
                   r.json().get("result", {}).get("username", r.text[:100]))
        except Exception as e:
            report("FAIL", "Telegram bot token", repr(e)[:150])
elif platform == "simulator":
    report("SKIP", "Messaging", "SIMULATED platform - not real messaging")
else:
    report("FAIL", "MESSAGING_PLATFORM", "set to google_chat, telegram or simulator")

print()
print("All good!" if "FAIL" not in results else "Fix the FAIL lines above, then re-run.")
sys.exit(1 if "FAIL" in results else 0)
