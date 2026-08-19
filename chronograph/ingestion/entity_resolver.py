import hashlib
from dataclasses import dataclass, field
from typing import List, Set, Dict

from rapidfuzz import fuzz

@dataclass
class ResolvedEntity:
    canonical_name: str
    entity_type: str
    aliases: Set[str] = field(default_factory=set)
    
    @property
    def id(self) -> str:
        return hashlib.sha256(self.canonical_name.encode('utf-8')).hexdigest()

class EntityResolver:
    def __init__(self):
        self.entities: Dict[str, ResolvedEntity] = {}
        self.threshold = 85.0
        
    def _normalize(self, name: str) -> str:
        return name.lower().strip()
        
    def resolve(self, name: str, entity_type: str = 'unknown') -> ResolvedEntity:
        """Resolve a name to an existing or new entity."""
        normalized_name = self._normalize(name)
        
        # Exact match
        for entity in self.entities.values():
            if normalized_name in [self._normalize(alias) for alias in entity.aliases] or \
               normalized_name == self._normalize(entity.canonical_name):
                entity.aliases.add(name)
                return entity
                
        # Fuzzy match
        for entity in self.entities.values():
            score = fuzz.ratio(normalized_name, self._normalize(entity.canonical_name))
            if score >= self.threshold:
                entity.aliases.add(name)
                return entity
                
            for alias in entity.aliases:
                alias_score = fuzz.ratio(normalized_name, self._normalize(alias))
                if alias_score >= self.threshold:
                    entity.aliases.add(name)
                    return entity
                    
        # Create new
        new_entity = ResolvedEntity(
            canonical_name=name,
            entity_type=entity_type,
            aliases={name}
        )
        self.entities[new_entity.id] = new_entity
        return new_entity
        
    def get_all_entities(self) -> List[ResolvedEntity]:
        """Return all tracked entities."""
        return list(self.entities.values())
