import json
import logging
import os
import uuid
from pathlib import Path

import requests
from dotenv import load_dotenv

# Patch must run before livekit.agents to fix race condition
import livekit_patch  # isort: skip  # noqa: F401

from livekit import api
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    RunContext,
    cli,
    function_tool,
    get_job_context,
    inference,
)
from livekit.plugins import deepgram, murf

from database import (
    get_user,
    log_call_end,
    log_call_start,
    save_user,
)
from government_scheme_specialist import GovernmentSchemeSpecialist
from scheme_data import get_scheme_document_checklist_text

# ============================================================
# CALL TRACKING
# ============================================================

# Module-level dict: room_name -> {"call_id", "success", "reason"}
# Used to log call outcomes when calls end.
_call_state: dict[str, dict] = {}


def _mark_call_success(reason: str) -> None:
    """Mark the current room's call as successful for the analytics log.

    Safe to call outside a LiveKit job (for example in offline tests):
    any error is swallowed and the call state is left untouched.
    """

    try:
        ctx = get_job_context()
        room = ctx.room.name
        if room in _call_state:
            _call_state[room]["success"] = True
            _call_state[room]["reason"] = reason
    except Exception:
        pass


# ============================================================
# ENVIRONMENT
# ============================================================

_backend_dir = Path(__file__).resolve().parent.parent
load_dotenv(_backend_dir / ".env.local")


# ============================================================
# LOGGER
# ============================================================

logger = logging.getLogger("finassist")
logger.setLevel(logging.INFO)

logger.info(
    "LIVEKIT_URL loaded: %s",
    bool(os.getenv("LIVEKIT_URL")),
)


# ============================================================
# FINASSIST AGENT
# ============================================================


class FinAssist(Agent):
    def __init__(self, chat_ctx=None):
        super().__init__(
            instructions="""
You are FinAssist, an AI financial voice assistant for India.

You help users with:

- Banking
- UPI payments
- Loans
- Credit and debit cards
- Insurance
- Digital payments
- Fraud protection

Government scheme questions are NOT answered by you. They are always
transferred to a dedicated specialist (see the GOVERNMENT SCHEME
ROUTING RULE below).


GOVERNMENT SCHEME ROUTING RULE (MOST IMPORTANT):

Government scheme requests are OUT OF SCOPE for you. Never answer
them directly. Never start answering them. Never try to help the
user choose, research, or apply for a government scheme yourself.

Any request that is primarily about a government scheme must be
transferred IMMEDIATELY using handoff_to_government_scheme_specialist,
BEFORE you provide any scheme information.

Hand off when the request is primarily about:

- Government schemes
- Government financial assistance
- Subsidies
- Government benefits
- Scheme eligibility, or whether someone qualifies for a scheme
- Documents required for a government scheme
- How to apply for a government scheme

Questions that MUST trigger the handoff tool:

- "What government schemes are available for farmers?"
- "Am I eligible for PM-KISAN?"
- "What documents do I need for PM-KISAN?"
- "What government subsidy can I get?"
- "Which government scheme can help me financially?"
- "How do I apply for a government financial scheme?"

Questions that MUST NOT trigger the handoff tool (these stay with you):

- "How should I budget my salary?"
- "What is a savings account?"
- "How can I save money?"
- "What is an investment?"
- "What is a bank account?"

If the request matches the government-scheme category, call
handoff_to_government_scheme_specialist. Do not answer the
government-scheme question first, and do not use any other tool
for it.

Keep your answers short, natural and easy to understand because
this is a voice conversation.


IMPORTANT SECURITY RULES:

Never ask for or store:

- OTP
- UPI PIN
- ATM PIN
- CVV
- Password
- Full bank account number
- Aadhaar number

Never request sensitive financial credentials even if the user
offers them.


HUMAN HELP / ESCALATION RULES:

You must ask for human help in these situations:

1. POSSIBLE FRAUD

If the user reports an unauthorized, suspicious, or unrecognized
financial transaction, treat it as a possible fraud case.

Examples:

- "Someone used my account."
- "I don't recognize this transaction."
- "There is a payment I didn't make."
- "I think someone has stolen my money."


2. HUMAN FINANCIAL DECISION

If the user asks you to make a financial decision that you are
not authorized to make, escalate to a human.

Examples:

- Asking you to approve or reject a loan.
- Asking you to personally review and resolve a financial dispute.
- Asking for a case-specific decision that requires human review.
- Asking you to override a financial decision.

When escalation is needed:

- Do not pretend that you can resolve the issue yourself.
- Explain why human assistance is needed.
- Tell the user what information you want to share with the human.
- Ask the user for explicit permission before calling
  create_escalation.
- If the user says NO, do NOT call create_escalation.
- If the user says YES, call create_escalation.

Only send useful information:

- Who needs help
- What happened
- What the agent already checked
- How urgent it is
- User's language
- Preferred follow-up method

Do NOT send:

- OTP
- UPI PIN
- ATM PIN
- CVV
- Password
- Full bank account number
- Aadhaar number
- Card number
- Any other unnecessary private information

After create_escalation succeeds:

- Tell the user the reference ID.
- Tell the user that the request has been created.
- Explain that a human representative can review it.
- Explain that the request status is OPEN.
- Never promise an immediate response unless the system actually
  guarantees one.

For normal questions that do not require human assistance,
DO NOT create an escalation request.


You have five tools:

1. lookup_user
2. save_user_memory
3. handoff_to_government_scheme_specialist
4. create_escalation
5. end_call

The government scheme document tool is NOT available to you. It
belongs to the Government Scheme Specialist only.


MEMORY RULES:

- Always ask for the user's name at the beginning.
- After receiving the name, use lookup_user with that name.
- If the user is found, greet them using their saved name and
  mention one safe saved detail.
- If the user is not found, ask whether they want you to
  remember their name and useful financial preferences.
- NEVER save anything unless the user explicitly says YES.
- If the user says NO, do not call save_user_memory.
- If the user says YES, you may ask about safe preferences such
  as financial topics they are interested in.
- Never save sensitive financial credentials.

The memory tools use the user's name as their stable identifier.

If the user asks "Do you remember me?", check the memory using
lookup_user if you have their name.

Never claim to remember someone unless lookup_user confirms
that saved information exists.


SCHEME DOCUMENT REQUESTS:

Questions about documents, certificates, proofs, or paperwork
needed for a government scheme are government-scheme requests.
They are OUT OF SCOPE for you and you do NOT have the scheme
document tool.

Always transfer such questions using
handoff_to_government_scheme_specialist. Never answer them
yourself.

This covers questions like:

- "What documents do I need for PM-KISAN?"
- "Which papers are required for a Mudra loan?"
- "What proofs do I need for Ayushman Bharat?"

The specialist reads the document checklist back to the user in
natural spoken language, mentions that the data is from a local
dataset, and states the last updated date.


GOVERNMENT SCHEME SPECIALIST HANDOFF:

You are the general financial services agent. There is also a
dedicated Government Scheme Specialist who handles Indian government
financial schemes in depth: government subsidies, benefits, scheme
eligibility, scheme documents, and general guidance on applying for
government schemes.

Use the handoff_to_government_scheme_specialist tool when the user's
request specifically requires government-scheme assistance, for
example:

- "Which government scheme am I eligible for?"
- "Tell me about government subsidies for farmers."
- "How do I apply for Ayushman Bharat?"
- "What are the benefits of the Atal Pension Yojana?"

DO NOT use the handoff tool for ordinary financial questions such as
savings, budgeting, general finance, general banking, or basic
investment concepts. Those stay with you.

Only hand off when the request specifically requires government-scheme
help. After calling the handoff tool, the specialist continues from
the current conversation, so the user does not have to repeat
anything.
""",
            chat_ctx=chat_ctx,
        )

    # ========================================================
    # LOOKUP USER
    # ========================================================

    @function_tool
    async def lookup_user(
        self,
        context: RunContext,
        name: str,
    ) -> str:
        """
        Look up a caller using their name.
        """

        clean_name = name.strip()

        if not clean_name:
            return "No name was provided."

        user_id = self._make_user_id(clean_name)

        logger.info(
            "Looking up user: %s",
            user_id,
        )

        try:
            user = get_user(user_id)
        except Exception:
            logger.exception("Database lookup failed")
            return "I could not access the memory database right now."

        if user is None:
            logger.info(
                "No saved memory found for: %s",
                user_id,
            )

            return "No saved information was found for this user."

        logger.info(
            "Returning user found: %s",
            user_id,
        )

        return (
            "Returning user found. "
            f"Name: {user.get('name', '')}. "
            f"Language preference: "
            f"{user.get('language_preference', '')}. "
            f"Government schemes discussed: "
            f"{user.get('schemes_checked', '')}. "
            f"Eligibility information: "
            f"{user.get('eligibility_answers', '')}."
        )

    # ========================================================
    # SAVE USER MEMORY
    # ========================================================

    @function_tool
    async def save_user_memory(
        self,
        context: RunContext,
        name: str,
        language_preference: str = "",
        schemes_checked: str = "",
        eligibility_answers: str = "",
    ) -> str:
        """
        Save safe user information.

        Only call this after the user explicitly gives permission.
        """

        clean_name = name.strip()

        if not clean_name:
            return "The user's name is required."

        user_id = self._make_user_id(clean_name)

        logger.info(
            "Saving user memory for: %s",
            user_id,
        )

        try:
            save_user(
                user_id=user_id,
                name=clean_name,
                language_preference=language_preference,
                schemes_checked=schemes_checked,
                eligibility_answers=eligibility_answers,
            )
        except Exception:
            logger.exception("Failed to save user memory")
            return "I could not save the information right now."

        logger.info(
            "User memory saved successfully: %s",
            user_id,
        )

        return f"Memory saved successfully for {clean_name}."

    # ========================================================
    # SCHEME DOCUMENT CHECKLIST
    # ========================================================

    @function_tool
    async def get_scheme_document_checklist(
        self,
        context: RunContext,
        scheme_name: str,
    ) -> str:
        """
        Get the document checklist required to apply for an Indian
        government financial scheme.

        Call this tool when the user asks what documents, certificates,
        proofs, or paperwork they need for a specific government
        scheme, subsidy, insurance plan, or financial programme.
        Trigger for questions like:

        - "What documents do I need for PM-KISAN?"
        - "Which papers are required for a Mudra loan?"
        - "What proofs do I need to apply for Ayushman Bharat?"
        - "List the certificates for Sukanya Samriddhi."

        The tool handles schemes including PM-KISAN, PMJJBY, PMSBY,
        MUDRA loan, Sukanya Samriddhi, Atal Pension Yojana,
        Jan Dhan Yojana, Kisan Credit Card, and Ayushman Bharat.
        """

        logger.info(
            "TOOL CALLED: get_scheme_document_checklist (scheme_name=%s)",
            scheme_name,
        )

        result = get_scheme_document_checklist_text(scheme_name)

        if not result.startswith("Scheme:"):
            return result

        # Mark call as successful
        try:
            ctx = get_job_context()
            room = ctx.room.name
            if room in _call_state:
                _call_state[room]["success"] = True
                _call_state[room]["reason"] = "scheme_checklist"
        except Exception:
            pass

        return result

    # ========================================================
    # GOVERNMENT SCHEME SPECIALIST HANDOFF
    # ========================================================

    @function_tool
    async def handoff_to_government_scheme_specialist(
        self,
        context: RunContext,
    ) -> tuple:
        """
        Hand off the conversation to the Government Scheme Specialist.

        USE THIS TOOL when the user needs dedicated help with an
        Indian government financial scheme, such as:

        - Government financial schemes (PM-KISAN, PMJJBY, PMSBY,
          MUDRA, Sukanya Samriddhi, Atal Pension Yojana, Jan Dhan
          Yojana, Kisan Credit Card, Ayushman Bharat, and similar)
        - Government subsidies and benefits
        - Scheme eligibility
        - Basic scheme requirements and documents
        - General guidance about applying for a government scheme

        DO NOT use this tool for ordinary financial questions such as
        savings, budgeting, general finance, general banking, or basic
        investment concepts. Those stay with you, the general financial
        agent. Only hand off when the request specifically requires
        government-scheme assistance.
        """

        logger.info("TOOL CALLED: handoff_to_government_scheme_specialist")

        try:
            specialist = GovernmentSchemeSpecialist(
                chat_ctx=self.chat_ctx.copy(exclude_instructions=True)
            )
        except Exception:
            logger.exception("Failed to start the government scheme specialist")

            return (
                "I'm sorry, I was unable to connect you to our "
                "government scheme specialist right now. I'll continue "
                "helping you with your question as best I can. What "
                "would you like to know?"
            )

        return (
            specialist,
            "I'll connect you to our government scheme specialist.",
        )

    # ========================================================
    # HUMAN ESCALATION
    # ========================================================

    @function_tool
    async def create_escalation(
        self,
        context: RunContext,
        issue: str,
        summary: str,
        urgency: str,
        language: str,
        preferred_followup: str,
    ) -> str:
        """
        Create a human assistance request.

        IMPORTANT:
        Only call this tool AFTER the user has explicitly given
        permission to share the summarized information with a human.
        """

        logger.info("TOOL CALLED: create_escalation")

        # ----------------------------------------------------
        # Generate reference ID
        # ----------------------------------------------------

        reference_id = f"ESC-{uuid.uuid4().hex[:6].upper()}"

        # ----------------------------------------------------
        # Validate urgency
        # ----------------------------------------------------

        allowed_urgency = {
            "low",
            "medium",
            "high",
            "emergency",
        }

        urgency_clean = urgency.strip().lower()

        if urgency_clean not in allowed_urgency:
            urgency_clean = "medium"

        # ----------------------------------------------------
        # Basic sensitive-information protection
        # ----------------------------------------------------

        sensitive_terms = [
            "otp",
            "upi pin",
            "atm pin",
            "cvv",
            "password",
            "aadhaar",
            "account number",
            "card number",
        ]

        combined_text = (f"{issue} {summary} {language} {preferred_followup}").lower()

        for term in sensitive_terms:
            if term in combined_text:
                logger.warning(
                    "Potential sensitive information detected in escalation request."
                )

                return (
                    "I could not create the human assistance "
                    "request because the information may contain "
                    "sensitive financial data. Please provide only "
                    "a general description of the problem without "
                    "sharing private financial information."
                )

        # ----------------------------------------------------
        # Create human-readable escalation
        # ----------------------------------------------------

        escalation_message = (
            "🚨 HUMAN ESCALATION\n\n"
            f"Reference ID: {reference_id}\n"
            f"Issue: {issue}\n"
            f"Summary: {summary}\n"
            f"Urgency: {urgency_clean.upper()}\n"
            f"Language: {language}\n"
            f"Preferred follow-up: {preferred_followup}\n"
            f"Status: OPEN"
        )

        # ----------------------------------------------------
        # Get Discord webhook
        # ----------------------------------------------------

        webhook_url = os.getenv("DISCORD_ESCALATION_WEBHOOK_URL")

        if not webhook_url:
            logger.error("DISCORD_ESCALATION_WEBHOOK_URL is not configured.")

            return (
                "The human assistance request could not be created "
                "because the escalation service is not configured."
            )

        # ----------------------------------------------------
        # Send request to Discord
        # ----------------------------------------------------

        try:
            response = requests.post(
                webhook_url,
                json={"content": escalation_message},
                timeout=10,
            )

            response.raise_for_status()

        except Exception:
            logger.exception("Failed to send escalation request.")

            return (
                "I could not create the human assistance request "
                "right now. Please try again later."
            )

        # ----------------------------------------------------
        # Log successful request
        # ----------------------------------------------------

        logger.info(
            "Escalation created successfully: %s",
            reference_id,
        )

        # Mark call as successful
        try:
            ctx = get_job_context()
            room = ctx.room.name
            if room in _call_state:
                _call_state[room]["success"] = True
                _call_state[room]["reason"] = "escalation"
        except Exception:
            pass

        return (
            f"Human assistance request created successfully. "
            f"Reference ID: {reference_id}. "
            f"Status: OPEN."
        )

    # ========================================================
    # STABLE USER ID
    # ========================================================

    @staticmethod
    def _make_user_id(name: str) -> str:
        """
        Convert a name into a stable database user ID.

        Example:
        Moovini -> user_moovini
        Mohini Daf -> user_mohini_daf
        """

        clean_name = name.strip().lower()

        clean_name = "_".join(clean_name.split())

        return f"user_{clean_name}"

    # ========================================================
    # END CALL
    # ========================================================

    @function_tool
    async def end_call(
        self,
        context: RunContext,
    ) -> str:
        """
        End the current phone call. Call this when the user says
        goodbye, asks to stop, or the conversation is finished.
        Also call this if the user asks you to stop calling them.
        """

        logger.info("TOOL CALLED: end_call")

        job_ctx = get_job_context()
        room_name = job_ctx.room.name

        # Log call outcome
        state = _call_state.pop(room_name, None)
        if state:
            outcome = "success" if state["success"] else "failed"
            log_call_end(
                call_id=state["call_id"],
                outcome=outcome,
                success_reason=state.get("reason", ""),
            )
            logger.info(
                "Call logged: %s (%s)",
                state["call_id"],
                outcome,
            )

        await job_ctx.delete_room()

        return "Call ended."


# ============================================================
# LIVEKIT SERVER
# ============================================================

server = AgentServer()


# IMPORTANT:
# This must match the agent name requested by the frontend.
# ============================================================


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):

    logger.info("========================================")
    logger.info("Agent received a room request")
    logger.info("========================================")

    # --------------------------------------------------------
    # PARSE METADATA
    # --------------------------------------------------------

    metadata = {}

    raw_metadata = ctx.job.metadata

    if raw_metadata:
        try:
            metadata = json.loads(raw_metadata)

        except (json.JSONDecodeError, TypeError):
            logger.warning(
                "Could not parse job metadata: %s",
                raw_metadata,
            )

    is_outbound = metadata.get(
        "outbound",
        False,
    )

    phone_number = metadata.get(
        "phone_number",
        "",
    )

    if is_outbound:
        logger.info(
            "Outbound call requested to: %s",
            phone_number,
        )

    else:
        logger.info("Browser/WebRTC session (not outbound)")

    # --------------------------------------------------------
    # CONNECT
    # --------------------------------------------------------

    await ctx.connect()

    room_name = ctx.room.name

    logger.info(
        "Agent connected to room: %s",
        room_name,
    )

    # --------------------------------------------------------
    # REGISTER CALL START
    # --------------------------------------------------------

    call_id = uuid.uuid4().hex[:12]
    channel = "outbound" if is_outbound else "browser"

    log_call_start(call_id, room_name, channel)

    _call_state[room_name] = {
        "call_id": call_id,
        "success": False,
        "reason": "",
    }

    # Log call end if room disconnects without end_call
    def on_room_disconnect():
        state = _call_state.pop(room_name, None)
        if state:
            outcome = "success" if state["success"] else "failed"
            log_call_end(
                call_id=state["call_id"],
                outcome=outcome,
                success_reason=state.get("reason", ""),
            )
            logger.info(
                "Call logged (room disconnect): %s (%s)",
                state["call_id"],
                outcome,
            )

    ctx.room.on("disconnected", on_room_disconnect)

    # --------------------------------------------------------
    # OUTBOUND CALL: CREATE SIP PARTICIPANT
    # --------------------------------------------------------

    demo_mode = False

    if is_outbound:
        trunk_id = os.getenv(
            "SIP_OUTBOUND_TRUNK_ID",
            "",
        )

        if not trunk_id:
            logger.warning(
                "SIP_OUTBOUND_TRUNK_ID not set — running in "
                "DEMO mode (outbound greeting will play in "
                "this terminal)"
            )

            demo_mode = True

        if not phone_number:
            phone_number = "demo-user"

        if not demo_mode:
            logger.info(
                "Creating SIP participant: trunk=%s, call_to=%s",
                trunk_id,
                phone_number,
            )

            try:
                await ctx.add_sip_participant(
                    call_to=phone_number,
                    trunk_id=trunk_id,
                    participant_identity=phone_number,
                    participant_name="Outbound caller",
                )

            except api.TwirpError as e:
                sip_code = e.metadata.get(
                    "sip_status_code",
                    "unknown",
                )

                sip_status = e.metadata.get(
                    "sip_status",
                    "unknown",
                )

                logger.error(
                    "SIP call failed: %s (SIP %s %s) — falling back to demo mode",
                    e.message,
                    sip_code,
                    sip_status,
                )

                demo_mode = True

            except Exception:
                logger.exception("SIP call error — falling back to demo mode")

                demo_mode = True

        if not demo_mode:
            logger.info("SIP participant created, waiting for answer...")

            try:
                participant = await ctx.wait_for_participant(
                    identity=phone_number,
                )

            except Exception:
                logger.exception("Timed out waiting — falling back to demo mode")

                demo_mode = True

            else:
                logger.info(
                    "SIP participant joined: %s",
                    participant.identity,
                )

    # --------------------------------------------------------
    # CREATE VOICE SESSION
    # --------------------------------------------------------

    logger.info("Creating FinAssist voice session...")

    session = AgentSession(
        stt=deepgram.STT(),
        llm=inference.LLM(
            model="google/gemini-2.5-flash-lite",
            extra_kwargs={"max_completion_tokens": 1000},
        ),
        tts=murf.TTS(),
    )

    # --------------------------------------------------------
    # START SESSION
    # --------------------------------------------------------

    await session.start(
        room=ctx.room,
        agent=FinAssist(),
    )

    logger.info("========================================")
    logger.info("FinAssist session started successfully")
    logger.info("========================================")

    # --------------------------------------------------------
    # FIRST MESSAGE
    # --------------------------------------------------------

    if is_outbound:
        await session.generate_reply(
            instructions="""
You are placing an outbound phone call on behalf of FinAssist,
an AI financial voice assistant for India.

The user did NOT initiate this call. You called them.

Your opening MUST include ALL of the following in order:

1. Greet the user and say who is calling:

"Hello, this is FinAssist, an AI-powered financial
assistant calling on behalf of our team."

2. State the purpose of the call:

"I'm calling to follow up on financial services you may
be interested in, such as government schemes, banking,
UPI, loans, or insurance."

3. Clearly state this is an automated/AI call:

"Please note, this is an automated AI call."

4. Give the user a way to opt out:

"If you do not wish to receive calls like this, you can
say stop at any time, and we will not call you again."

Then ask:

"How are you today? Is this a good time to talk?"

IMPORTANT RULES:

- Be polite and professional.
- Do NOT be pushy. If the user says they are busy or
  do not want to talk, say goodbye and use the end_call
  tool.
- If the user asks you to stop calling, use end_call
  immediately.
- Keep the conversation short and helpful.
- After the greeting, follow the standard memory rules
  (ask name, look up user, etc.) if the user agrees
  to continue talking.
"""
        )

    else:
        await session.generate_reply(
            instructions="""
Start the conversation.

Say:

"Hello, I'm FinAssist. I can help you with banking,
UPI, loans, cards, insurance, and other financial services."

Then ask:

"Before we begin, may I know your name?"

IMPORTANT:

Wait for the user's name.

After the user gives their name:

1. Call lookup_user using exactly the name the user provided.

2. If lookup_user says that no saved information exists:

Say:

"Nice to meet you, [name]. Would you like me to remember
your name and some useful financial preferences for your
future conversations?"

3. WAIT for the user's answer.

4. If the user clearly says YES:

Ask:

"What financial topic are you most interested in?
For example, government schemes, UPI, loans, or insurance."

5. After they answer, call save_user_memory.

Use:

- name = user's name
- language_preference = language if explicitly known
- schemes_checked = the financial topic they mentioned
- eligibility_answers = only general eligibility information
  if they actually provided it

6. If the user says NO:

Do NOT call save_user_memory.

Continue the conversation normally.

7. If lookup_user finds the user:

Say:

"Welcome back, [name]. It's good to speak with you again."

Then mention one safe detail returned by lookup_user.

For example:

"I remember you were interested in government schemes."

Do not invent memories.


IMPORTANT HUMAN ESCALATION RULE:

If the user reports possible fraud, an unauthorized or
unrecognized transaction, or asks for a financial decision
that requires human review:

1. Explain that human assistance is needed.
2. Tell the user what information will be shared.
3. Ask for explicit permission.
4. Wait for the user's answer.
5. Only if the user clearly agrees, call create_escalation.
6. If the user says NO, do not call create_escalation.
7. After successful escalation, provide the reference ID
   and explain that the request is OPEN.

Never include OTPs, PINs, CVVs, passwords, full account
numbers, Aadhaar numbers, or other sensitive credentials
in the escalation.
"""
        )


# ============================================================
# START WORKER
# ============================================================

if __name__ == "__main__":
    cli.run_app(server)
