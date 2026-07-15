from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

from eval.domain.scenario import ScenarioFixture
from eval.domain.taxonomy import TaxonomyRegistry

MatrixTier = Literal["smoke", "judge"]


@dataclass(frozen=True)
class ScenarioRef:
    """Lightweight scenario reference for coverage cells."""

    id: str
    tags: tuple[str, ...]
    description: str


@dataclass(frozen=True)
class ScenarioRunSnapshot:
    """Normalized run row for coverage aggregation."""

    scenario_id: str
    tier: str
    mode: str
    status: str
    finished_at: str | None
    passed: bool | None


@dataclass(frozen=True)
class CoverageCell:
    """One domain × tier matrix cell."""

    domain: str
    domain_label: str
    tier: MatrixTier
    scenario_count: int
    scenarios: tuple[ScenarioRef, ...]
    tags_covered: tuple[str, ...]
    tags_expected: tuple[str, ...]
    tags_missing: tuple[str, ...]
    tier_expected: bool
    last_run_at: str | None
    pass_count: int
    fail_count: int
    pass_rate: float | None


@dataclass(frozen=True)
class TagCoverageRow:
    """Global tag coverage summary."""

    tag: str
    scenario_count: int
    domains: tuple[str, ...]


@dataclass(frozen=True)
class CoverageMatrix:
    """Full coverage matrix snapshot."""

    generated_at: str
    cells: tuple[CoverageCell, ...]
    tag_coverage: tuple[TagCoverageRow, ...]


def runs_from_summaries(summaries: list[dict[str, object]]) -> tuple[ScenarioRunSnapshot, ...]:
    """Convert persisted run summary dicts into coverage snapshots."""

    snapshots: list[ScenarioRunSnapshot] = []
    for item in summaries:
        if item.get("mode", "scenario") != "scenario":
            continue
        status = str(item.get("status", "failed"))
        assertions_passed = item.get("assertions_passed")
        judge_passed = item.get("judge_overall_passed")
        passed: bool | None = None
        if status == "completed":
            if assertions_passed is False:
                passed = False
            elif judge_passed is False:
                passed = False
            elif assertions_passed is True or assertions_passed is None:
                passed = True
            else:
                passed = bool(assertions_passed)
        elif status in {"failed", "cancelled"}:
            passed = False
        snapshots.append(
            ScenarioRunSnapshot(
                scenario_id=str(item.get("scenario_id", "")),
                tier=str(item.get("tier", "smoke")),
                mode=str(item.get("mode", "scenario")),
                status=status,
                finished_at=(
                    str(item["finished_at"]) if item.get("finished_at") is not None else None
                ),
                passed=passed,
            )
        )
    return tuple(snapshots)


def _normalize_scenario_id(scenario_id: str) -> str:
    return scenario_id.replace("\\", "/").strip("/")


def _latest_runs_by_scenario(
    runs: tuple[ScenarioRunSnapshot, ...],
) -> dict[tuple[str, str], ScenarioRunSnapshot]:
    """Map (scenario_id, tier) to the latest finished run."""

    latest: dict[tuple[str, str], ScenarioRunSnapshot] = {}
    for run in runs:
        if run.tier not in {"smoke", "judge"}:
            continue
        key = (_normalize_scenario_id(run.scenario_id), run.tier)
        if not key[0]:
            continue
        existing = latest.get(key)
        if existing is None:
            latest[key] = run
            continue
        existing_at = existing.finished_at or ""
        current_at = run.finished_at or ""
        if current_at >= existing_at:
            latest[key] = run
    return latest


def _lookup_latest_run(
    latest_runs: dict[tuple[str, str], ScenarioRunSnapshot],
    *,
    rel_id: str,
    short_id: str,
    tier: str,
) -> ScenarioRunSnapshot | None:
    for candidate in (_normalize_scenario_id(rel_id), _normalize_scenario_id(short_id)):
        if not candidate:
            continue
        run = latest_runs.get((candidate, tier))
        if run is not None:
            return run
    return None


def build_coverage_matrix(
    *,
    loaded_scenarios: list[tuple[str, ScenarioFixture]],
    runs: tuple[ScenarioRunSnapshot, ...],
    registry: TaxonomyRegistry,
) -> CoverageMatrix:
    """Build domain × tier coverage matrix from fixtures and run history."""

    latest_runs = _latest_runs_by_scenario(runs)
    cells: list[CoverageCell] = []
    tag_to_domains: dict[str, set[str]] = {}
    tag_counts: dict[str, int] = {}

    matrix_tiers: tuple[MatrixTier, ...] = ("smoke", "judge")
    for domain in registry.domains:
        for tier in matrix_tiers:
            domain_items = [
                (rel_id, item)
                for rel_id, item in loaded_scenarios
                if item.domain == domain.id and item.tier == tier
            ]
            refs = tuple(
                ScenarioRef(
                    id=rel_id,
                    tags=tuple(item.tags),
                    description=item.description,
                )
                for rel_id, item in domain_items
            )
            tags_covered_set: set[str] = set()
            for _, item in domain_items:
                tags_covered_set.update(item.tags)
                for tag in item.tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
                    tag_to_domains.setdefault(tag, set()).add(domain.id)
            tags_covered = tuple(sorted(tags_covered_set))
            tier_expected = True
            if tier == "judge" and not registry.judge_expected_for(domain.id):
                tier_expected = False
                tags_expected = ()
                tags_missing = ()
            else:
                tags_expected = registry.recommended_tags_for(domain.id)
                tags_missing = tuple(sorted(set(tags_expected) - tags_covered_set))

            pass_count = 0
            fail_count = 0
            last_run_at: str | None = None
            for rel_id, item in domain_items:
                run = _lookup_latest_run(
                    latest_runs,
                    rel_id=rel_id,
                    short_id=item.id,
                    tier=tier,
                )
                if run is None:
                    continue
                if run.passed is True:
                    pass_count += 1
                elif run.passed is False:
                    fail_count += 1
                if run.finished_at and (last_run_at is None or run.finished_at > last_run_at):
                    last_run_at = run.finished_at

            total = pass_count + fail_count
            pass_rate = (pass_count / total) if total > 0 else None

            cells.append(
                CoverageCell(
                    domain=domain.id,
                    domain_label=domain.label,
                    tier=tier,
                    scenario_count=len(domain_items),
                    scenarios=refs,
                    tags_covered=tags_covered,
                    tags_expected=tags_expected,
                    tags_missing=tags_missing,
                    tier_expected=tier_expected,
                    last_run_at=last_run_at,
                    pass_count=pass_count,
                    fail_count=fail_count,
                    pass_rate=pass_rate,
                )
            )

    tag_coverage = tuple(
        TagCoverageRow(
            tag=tag,
            scenario_count=tag_counts[tag],
            domains=tuple(sorted(tag_to_domains.get(tag, set()))),
        )
        for tag in sorted(tag_counts)
    )

    return CoverageMatrix(
        generated_at=datetime.now(tz=UTC).isoformat(),
        cells=tuple(cells),
        tag_coverage=tag_coverage,
    )
