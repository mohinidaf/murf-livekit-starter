import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    RunContext,
    cli,
    function_tool,
    inference,
)

from database import get_user, save_user
from scheme_data import (
    DATA_SOURCE,
    LAST_UPDATED,
    get_scheme_info,
    list_available_schemes,
)

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
    def __init__(self):
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
- Government financial schemes

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

You have three tools:

1. lookup_user
2. save_user_memory
3. get_scheme_document_checklist

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

SCHEME DOCUMENT TOOL:

When the user asks what documents, certificates, proofs, or
paperwork are needed for any Indian government financial scheme,
call get_scheme_document_checklist with the scheme name.

This covers questions like:
- "What documents do I need for PM-KISAN?"
- "Which papers are required for a Mudra loan?"
- "What proofs do I need for Ayushman Bharat?"

When you read the result back to the user, convert it into
natural spoken language. Do NOT read JSON or bullet symbols.
Mention that the data is from a local dataset and state the
last updated date.

If the tool returns a failure, tell the user you cannot access
the information right now and do not want to give inaccurate
details. Do NOT invent document lists if the tool fails.
"""
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

        if not scheme_name or not scheme_name.strip():
            available = list_available_schemes()
            return (
                "No scheme name was provided. "
                f"Available schemes: {', '.join(available)}. "
                "Please ask about a specific scheme."
            )

        try:
            info = get_scheme_info(scheme_name)
        except Exception:
            logger.exception("Failed to look up scheme data")
            return (
                "FAILURE: Unable to access scheme information "
                "right now. I do not want to give you inaccurate "
                "information. Please try again later or check the "
                "official scheme website."
            )

        if info is None:
            available = list_available_schemes()
            logger.info(
                "Scheme not found: %s. Available: %s",
                scheme_name,
                available,
            )
            return (
                f"I could not find a scheme called '{scheme_name}'. "
                f"Available schemes are: {', '.join(available)}. "
                "Please ask about one of these schemes."
            )

        doc_list = "\n".join(f"- {doc}" for doc in info["documents"])

        result = (
            f"Scheme: {info['full_name']}\n"
            f"Objective: {info['objective']}\n"
            f"Required documents:\n{doc_list}\n"
            f"Eligibility notes: {info['eligibility_notes']}\n"
            f"Data source: {DATA_SOURCE}\n"
            f"Data last updated: {LAST_UPDATED}\n"
            f"Data type: Local dataset (not live data)"
        )

        logger.info(
            "Scheme checklist returned for: %s",
            info["full_name"],
        )

        return result

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
    # CONNECT
    # --------------------------------------------------------

    await ctx.connect()

    logger.info(
        "Agent connected to room: %s",
        ctx.room.name,
    )

    # --------------------------------------------------------
    # CREATE VOICE SESSION
    # --------------------------------------------------------

    logger.info("Creating FinAssist voice session...")

    session = AgentSession(
        stt=inference.STT(
            model="deepgram/nova-3",
        ),
        llm=inference.LLM(
            model="openai/gpt-4o-mini",
        ),
        tts=inference.TTS(
            model="cartesia/sonic-3",
        ),
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

IMPORTANT:

Never say that you remember the user unless lookup_user
actually returned saved information.
"""
    )


# ============================================================
# START WORKER
# ============================================================

if __name__ == "__main__":
    cli.run_app(server)
