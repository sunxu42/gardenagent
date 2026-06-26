from eval.domain.coverage import (
    ScenarioRunSnapshot,
    build_coverage_matrix,
    runs_from_summaries,
)
from eval.domain.scenario import ScenarioFixture, UserDriverConfig, UserTurn
from eval.domain.taxonomy import load_taxonomy


def _scenario(
    *,
    scenario_id: str,
    domain: str,
    tier: str = "smoke",
    tags: list[str] | None = None,
) -> ScenarioFixture:
    return ScenarioFixture(
        id=scenario_id,
        domain=domain,
        tags=tags or ["happy_path"],
        tier=tier,  # type: ignore[arg-type]
        description="test",
        user_driver=UserDriverConfig(type="scripted", turns=[UserTurn(text="hi")]),
    )


def _loaded(
    rel_id: str,
    fixture: ScenarioFixture,
) -> list[tuple[str, ScenarioFixture]]:
    return [(rel_id, fixture)]


def test_build_coverage_matrix_sixteen_cells() -> None:
    registry = load_taxonomy()
    loaded = [
        *_loaded("smoke/greeting_01", _scenario(scenario_id="greeting_01", domain="persona")),
        *_loaded(
            "smoke/memory_recall_01",
            _scenario(
                scenario_id="memory_recall_01",
                domain="memory",
                tags=["memory_recall", "multi_turn"],
            ),
        ),
    ]
    matrix = build_coverage_matrix(loaded_scenarios=loaded, runs=(), registry=registry)
    assert len(matrix.cells) == 16


def test_pass_rate_uses_latest_run_per_scenario() -> None:
    registry = load_taxonomy()
    loaded = _loaded(
        "smoke/greeting_01",
        _scenario(scenario_id="greeting_01", domain="persona", tags=["happy_path"]),
    )
    runs = (
        ScenarioRunSnapshot(
            scenario_id="greeting_01",
            tier="smoke",
            mode="scenario",
            status="failed",
            finished_at="2026-01-01T00:00:00+00:00",
            passed=False,
        ),
        ScenarioRunSnapshot(
            scenario_id="greeting_01",
            tier="smoke",
            mode="scenario",
            status="completed",
            finished_at="2026-01-02T00:00:00+00:00",
            passed=True,
        ),
    )
    matrix = build_coverage_matrix(loaded_scenarios=loaded, runs=runs, registry=registry)
    persona_smoke = next(cell for cell in matrix.cells if cell.domain == "persona" and cell.tier == "smoke")
    assert persona_smoke.pass_rate == 1.0
    assert persona_smoke.pass_count == 1


def test_smoke_and_judge_with_same_yaml_id_get_distinct_paths() -> None:
    registry = load_taxonomy()
    loaded = [
        *_loaded(
            "smoke/emotion_anxious_01",
            _scenario(
                scenario_id="emotion_anxious_01",
                domain="emotion",
                tier="smoke",
                tags=["mood_anxious", "single_turn"],
            ),
        ),
        *_loaded(
            "judge/emotion_anxious_01",
            _scenario(
                scenario_id="emotion_anxious_01",
                domain="emotion",
                tier="judge",
                tags=["mood_anxious", "multi_turn"],
            ),
        ),
    ]
    matrix = build_coverage_matrix(loaded_scenarios=loaded, runs=(), registry=registry)
    emotion_smoke = next(cell for cell in matrix.cells if cell.domain == "emotion" and cell.tier == "smoke")
    emotion_judge = next(cell for cell in matrix.cells if cell.domain == "emotion" and cell.tier == "judge")
    assert [ref.id for ref in emotion_smoke.scenarios] == ["smoke/emotion_anxious_01"]
    assert [ref.id for ref in emotion_judge.scenarios] == ["judge/emotion_anxious_01"]


def test_runs_from_summaries_skips_exploratory() -> None:
    snapshots = runs_from_summaries(
        [
            {"mode": "exploratory", "scenario_id": "x", "tier": "exploratory", "status": "completed"},
            {
                "mode": "scenario",
                "scenario_id": "greeting_01",
                "tier": "smoke",
                "status": "completed",
                "assertions_passed": True,
            },
        ]
    )
    assert len(snapshots) == 1
    assert snapshots[0].passed is True
