"""Vertical base class — the re-purposable framework entry point.

A Vertical packages domain-specific agents, tools, and prompts for a
particular business use case (revenue intelligence, customer success, etc.).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class VerticalConfig:
    """Configuration for a vertical."""

    name: str
    description: str
    version: str = "0.1.0"
    default_model: str = "litellm/deepseek/deepseek-chat"
    metric_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class Vertical:
    """Base class for business verticals.

    Subclass this to create domain-specific agent packs:

        class RevenueIntelligence(Vertical):
            config = VerticalConfig(
                name="revenue",
                description="SaaS revenue intelligence",
                metric_ids=["mrr", "churn", "arpu", ...],
            )

    Then register agents and tools via the provided methods.
    """

    config: VerticalConfig

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, "config"):
            raise TypeError(f"Vertical subclass {cls.__name__} must define a 'config' class attribute")

    @classmethod
    def get_name(cls) -> str:
        return cls.config.name

    @classmethod
    def get_description(cls) -> str:
        return cls.config.description
