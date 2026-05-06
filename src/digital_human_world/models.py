from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import IntEnum, StrEnum
from typing import Any


TICK_SECONDS = 10
NIGHT_CONSOLIDATION_HOUR = 21


class Weather(StrEnum):
    CLEAR = "clear"
    RAIN = "rain"


class LocationKind(StrEnum):
    INDOOR = "indoor"
    OUTDOOR = "outdoor"


class ActionType(StrEnum):
    GO = "GO"
    DO = "DO"
    USE = "USE"
    SPEAK = "SPEAK"
    REST = "REST"
    LEARN = "LEARN"


class EventType(StrEnum):
    DECISION = "decision"
    TASK_ASSIGNED = "task_assigned"
    WEATHER_CHANGED = "weather_changed"
    ACTION_STARTED = "action_started"
    ACTION_COMPLETED = "action_completed"
    ACTION_FAILED = "action_failed"
    ACTION_INTERRUPTED = "action_interrupted"
    TOOL_ACQUIRED = "tool_acquired"
    TOOL_RETURNED = "tool_returned"
    PROFILE_UPDATED = "profile_updated"
    INFO = "info"


class EventPriority(IntEnum):
    LOW = 1
    NORMAL = 2
    HIGH = 3


@dataclass(slots=True)
class Location:
    id: str
    name: str
    kind: LocationKind
    neighbors: list[str]
    tools: list[str] = field(default_factory=list)


@dataclass(slots=True)
class WorldTask:
    id: str
    name: str
    kind: str
    location_id: str
    required_tool: str | None = None
    active: bool = False
    completed: bool = False
    target_progress: int = 100
    progress: int = 0


@dataclass(slots=True)
class Event:
    event_type: EventType
    timestamp: datetime
    message: str
    priority: EventPriority = EventPriority.NORMAL
    actor_id: str | None = None
    target_ids: list[str] = field(default_factory=list)
    location_id: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Observation:
    timestamp: datetime
    location_id: str
    location_name: str
    location_kind: LocationKind
    weather: Weather
    visible_people: list[str]
    visible_tools: list[str]
    visible_tasks: list[str]
    self_state: dict[str, Any]
    text: str


@dataclass(slots=True)
class ObservationDelta:
    changed: bool
    significant: bool
    messages: list[str] = field(default_factory=list)


@dataclass(slots=True)
class WorkingMemory:
    active_goal: str | None = None
    current_intent: str | None = None
    recent_observation_changes: deque[str] = field(default_factory=lambda: deque(maxlen=6))
    recent_events: deque[str] = field(default_factory=lambda: deque(maxlen=10))
    recent_outcomes: deque[str] = field(default_factory=lambda: deque(maxlen=10))
    episodic_buffer: list[dict[str, Any]] = field(default_factory=list)


@dataclass(slots=True)
class Profile:
    identity: str
    stable_traits: list[str] = field(default_factory=list)
    learned_rules: dict[str, str] = field(default_factory=dict)
    preferences: dict[str, float] = field(default_factory=dict)
    skills: dict[str, int] = field(default_factory=dict)
    habits: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ActionPlan:
    action_type: ActionType
    target: str
    duration_ticks: int
    label: str
    payload: dict[str, Any] = field(default_factory=dict)
    interruptible: bool = True


@dataclass(slots=True)
class ActionInstance:
    action_type: ActionType
    target: str
    total_ticks: int
    remaining_ticks: int
    label: str
    started_at: datetime
    payload: dict[str, Any] = field(default_factory=dict)
    interruptible: bool = True


@dataclass(slots=True)
class Person:
    id: str
    name: str
    location_id: str
    home_id: str
    inventory: list[str] = field(default_factory=list)
    hunger: int = 10
    fatigue: int = 10
    emotion: str = "calm"
    autonomous: bool = True
    working_memory: WorkingMemory = field(default_factory=WorkingMemory)
    profile: Profile = field(default_factory=lambda: Profile(identity="proto-human"))
    current_action: ActionInstance | None = None
    last_observation: Observation | None = None


@dataclass(slots=True)
class WorldState:
    current_time: datetime
    weather: Weather
    locations: dict[str, Location]
    people: dict[str, Person]
    tasks: dict[str, WorldTask]
    last_consolidation_day: datetime.date | None = None

    def advance(self) -> None:
        self.current_time += timedelta(seconds=TICK_SECONDS)

    def location(self, location_id: str) -> Location:
        return self.locations[location_id]

    def is_outdoors(self, person: Person) -> bool:
        return self.location(person.location_id).kind is LocationKind.OUTDOOR

    def distance_in_ticks(self, start_id: str, end_id: str) -> int:
        if start_id == end_id:
            return 1

        frontier: deque[tuple[str, int]] = deque([(start_id, 0)])
        visited = {start_id}

        while frontier:
            location_id, distance = frontier.popleft()
            if location_id == end_id:
                return max(1, distance)
            for neighbor_id in self.location(location_id).neighbors:
                if neighbor_id in visited:
                    continue
                visited.add(neighbor_id)
                frontier.append((neighbor_id, distance + 1))

        raise ValueError(f"unreachable location: {start_id} -> {end_id}")
