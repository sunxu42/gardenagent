import json

from eval.api.routes import _json
from eval.api.schemas import ScenarioSummary


def test_json_serializes_scenario_summary_list() -> None:
    response = _json(
        [
            ScenarioSummary(
                id="smoke/greeting_01",
                description="基础问候",
                domain="persona",
                tier="smoke",
                tags=["happy_path", "identity_disclosure"],
            )
        ]
    )
    assert response.status_code == 200
    payload = json.loads(response.body)
    assert payload == [
        {
            "id": "smoke/greeting_01",
            "description": "基础问候",
            "domain": "persona",
            "tier": "smoke",
            "tags": ["happy_path", "identity_disclosure"],
        }
    ]
