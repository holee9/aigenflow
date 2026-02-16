"""
Cache key generator following FR-1 requirements.

Implements SHA-256 based cache key generation with:
- Prompt text
- Context hash (including previous phase results)
- Agent type
- Phase number
- Model version

Reference: SPEC-ENHANCE-004 FR-1
"""

import hashlib
import json
from typing import Any

from core.models import AgentType


class CacheKeyGenerator:
    """
    Generates unique cache keys based on request parameters.

    Uses SHA-256 hashing algorithm with normalization for consistency.
    """

    def generate(
        self,
        prompt: str,
        context: dict[str, Any] | None = None,
        agent_type: AgentType | None = None,
        phase: int | None = None,
        model_version: str | None = None,
    ) -> str:
        """
        Generate a unique cache key for the given parameters.

        Args:
            prompt: The prompt text (normalized)
            context: Additional context (e.g., previous phase summary)
            agent_type: The AI agent type
            phase: Pipeline phase number
            model_version: Model version identifier

        Returns:
            A 64-character hex string (SHA-256 hash)
        """
        # Normalize prompt: remove extra whitespace
        normalized_prompt = self._normalize_text(prompt)

        # Build key components
        components = {
            "prompt": normalized_prompt,
        }

        # Add optional components
        if context:
            # Hash context to avoid huge keys
            context_hash = self._hash_dict(context)
            components["context"] = context_hash

        if agent_type:
            components["agent"] = agent_type.value

        if phase is not None:
            components["phase"] = str(phase)

        if model_version:
            components["model"] = model_version

        # Create deterministic string representation
        key_string = json.dumps(components, sort_keys=True)

        # Generate SHA-256 hash
        return hashlib.sha256(key_string.encode()).hexdigest()

    def _normalize_text(self, text: str) -> str:
        """
        Normalize text for consistent hashing.

        - Converts multiple spaces to single space
        - Removes leading/trailing whitespace
        - Preserves case (case-sensitive prompts)
        - Normalizes newlines to spaces

        Args:
            text: Input text

        Returns:
            Normalized text
        """
        # Replace newlines with spaces
        text = text.replace("\n", " ").replace("\r", " ")

        # Collapse multiple spaces to single space
        text = " ".join(text.split())

        # Strip leading/trailing
        return text.strip()

    def _hash_dict(self, data: dict[str, Any]) -> str:
        """
        Create hash from dictionary for compact representation.

        Args:
            data: Dictionary to hash

        Returns:
            Hex string hash (first 16 chars of SHA-256)
        """
        # Sort keys for deterministic output
        sorted_json = json.dumps(data, sort_keys=True)

        # Return first 16 characters of hash (enough for collision resistance)
        return hashlib.sha256(sorted_json.encode()).hexdigest()[:16]
