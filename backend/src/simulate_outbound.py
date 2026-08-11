"""
Day 6 — Simulated outbound call demo.

Dispatches the FinAssist agent to a room with outbound metadata,
generates a user token, and opens a standalone HTML page that
connects to the same room via LiveKit JS SDK.

Usage (one command):
    python src/simulate_outbound.py

Prerequisites:
    uv run python src/agent.py dev
"""

import asyncio
import json
import os
import sys
import webbrowser
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv
from livekit.api import LiveKitAPI
from livekit.api.access_token import AccessToken, VideoGrants
from livekit.protocol.agent_dispatch import CreateAgentDispatchRequest

_backend_dir = Path(__file__).resolve().parent.parent
load_dotenv(_backend_dir / ".env.local")

ROOM_PREFIX = "outbound-sim"
HTML_PATH = _backend_dir.parent / "frontend" / "public" / "simulate-outbound.html"


async def run_demo() -> None:
    url = os.getenv("LIVEKIT_URL")
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")

    if not all([url, api_key, api_secret]):
        print(
            "ERROR: LIVEKIT_URL, LIVEKIT_API_KEY, and "
            "LIVEKIT_API_SECRET must be set in .env.local"
        )
        sys.exit(1)

    lkapi = LiveKitAPI(url, api_key, api_secret)
    agent_name = os.getenv("AGENT_NAME", "my-agent")
    room_name = f"{ROOM_PREFIX}-{os.getpid()}"

    # ── 1. Dispatch agent ─────────────────────────────────────
    print()
    print("=" * 52)
    print("  DAY 6 — SIMULATED OUTBOUND CALL DEMO")
    print("=" * 52)
    print()
    print("[1/3] Dispatching agent...")

    metadata = json.dumps({"outbound": True, "phone_number": "simulated-user"})

    try:
        await lkapi.agent_dispatch.create_dispatch(
            CreateAgentDispatchRequest(
                agent_name=agent_name,
                room=room_name,
                metadata=metadata,
            )
        )
        print(f"       Room: {room_name}")
    except Exception as e:
        print(f"ERROR: Dispatch failed: {e}")
        await lkapi.aclose()
        sys.exit(1)

    # ── 2. Generate user token ────────────────────────────────
    print("[2/3] Generating user token...")

    token = (
        AccessToken(api_key, api_secret)
        .with_identity("simulated-user")
        .with_grants(VideoGrants(room_join=True, room=room_name))
        .with_ttl(timedelta(hours=1))
    )
    user_token = token.to_jwt()

    # ── 3. Open browser ───────────────────────────────────────
    print("[3/3] Opening demo page...")

    if not HTML_PATH.exists():
        print(f"ERROR: HTML page not found at {HTML_PATH}")
        await lkapi.aclose()
        sys.exit(1)

    sep = "&" if "?" in HTML_PATH.as_uri() else "?"
    full_url = (
        f"{HTML_PATH.as_uri()}{sep}serverUrl={url}&room={room_name}&token={user_token}"
    )
    webbrowser.open(full_url)

    await lkapi.aclose()

    print()
    print("=" * 52)
    print("  CALL STAGES  (for screen recording)")
    print("=" * 52)
    print()
    print("  1. [Calling...]    Agent connects to the room")
    print("  2. [Ringing...]    Agent prepares the greeting")
    print("  3. [Connected]     Agent speaks via Murf Falcon TTS")
    print("  4. [User responds] Speak into your microphone")
    print("  5. [Call ended]    Click 'End Call' or say goodbye")
    print()
    print("  Browser should open automatically.")
    print("  Click 'Start Call' in the page, then speak.")
    print("=" * 52)
    print()


if __name__ == "__main__":
    asyncio.run(run_demo())
