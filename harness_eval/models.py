from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class TestCase(BaseModel):
    id: str
    prompt: str
    category: str = "general"
    expected: str | None = None
    expected_tools: list[str] = Field(default_factory=list)
    output_schema: dict[str, Any] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ToolCall(BaseModel):
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class HarnessResponse(BaseModel):
    output: str
    latency_s: float
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    tool_calls: list[ToolCall] = Field(default_factory=list)
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None


class MetricResult(BaseModel):
    metric: str
    score: float                 # normalized 0..1, higher is better
    value: float | None = None   # raw measured number, e.g. p95 seconds
    details: dict[str, Any] = Field(default_factory=dict)