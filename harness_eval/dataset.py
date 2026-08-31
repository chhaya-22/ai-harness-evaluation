import json
from pathlib import Path

from .models import TestCase


def load_dataset(path: str | Path) -> list[TestCase]:
    """Load a dataset of test cases from a JSON file.

    The file is a plain list of objects; each becomes a TestCase. New
    datasets can be dropped in as JSON with no code changes, and Pydantic
    validates the shape so a malformed case fails loudly instead of silently.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"dataset not found: {path}")

    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError(f"dataset must be a JSON list, got {type(raw).__name__}")

    return [TestCase(**item) for item in raw]