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