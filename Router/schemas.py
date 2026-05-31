from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentResult:
    agent_name: str
    items: list[dict[str, Any]] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    error: Any = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "items": self.items,
            "sources": self.sources,
            "metadata": self.metadata,
            "error": self.error,
        }


@dataclass
class RouterRequest:
    query: str
    profile: dict[str, Any]
    user_id: str | None = None


@dataclass
class RouterState:
    query: str
    profile: dict[str, Any]
    user_id: str | None = None
    classification: dict[str, Any] = field(default_factory=dict)
    agents: dict[str, dict[str, Any]] = field(default_factory=dict)
    formatted_context: dict[str, str] = field(default_factory=dict)
    final_answer: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    error: Any = None
