from pathlib import Path

import pytest

from eval.domain.taxonomy import load_taxonomy


def test_load_taxonomy_has_eight_domains() -> None:
    registry = load_taxonomy()
    assert len(registry.domains) == 8
    assert "memory" in registry.domain_ids
    assert "transport" in registry.domain_ids


def test_all_tags_union() -> None:
    registry = load_taxonomy()
    assert "jailbreak" in registry.all_tags
    assert "memory_recall" in registry.all_tags
    assert "mood_happy" in registry.all_tags
    assert "stage_exploration" in registry.all_tags


def test_validate_scenario_tags_rejects_unknown_tag() -> None:
    registry = load_taxonomy()
    with pytest.raises(ValueError, match="unknown tag"):
        registry.validate_scenario(domain="emotion", tags=["not_a_real_tag"])


def test_validate_scenario_tags_rejects_unknown_domain() -> None:
    registry = load_taxonomy()
    with pytest.raises(ValueError, match="unknown domain"):
        registry.validate_scenario(domain="unknown", tags=["happy_path"])


def test_validate_scenario_tags_requires_one_to_three() -> None:
    registry = load_taxonomy()
    with pytest.raises(ValueError, match="tags count"):
        registry.validate_scenario(domain="emotion", tags=[])
    with pytest.raises(ValueError, match="tags count"):
        registry.validate_scenario(
            domain="emotion",
            tags=["mood_anxious", "mood_sad", "mood_angry", "single_turn"],
        )


def test_load_taxonomy_missing_file_returns_empty_registry(tmp_path: Path) -> None:
    missing = tmp_path / "missing.yaml"
    registry = load_taxonomy(path=missing)
    assert registry.domains == ()
    assert registry.is_degraded is True
