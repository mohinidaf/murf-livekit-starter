"""
Day 6 demo — Make one outbound call using Twilio Voice API.

Usage:
    python src/twilio_demo_call.py +919876543210

Requires in .env.local:
    TWILIO_ACCOUNT_SID
    TWILIO_AUTH_TOKEN
    TWILIO_PHONE_NUMBER  (your Twilio caller ID)
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from twilio.rest import Client

_backend_dir = Path(__file__).resolve().parent.parent
load_dotenv(_backend_dir / ".env.local")


def make_call(to_number: str) -> None:
    account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
    from_number = os.getenv("TWILIO_PHONE_NUMBER", "")

    if not all([account_sid, auth_token, from_number]):
        print("ERROR: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER")
        print("must all be set in backend/.env.local")
        sys.exit(1)

    client = Client(account_sid, auth_token)

    twiml = """
    <Response>
        <Say voice="Polly.Matthew">
            Hello, this is FinAssist, an AI-powered financial assistant
            calling on behalf of our team.
        </Say>
        <Pause length="1"/>
        <Say voice="Polly.Matthew">
            I am calling to share a quick reminder about government
            financial schemes you may be eligible for, such as
            PM Kisan, which provides income support to farmer families,
            or the Mudra Loan, which offers up to ten lakh rupees
            for small businesses.
        </Say>
        <Pause length="1"/>
        <Say voice="Polly.Matthew">
            Please note, this is an automated AI call.
            You can hang up at any time.
            Thank you for your time. Goodbye.
        </Say>
    </Response>
    """

    print(f"Calling {to_number} from {from_number}...")

    call = client.calls.create(
        to=to_number,
        from_=from_number,
        twiml=twiml,
    )

    print(f"Call placed. SID: {call.sid}")
    print("Your phone should ring shortly.")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python src/twilio_demo_call.py <phone_number>")
        print("Example: python src/twilio_demo_call.py +919876543210")
        sys.exit(1)

    make_call(sys.argv[1])


if __name__ == "__main__":
    main()
