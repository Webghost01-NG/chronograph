"""Entity resolution and alias normalization engine for ChronoGraph."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

from rapidfuzz import fuzz


@dataclass
class ResolvedEntity:
    canonical_name: str
    entity_type: str
    aliases: set[str] = field(default_factory=set)

    @property
    def id(self) -> str:
        return hashlib.sha256(self.canonical_name.encode("utf-8")).hexdigest()


class EntityResolver:
    def __init__(self, threshold: float = 75.0):
        self.entities: dict[str, ResolvedEntity] = {}
        self.threshold = threshold

    def _normalize(self, name: str) -> str:
        return name.lower().strip()

    def resolve(self, name: str, entity_type: str = "unknown") -> ResolvedEntity:
        """Resolve an incoming entity name to an existing canonical entity or create a new one."""
        normalized_name = self._normalize(name)
        if not normalized_name:
            return ResolvedEntity(canonical_name="Unknown", entity_type=entity_type)

        # 1. Exact match against canonical name or known aliases
        for entity in self.entities.values():
            canon_norm = self._normalize(entity.canonical_name)
            if normalized_name == canon_norm or normalized_name in [
                self._normalize(a) for a in entity.aliases
            ]:
                entity.aliases.add(name)
                return entity

        # 2. Substring containment (e.g. "Uniswap Labs" contains "Uniswap")
        for entity in self.entities.values():
            canon_norm = self._normalize(entity.canonical_name)
            if (
                len(normalized_name) > 3
                and len(canon_norm) > 3
                and (normalized_name in canon_norm or canon_norm in normalized_name)
            ):
                entity.aliases.add(name)
                return entity

        # 3. Fuzzy match using token set ratio
        for entity in self.entities.values():
            canon_norm = self._normalize(entity.canonical_name)
            score = max(
                fuzz.ratio(normalized_name, canon_norm),
                fuzz.token_set_ratio(normalized_name, canon_norm),
            )
            if score >= self.threshold:
                entity.aliases.add(name)
                return entity

            for alias in entity.aliases:
                alias_score = max(
                    fuzz.ratio(normalized_name, self._normalize(alias)),
                    fuzz.token_set_ratio(normalized_name, self._normalize(alias)),
                )
                if alias_score >= self.threshold:
                    entity.aliases.add(name)
                    return entity

        # 4. Create new entity
        new_entity = ResolvedEntity(canonical_name=name, entity_type=entity_type, aliases={name})
        self.entities[new_entity.id] = new_entity
        return new_entity

    def get_all_entities(self) -> list[ResolvedEntity]:
        """Return all tracked entities."""
        return list(self.entities.values())
