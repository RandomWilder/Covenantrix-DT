"""
Entity domain models
"""
from enum import Enum
from dataclasses import dataclass
from typing import List


class EntityType(Enum):
    """Entity type enumeration"""
    PERSON = "person"
    ORGANIZATION = "organization"
    GEO = "geo"
    EVENT = "event"
    CATEGORY = "category"


@dataclass
class Entity:
    """Entity data class"""
    name: str
    type: EntityType
    description: str
    relationship_count: int = 0


@dataclass
class EntitySummary:
    """Grouped entity summary"""
    people: List[Entity]
    organizations: List[Entity]
    locations: List[Entity]
    financial: List[Entity]
    dates_and_terms: List[Entity]
