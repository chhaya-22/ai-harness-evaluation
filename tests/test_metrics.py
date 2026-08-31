from harness_eval.metrics.consistency import ConsistencyMetric
from harness_eval.metrics.correctness import CorrectnessMetric
from harness_eval.metrics.failure import FailureRateMetric
from harness_eval.metrics.latency import LatencyMetric
from harness_eval.metrics.structured import StructuredOutputMetric
from harness_eval.metrics.tools import ToolCallMetric
from harness_eval.models import HarnessResponse, TestCase, ToolCall


def resp(output="ok", latency=1.0, error=None, **kw):
    return HarnessResponse(output=output, latency_s=latency, error=error, **kw)


def test_correctness_exact_match_scores_one():
    case = TestCase(id="c", prompt="p", expected="Paris")
    result = CorrectnessMetric().score(case, [resp(output="Paris")])
    assert result.score == 1.0


def test_correctness_wrong_answer_scores_zero():
    case = TestCase(id="c", prompt="p", expected="Paris")
    result = CorrectnessMetric().score(case, [resp(output="Berlin")])
    assert result.score == 0.0


def test_correctness_skipped_when_no_expected():
    case = TestCase(id="c", prompt="p")  # no expected answer
    result = CorrectnessMetric().score(case, [resp(output="anything")])
    assert result.score == 1.0  # skipped, not penalised


def test_failure_rate_counts_errors():
    case = TestCase(id="c", prompt="p")
    responses = [resp(), resp(error="timeout"), resp(), resp()]
    result = FailureRateMetric().score(case, responses)
    assert result.score == 0.75  # 1 of 4 failed


def test_consistency_all_same_is_perfect():
    case = TestCase(id="c", prompt="p")
    result = ConsistencyMetric().score(case, [resp(output="x")] * 4)
    assert result.score == 1.0


def test_consistency_drops_when_outputs_vary():
    case = TestCase(id="c", prompt="p")
    responses = [resp(output="x"), resp(output="x"), resp(output="y"), resp(output="z")]
    result = ConsistencyMetric().score(case, responses)
    assert result.score == 0.5  # most common ("x") appears 2 of 4 times


def test_latency_fast_scores_high():
    case = TestCase(id="c", prompt="p")
    result = LatencyMetric().score(case, [resp(latency=0.5)] * 3)
    assert result.score == 1.0  # under the "good" threshold


def test_latency_slow_scores_low():
    case = TestCase(id="c", prompt="p")
    result = LatencyMetric().score(case, [resp(latency=15.0)] * 3)
    assert result.score == 0.0  # over the "bad" ceiling


def test_structured_output_valid_json():
    case = TestCase(id="c", prompt="p", output_schema={"required": ["name", "age"]})
    result = StructuredOutputMetric().score(case, [resp(output='{"name": "A", "age": 30}')])
    assert result.score == 1.0


def test_structured_output_missing_key():
    case = TestCase(id="c", prompt="p", output_schema={"required": ["name", "age"]})
    result = StructuredOutputMetric().score(case, [resp(output='{"name": "A"}')])
    assert result.score == 0.0  # 'age' missing


def test_structured_output_invalid_json():
    case = TestCase(id="c", prompt="p", output_schema={"required": ["name"]})
    result = StructuredOutputMetric().score(case, [resp(output="not json at all")])
    assert result.score == 0.0


def test_tool_calling_all_expected_tools_present():
    case = TestCase(id="c", prompt="p", expected_tools=["get_weather"])
    r = resp(tool_calls=[ToolCall(name="get_weather")])
    result = ToolCallMetric().score(case, [r])
    assert result.score == 1.0


def test_tool_calling_missing_tool():
    case = TestCase(id="c", prompt="p", expected_tools=["get_weather"])
    result = ToolCallMetric().score(case, [resp(tool_calls=[])])
    assert result.score == 0.0