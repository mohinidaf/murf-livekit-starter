"""
Day 9: Government Scheme Specialist handoff tests.

These are offline structural/behaviour tests. They do not require
LiveKit credentials or an LLM. They verify:

- The main FinAssist agent exposes the handoff tool.
- The handoff tool returns a GovernmentSchemeSpecialist plus a
  transition message, and preserves the conversation history.
- The specialist only exposes scheme-related tools (it is not a
  general-purpose financial agent).
- The specialist can hand back to the main agent.
- The shared scheme checklist text builder behaves correctly.

Run with:
    uv run pytest tests/test_government_scheme_handoff.py
"""

from livekit.agents import llm

from agent import FinAssist
from government_scheme_specialist import GovernmentSchemeSpecialist
from scheme_data import get_scheme_document_checklist_text


def _tool_names(agent) -> set[str]:
    return {tool.info.name for tool in agent.tools}


def _make_history() -> llm.ChatContext:
    chat_ctx = llm.ChatContext()
    chat_ctx.add_message(role="user", content="I need PM-KISAN documents")
    chat_ctx.add_message(role="assistant", content="Sure, let me help you.")
    return chat_ctx


async def test_finassist_exposes_handoff_tool() -> None:
    agent = FinAssist()

    names = _tool_names(agent)

    assert "handoff_to_government_scheme_specialist" in names
    assert "get_scheme_document_checklist" in names
    # Day 8 tools must remain available
    assert {"lookup_user", "save_user_memory", "create_escalation", "end_call"} <= names


async def test_specialist_is_not_a_general_agent() -> None:
    specialist = GovernmentSchemeSpecialist()

    names = _tool_names(specialist)

    assert "get_scheme_document_checklist" in names
    assert "handoff_back_to_main_agent" in names
    # No general-purpose financial tools
    assert not (
        {"lookup_user", "save_user_memory", "create_escalation", "end_call"} & names
    )


async def test_handoff_returns_specialist_and_preserves_history() -> None:
    chat_ctx = _make_history()
    agent = FinAssist(chat_ctx=chat_ctx)

    result = await agent.handoff_to_government_scheme_specialist(context=object())

    assert isinstance(result, tuple)
    assert len(result) == 2

    specialist, message = result

    assert isinstance(specialist, GovernmentSchemeSpecialist)
    assert "specialist" in message.lower()

    # The specialist carries the existing conversation context.
    messages = specialist.chat_ctx.messages()
    spoken = [item.content for item in messages]
    assert any("PM-KISAN documents" in str(c) for c in spoken)


async def test_handoff_failure_path_returns_string() -> None:
    agent = FinAssist()

    # Force the specialist constructor to fail so the graceful fallback
    # message is returned instead of an agent.
    original = GovernmentSchemeSpecialist.__init__
    try:
        GovernmentSchemeSpecialist.__init__ = lambda *a, **kw: (_ for _ in ()).throw(
            RuntimeError("boom")
        )
        result = await agent.handoff_to_government_scheme_specialist(context=object())
    finally:
        GovernmentSchemeSpecialist.__init__ = original

    assert isinstance(result, str)
    assert "unable to connect" in result.lower()


async def test_specialist_can_hand_back_to_main_agent() -> None:
    specialist = GovernmentSchemeSpecialist(chat_ctx=_make_history())

    result = await specialist.handoff_back_to_main_agent(context=object())

    assert isinstance(result, tuple)
    main_agent, message = result
    assert isinstance(main_agent, FinAssist)
    assert "main financial assistant" in message.lower()


def test_scheme_checklist_text_builder() -> None:
    result = get_scheme_document_checklist_text("pm kisan")
    assert result.startswith("Scheme:")
    assert "Pradhan Mantri Kisan" in result

    missing = get_scheme_document_checklist_text("no such scheme")
    assert "I could not find a scheme" in missing

    empty = get_scheme_document_checklist_text("")
    assert "No scheme name was provided" in empty
