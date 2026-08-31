import abc
import random
import time

from .models import HarnessResponse, TestCase, ToolCall


class Harness(abc.ABC):
    """A harness takes one test case and returns a single response.

    Subclass this to evaluate a real system: wrap your prompt/model/tool
    orchestration inside run() and fill in the response fields you can measure.
    """

    name: str = "base"

    @abc.abstractmethod
    def run(self, case: TestCase) -> HarnessResponse: ...


class MockHarness(Harness):
    """Deterministic-ish stand-in so the framework runs offline.

    Echoes the expected answer most of the time, occasionally fails or drifts,
    so metrics like consistency and failure-rate have something to measure.
    """

    name = "mock"

    def __init__(self, fail_rate: float = 0.05, seed: int | None = None):
        self.fail_rate = fail_rate
        self._rng = random.Random(seed)

    def run(self, case: TestCase) -> HarnessResponse:
        latency = self._rng.uniform(0.3, 2.5)
        time.sleep(0.0)  # keep tests fast; real harness would actually block

        if self._rng.random() < self.fail_rate:
            return HarnessResponse(output="", latency_s=latency, error="simulated timeout")

        output = case.expected or f"response to: {case.prompt[:40]}"
        if self._rng.random() < 0.15:            # occasional drift for consistency to catch
            output += " "
        tokens_in = len(case.prompt.split())
        tokens_out = len(output.split())
        tools = [ToolCall(name=t) for t in case.expected_tools]
        return HarnessResponse(
            output=output,
            latency_s=latency,
            input_tokens=tokens_in,
            output_tokens=tokens_out,
            cost_usd=(tokens_in * 3 + tokens_out * 15) / 1_000_000,
            tool_calls=tools,
        )

class FlawedHarness(Harness):
    """A deliberately imperfect harness for demonstrating the framework.

    Unlike MockHarness, this one sometimes returns wrong answers, drops tool
    calls, and emits malformed JSON — so failed-case detection and
    recommendations have something real to report. It represents a weaker
    harness version you'd want the framework to catch.
    """

    name = "flawed"

    def __init__(self, seed: int | None = None):
        self._rng = random.Random(seed)

    def run(self, case: TestCase) -> HarnessResponse:
        latency = self._rng.uniform(1.0, 6.0)   # slower than the good mock

        # 15% of runs fail outright.
        if self._rng.random() < 0.15:
            return HarnessResponse(output="", latency_s=latency, error="simulated timeout")

        # 30% of the time, return a wrong / degraded answer.
        degraded = self._rng.random() < 0.30
        if case.expected and not degraded:
            output = case.expected
        elif case.expected:
            output = "I'm not sure about that."        # wrong answer
        else:
            output = f"response to: {case.prompt[:40]}"

        # Drop tool calls half the time when tools were expected.
        if case.expected_tools and self._rng.random() < 0.5:
            tools = []                                  # missed the tool call
        else:
            tools = [ToolCall(name=t) for t in case.expected_tools]

        tokens_in = len(case.prompt.split())
        tokens_out = len(output.split())
        return HarnessResponse(
            output=output,
            latency_s=latency,
            input_tokens=tokens_in,
            output_tokens=tokens_out,
            cost_usd=(tokens_in * 3 + tokens_out * 15) / 1_000_000,
            tool_calls=tools,
        )