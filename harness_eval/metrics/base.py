import abc

from ..models import HarnessResponse, MetricResult, TestCase

_REGISTRY: dict[str, type["Metric"]] = {}


def register(cls: type["Metric"]) -> type["Metric"]:
    _REGISTRY[cls.name] = cls
    return cls


def get_metric(name: str) -> "Metric":
    return _REGISTRY[name]()


def all_metrics() -> list[str]:
    return list(_REGISTRY)

def metric_info() -> list[dict]:
    """Return name + category for every registered metric, for display."""
    info = []
    for name, cls in _REGISTRY.items():
        info.append({
            "name": name,
            "category": getattr(cls, "category", "uncategorised"),
            "higher_is_better": getattr(cls, "higher_is_better", True),
        })
    return sorted(info, key=lambda x: x["name"])    


class Metric(abc.ABC):
    """Scores one test case given all repeated responses for it.

    Takes a list because we run each case k times to measure consistency
    and get stable latency percentiles.
    """

    name: str
    category: str
    higher_is_better: bool = True

    @abc.abstractmethod
    def score(self, case: TestCase, responses: list[HarnessResponse]) -> MetricResult: ...