"""
MEOK auth_middleware (metered) — drop-in replacement for the bundled auth_middleware.py
=======================================================================================
Adds SERVER-SIDE metering: every call checks the live /verify endpoint (persistent
per-key daily limit via Vercel KV). FAIL-OPEN — if /verify is unreachable or KV
isn't configured, calls are allowed (never breaks the MCP). Keeps the existing
check_access(api_key) -> (allowed, message, tier) signature so packages need no code change.

Free tier: server-enforced 200/day (anon less). Pro/PAYG/CSOAI keys: unlimited.
Get a free key: https://proofof.ai/get-key.html   Upgrade: https://buy.stripe.com/aFa7sNcgAdQS0ZT1Uc8k91t
"""
from __future__ import annotations
import json, os, urllib.request, urllib.error

_VERIFY_URL = os.environ.get("MEOK_VERIFY_URL", "https://proofof.ai/verify")
_PRO = "https://buy.stripe.com/aFa7sNcgAdQS0ZT1Uc8k91t"
_TIMEOUT = float(os.environ.get("MEOK_VERIFY_TIMEOUT", "2.5"))


def _server_check(api_key: str, tool: str = ""):
    """Returns (allowed, tier, remaining) from the server, or None on any failure (fail-open)."""
    try:
        data = json.dumps({"api_key": api_key, "tool": tool}).encode()
        req = urllib.request.Request(_VERIFY_URL, data=data,
                                     headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as r:
            d = json.load(r)
            return bool(d.get("allowed", True)), d.get("tier", "free"), d.get("remaining")
    except Exception:
        return None  # fail-open


def check_access(api_key: str = ""):
    key = (api_key or os.environ.get("MEOK_API_KEY", "")).strip()
    # Pro/PAYG/CSOAI keys: trusted, unlimited (still cheap local check)
    if key.startswith(("CSOAI-", "meok_pro_", "payg_")):
        return True, "OK (pro)", "pro"
    res = _server_check(key)
    if res is None:
        # fail-open: behave like the free tier without hard enforcement
        msg = "OK, Pro at https://proofof.ai/get-key.html" if not key else "OK"
        return True, msg, ("free" if key else "free")
    allowed, tier, remaining = res
    if allowed:
        return True, f"OK ({remaining} left today)" if remaining not in (None, "unlimited") else "OK", tier
    return False, f"Free daily limit reached. Upgrade (unlimited): {_PRO} — or get a free key: https://proofof.ai/get-key.html", tier


# ── Attestation primitive (the moat): HMAC-sign any tool result ──────────────
import hmac as _hmac, hashlib as _hashlib, json as _json


def meok_attest(result) -> str:
    """Return a verifiable HMAC-SHA256 attestation of a tool result. Sign with
    MEOK_ATTEST_KEY (env) — verifiable by anyone with the key at verify.meok.ai.
    Wire into a tool by adding {"attestation": meok_attest(out)} to its return."""
    key = os.environ.get("MEOK_ATTEST_KEY", "meok-public").encode()
    payload = _json.dumps(result, sort_keys=True, default=str).encode()
    return _hmac.new(key, payload, _hashlib.sha256).hexdigest()
