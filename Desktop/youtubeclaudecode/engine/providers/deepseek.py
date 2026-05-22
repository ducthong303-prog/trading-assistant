"""YouTube AI Factory v4.1 — DeepSeek Script Generation Router

Routes script generation through DeepSeek V4 Pro (cheaper).
Claude Code handles orchestration; DeepSeek handles script drafting.

This module provides the interface for calling DeepSeek for
script generation, returning text that Claude then reviews/humanizes.
"""
from engine.utils.config import get_env


class DeepSeekRouter:
    """Routes script generation requests to DeepSeek V4 Pro.

    In practice, script generation is done through Claude Code's
    agent routing (the proxy handles the DeepSeek backend).
    This module serves as the configuration and tracking layer.
    """

    def __init__(self):
        self.model = "deepseek-v4"
        self.proxy_enabled = bool(get_env("DEEPSEEK_PROXY_URL"))

    def get_model_for_script(self) -> str:
        """Return which model to use for script generation."""
        if self.proxy_enabled:
            return self.model
        return "claude"  # Fallback to Claude if proxy not available

    def estimate_tokens(self, word_count: int) -> dict:
        """Estimate token usage for a script of given word count.
        Rough estimate: 1 word ≈ 1.3 tokens (Hebrew/Greek words add overhead).
        """
        tokens = int(word_count * 1.3)
        return {
            "model": self.model,
            "word_count": word_count,
            "estimated_tokens": tokens,
            "estimated_cost": round(tokens * 0.0014 / 1000, 4),  # $0.0014/1K tokens
        }
