"""
LLMClient
---------
Thin wrapper around the Anthropic Messages API. Kept separate from the
handler so the LLM provider can be swapped (Bedrock, OpenAI, etc.) without
touching retrieval or prompt logic.
"""

from __future__ import annotations

import logging
import os

import anthropic

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self, model: str, temperature: float = 0.2, max_tokens: int = 800):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        # Reads ANTHROPIC_API_KEY from environment (set via Lambda env var /
        # Secrets Manager in production — never hardcode keys).
        self.client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    def generate(self, prompt: str) -> str:
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[{"role": "user", "content": prompt}],
            )
            return "".join(
                block.text for block in response.content if block.type == "text"
            ).strip()
        except Exception:
            logger.exception("LLM call failed")
            raise
