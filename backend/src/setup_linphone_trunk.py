"""
Set up a Linphone SIP outbound trunk in LiveKit.

Run once:
    python src/setup_linphone_trunk.py <sip_username> <sip_password>

Creates a trunk that routes SIP calls through sip.linphone.org.
"""

import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv
from livekit.api import LiveKitAPI
from livekit.protocol.sip import (
    CreateSIPOutboundTrunkRequest,
    SIPOutboundTrunkInfo,
)

_backend_dir = Path(__file__).resolve().parent.parent
load_dotenv(_backend_dir / ".env.local")

SIP_PROXY = "sip.linphone.org"


async def create_trunk(username: str, password: str) -> str:
    lkapi = LiveKitAPI()

    trunk = SIPOutboundTrunkInfo(
        name="Linphone SIP-to-SIP",
        address=SIP_PROXY,
        numbers=[f"sip:{username}@{SIP_PROXY}"],
        auth_username=username,
        auth_password=password,
    )

    result = await lkapi.sip.create_sip_outbound_trunk(
        CreateSIPOutboundTrunkRequest(trunk=trunk)
    )

    await lkapi.aclose()
    return result.sip_trunk_id


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: python src/setup_linphone_trunk.py <sip_username> <sip_password>")
        sys.exit(1)

    username = sys.argv[1]
    password = sys.argv[2]

    trunk_id = asyncio.run(create_trunk(username, password))

    print(f"Trunk created: {trunk_id}")
    print("Add this to backend/.env.local:")
    print(f"SIP_OUTBOUND_TRUNK_ID={trunk_id}")


if __name__ == "__main__":
    main()
