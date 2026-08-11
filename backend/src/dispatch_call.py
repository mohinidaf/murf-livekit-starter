"""
Day 6 — Trigger an outbound call from the FinAssist agent.

Usage with a phone number:
    python src/dispatch_call.py +919876543210

Usage with a SIP address (Linphone SIP-to-SIP demo):
    python src/dispatch_call.py sip:user@sip.linphone.org

This creates a new room, dispatches the my-agent to it, and passes
the destination in metadata so the agent places the SIP call.

Requires:
    - LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET in .env.local
    - The agent running (uv run python src/agent.py dev)
"""

import asyncio
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from livekit.api import LiveKitAPI
from livekit.protocol.agent_dispatch import CreateAgentDispatchRequest

_backend_dir = Path(__file__).resolve().parent.parent
load_dotenv(_backend_dir / ".env.local")


async def dispatch_outbound_call(phone_number: str) -> None:
    """Dispatch the agent to a new room and pass the phone number."""

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
    safe_id = (
        phone_number.replace("+", "")
        .replace("@", "-")
        .replace(":", "-")
        .replace(".", "-")
    )
    room_name = f"outbound-call-{safe_id}"

    metadata = json.dumps(
        {
            "outbound": True,
            "phone_number": phone_number,
        }
    )

    print(f"Dispatching agent '{agent_name}' to room '{room_name}'")
    print(f"Phone number: {phone_number}")

    try:
        dispatch = await lkapi.agent_dispatch.create_dispatch(
            CreateAgentDispatchRequest(
                agent_name=agent_name,
                room=room_name,
                metadata=metadata,
            )
        )
        print(f"Dispatch created: {dispatch}")
        print(
            "\nThe agent should now be placing the call. "
            "Check the agent terminal for logs."
        )
    except Exception as e:
        print(f"ERROR: Failed to create dispatch: {e}")
        sys.exit(1)
    finally:
        await lkapi.aclose()


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python src/dispatch_call.py <destination>")
        print("Phone:  python src/dispatch_call.py +919876543210")
        print("SIP:    python src/dispatch_call.py sip:user@sip.linphone.org")
        sys.exit(1)

    destination = sys.argv[1]

    if not destination.startswith("+") and not destination.startswith("sip:"):
        print(
            "WARNING: Destination should be E.164 (+919876543210) "
            "or SIP address (sip:user@host)."
        )

    asyncio.run(dispatch_outbound_call(destination))


if __name__ == "__main__":
    main()
