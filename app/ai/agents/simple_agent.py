"""
Minimal AI agent implementation for the MyEntity service.

This agent simply echoes back the prompt it receives in a structured
response.  It demonstrates how to encapsulate AI logic in a class and
provides a clear extension point for integrating a real large language
model (LLM) or other AI provider.  When adding new agents follow this
pattern: implement a ``get_response`` method that accepts your
input(s) and returns a response object or dict.
"""

from __future__ import annotations

from typing import Any, Dict


class SimpleAgent:
    """A simple echo agent used as a placeholder for AI functionality.

    The agent exposes a single method, ``get_response``, which takes a
    text prompt and returns a dictionary containing the same text.  This
    allows callers to test the AI integration points without invoking
    external services.  Replace the implementation of ``get_response``
    with calls to your LLM of choice as needed.
    """

    def __init__(self) -> None:
        # No state is required for this agent
        pass

    def get_response(self, prompt: str) -> Dict[str, Any]:
        """Return a simple JSON response containing the input prompt.

        Args:
            prompt: The user or system prompt to process.

        Returns:
            A dictionary with a single key ``response`` echoing the prompt.
        """
        return {"response": prompt}