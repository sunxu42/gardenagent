import os

import pytest


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "smoke: PR smoke eval scenarios (L0 only)")
    config.addinivalue_line("markers", "judge: DeepEval judge scenarios (Nightly)")
    config.addinivalue_line(
        "markers",
        "integration: requires live AgentManager and LLM",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if os.getenv("EVAL_INTEGRATION") == "1":
        return
    skip_integration = pytest.mark.skip(
        reason="set EVAL_INTEGRATION=1 to run live AgentManager integration tests",
    )
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)
