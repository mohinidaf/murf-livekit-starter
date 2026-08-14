"""
Government Scheme Specialist agent for FinAssist.

This specialist handles Indian government financial schemes ONLY:
schemes, subsidies, benefits, eligibility, required documents, and
general guidance on applying for relevant government schemes.

It is intentionally NOT a general-purpose financial agent. If the
conversation moves outside its scope, it hands the call back to the
main FinAssist agent.
"""

import logging

from livekit.agents import (
    Agent,
    RunContext,
    function_tool,
)

from scheme_data import (
    get_scheme_document_checklist_text,
)

logger = logging.getLogger("finassist")


class GovernmentSchemeSpecialist(Agent):
    def __init__(self, chat_ctx=None):
        super().__init__(
            instructions="""
You are the Government Scheme Specialist at FinAssist.

Your ONLY responsibility is helping with Indian government financial
schemes:

- Government financial schemes
- Government subsidies and benefits
- Scheme eligibility
- Basic scheme requirements and documents
- General guidance about applying for relevant government schemes

You are NOT a general-purpose financial agent. Do NOT answer general
questions about savings, budgeting, general finance, general banking,
or basic investment concepts. Those are handled by the main FinAssist
agent. If the user asks about such topics, politely use the
handoff_back_to_main_agent tool so the main agent can take over.

Keep your answers short, natural and easy to understand because this
is a voice conversation.

When the user asks what documents, certificates, proofs, or paperwork
are needed for any Indian government financial scheme, call
get_scheme_document_checklist with the scheme name.

This covers questions like:

- "What documents do I need for PM-KISAN?"
- "Which papers are required for a Mudra loan?"
- "What proofs do I need for Ayushman Bharat?"

When you read the result back to the user, convert it into natural
spoken language. Do NOT read JSON or bullet symbols. Mention that the
data is from a local dataset and state the last updated date.

If the tool returns a failure, tell the user you cannot access the
information right now and do not want to give inaccurate details. Do
NOT invent document lists if the tool fails.

Common schemes you may be asked about: PM-KISAN, PMJJBY, PMSBY,
MUDRA, Sukanya Samriddhi Yojana, Atal Pension Yojana, Jan Dhan Yojana,
Kisan Credit Card, Ayushman Bharat, and PM Swayam Siksha Prayog.
""",
            chat_ctx=chat_ctx,
        )

    async def on_enter(self) -> None:
        await self.session.generate_reply(
            instructions="""
Introduce yourself naturally and continue the existing conversation.

Say something like:

"Hi, I'm the Government Scheme Specialist. I understand you're
looking for information about a government financial scheme.
Let me help you with that."

Do NOT ask the user to repeat themselves or explain their whole
problem again. Use the conversation history that is already present.
If the user's scheme question is already clear from the conversation,
continue helping them directly.
"""
        )

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
            "SPECIALIST TOOL CALLED: get_scheme_document_checklist (scheme_name=%s)",
            scheme_name,
        )

        return get_scheme_document_checklist_text(scheme_name)

    # ========================================================
    # HANDOFF BACK TO MAIN AGENT
    # ========================================================

    @function_tool
    async def handoff_back_to_main_agent(
        self,
        context: RunContext,
    ) -> tuple:
        """
        Hand the conversation back to the main FinAssist agent.

        Use this tool when the user asks a question that is NOT about
        Indian government financial schemes, such as general banking,
        savings, budgeting, loans, insurance, UPI, or basic investment
        questions. The main agent is better suited for those topics.
        """

        # Local import avoids a circular import at module load time.
        from agent import FinAssist  # isort: skip

        logger.info("SPECIALIST TOOL CALLED: handoff_back_to_main_agent")

        return (
            FinAssist(chat_ctx=self.chat_ctx.copy(exclude_instructions=True)),
            "I'll connect you back to the main financial assistant.",
        )
