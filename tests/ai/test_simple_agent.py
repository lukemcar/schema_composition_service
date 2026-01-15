"""Tests for the SimpleAgent AI wrapper."""

from app.ai.agents import SimpleAgent


def test_simple_agent_echo() -> None:
    """Ensure the SimpleAgent echoes the prompt in its response."""
    agent = SimpleAgent()
    prompt = "Hello, SchemaComposition!"
    response = agent.get_response(prompt)
    assert isinstance(response, dict)
    assert response.get("response") == prompt