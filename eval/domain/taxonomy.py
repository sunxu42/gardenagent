from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from shared.config.paths import resolve_eval_taxonomy_path
from shared.observability.logging import LogModule, get_logger

_log = get_logger(LogModule.EVAL)


class DomainDef(BaseModel):
    """One eval capability domain from taxonomy.yaml."""

    id: str
    label: str
    description: str = ""
    priority: int = 1
    recommended_tags: list[str] = Field(default_factory=list)
    # When false, empty judge tier is intentional (smoke_only domain).
    judge_expected: bool = True


class TagGroupDef(BaseModel):
    """Grouped tag labels for taxonomy display."""

    label: str
    tags: list[str] = Field(default_factory=list)


class TaxonomyDocument(BaseModel):
    """Parsed taxonomy.yaml document."""

    version: int = 1
    domains: list[DomainDef] = Field(default_factory=list)
    tag_groups: dict[str, TagGroupDef] = Field(default_factory=dict)


@dataclass(frozen=True)
class TaxonomyRegistry:
    """Loaded taxonomy with validation helpers."""

    domains: tuple[DomainDef, ...]
    all_tags: frozenset[str]
    is_degraded: bool = False

    @property
    def domain_ids(self) -> frozenset[str]:
        return frozenset(domain.id for domain in self.domains)

    def domain_by_id(self, domain_id: str) -> DomainDef | None:
        for domain in self.domains:
            if domain.id == domain_id:
                return domain
        return None

    def recommended_tags_for(self, domain_id: str) -> tuple[str, ...]:
        domain = self.domain_by_id(domain_id)
        if domain is None:
            return ()
        return tuple(domain.recommended_tags)

    def judge_expected_for(self, domain_id: str) -> bool:
        domain = self.domain_by_id(domain_id)
        if domain is None:
            return True
        return bool(domain.judge_expected)

    def validate_scenario(self, *, domain: str, tags: list[str]) -> None:
        """Validate scenario domain and tags against the taxonomy."""

        if self.is_degraded:
            return
        if domain not in self.domain_ids:
            raise ValueError(f"unknown domain: {domain}")
        if not 1 <= len(tags) <= 3:
            raise ValueError(f"tags count must be 1-3, got {len(tags)}")
        unknown = [tag for tag in tags if tag not in self.all_tags]
        if unknown:
            raise ValueError(f"unknown tag: {unknown[0]}")
        recommended = set(self.recommended_tags_for(domain))
        if recommended and not recommended.intersection(tags):
            _log.warning(
                f"scenario domain={domain} tags={tags} have no overlap with recommended_tags",
            )


def _build_registry(document: TaxonomyDocument, *, is_degraded: bool) -> TaxonomyRegistry:
    all_tags: set[str] = set()
    for group in document.tag_groups.values():
        all_tags.update(group.tags)
    return TaxonomyRegistry(
        domains=tuple(document.domains),
        all_tags=frozenset(all_tags),
        is_degraded=is_degraded,
    )


def load_taxonomy(path: Path | None = None) -> TaxonomyRegistry:
    """Load taxonomy from YAML, or return a degraded empty registry."""

    taxonomy_path = path or resolve_eval_taxonomy_path()
    if not taxonomy_path.is_file():
        _log.warning(f"taxonomy file missing: {taxonomy_path} — degraded mode")
        return TaxonomyRegistry(domains=(), all_tags=frozenset(), is_degraded=True)
    data = yaml.safe_load(taxonomy_path.read_text(encoding="utf-8"))
    document = TaxonomyDocument.model_validate(data or {})
    return _build_registry(document, is_degraded=False)


@lru_cache(maxsize=1)
def get_taxonomy_registry() -> TaxonomyRegistry:
    """Return the cached taxonomy registry for the process."""

    return load_taxonomy()
