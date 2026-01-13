"""
AI agents package.

This package exposes available AI agent implementations.  The default
``SimpleAgent`` provides a trivial echo implementation for testing
purposes.  To integrate an actual LLM, create a new module that
implements a class with a ``get_response`` method and import it here.
"""

from .simple_agent import SimpleAgent  # noqa: F401

__all__ = ["SimpleAgent"]