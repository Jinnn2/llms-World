from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time
from typing import Any
from typing import Callable

from .models import (
    ActionInstance,
    ActionType,
    Event,
    EventPriority,
    EventType,
    NIGHT_CONSOLIDATION_HOUR,
    Observation,
    ObservationDelta,
    Person,
    WorldState,
)
from .policy import DecisionPolicy, PolicyDecision


ScheduledCallback = Callable[[WorldState], list[Event]]


@dataclass(slots=True)
class ScheduledWorldEvent:
    at: datetime
    name: str
    callback: ScheduledCallback
    fired: bool = False


class Inspector:
    def capture(self, person: Person, world: WorldState) -> Observation:
        location = world.location(person.location_id)
        visible_people = sorted(
            other.name
            for other in world.people.values()
            if other.id != person.id and other.location_id == person.location_id
        )
        visible_tools = list(location.tools)
        visible_tasks = sorted(
            task.name
            for task in world.tasks.values()
            if task.location_id == person.location_id and task.active and not task.completed
        )

        self_state = {
            "location": location.name,
            "inventory": list(person.inventory),
            "fatigue": person.fatigue,
            "emotion": person.emotion,
            "active_goal": person.working_memory.active_goal,
            "current_intent": person.working_memory.current_intent,
        }

        text = (
            f"Location={location.name}; Weather={world.weather}; "
            f"VisiblePeople={visible_people}; VisibleTools={visible_tools}; "
            f"VisibleTasks={visible_tasks}; SelfState={self_state}"
        )

        return Observation(
            timestamp=world.current_time,
            location_id=location.id,
            location_name=location.name,
            location_kind=location.kind,
            weather=world.weather,
            visible_people=visible_people,
            visible_tools=visible_tools,
            visible_tasks=visible_tasks,
            self_state=self_state,
            text=text,
        )


class ObservationDiffer:
    def diff(
        self, previous: Observation | None, current: Observation
    ) -> ObservationDelta:
        if previous is None:
            return ObservationDelta(
                changed=True,
                significant=True,
                messages=["initial observation created"],
            )

        changes: list[str] = []
        if previous.location_id != current.location_id:
            changes.append(
                f"location changed from {previous.location_name} to {current.location_name}"
            )
        if previous.weather != current.weather:
            changes.append(f"weather changed from {previous.weather} to {current.weather}")
        if previous.visible_tools != current.visible_tools:
            changes.append(
                f"visible tools changed from {previous.visible_tools} to {current.visible_tools}"
            )
        if previous.visible_tasks != current.visible_tasks:
            changes.append(
                f"visible tasks changed from {previous.visible_tasks} to {current.visible_tasks}"
            )
        if previous.visible_people != current.visible_people:
            changes.append(
                f"visible people changed from {previous.visible_people} to {current.visible_people}"
            )

        return ObservationDelta(
            changed=bool(changes),
            significant=bool(changes),
            messages=changes,
        )


class MemoryManager:
    def ingest_events(self, world: WorldState, events: list[Event]) -> None:
        for event in events:
            for person in world.people.values():
                if not person.autonomous:
                    continue
                if not self._event_relevant(person, event):
                    continue
                self._remember_event(person, event)

    def remember_observation_delta(
        self, person: Person, delta: ObservationDelta
    ) -> None:
        for message in delta.messages:
            person.working_memory.recent_observation_changes.append(message)

    def consolidate(self, world: WorldState) -> list[Event]:
        events: list[Event] = []
        for person in world.people.values():
            if not person.autonomous:
                continue

            changes: list[str] = []
            for episode in person.working_memory.episodic_buffer:
                if (
                    episode["event_type"] == EventType.ACTION_FAILED.value
                    and episode["payload"].get("reason") == "missing_tool"
                    and episode["payload"].get("task_id") == "clean_square"
                    and person.profile.learned_rules.get(
                        "clean_square_requires_broom"
                    )
                    != "broom"
                ):
                    person.profile.learned_rules["clean_square_requires_broom"] = "broom"
                    changes.append("learned that square cleaning requires a broom")

                if (
                    episode["event_type"] == EventType.WEATHER_CHANGED.value
                    and episode["payload"].get("weather") == "rain"
                    and episode["payload"].get("outdoor_exposure")
                ):
                    if person.profile.preferences.get("avoid_outdoor_in_rain", 0.0) < 1.0:
                        person.profile.preferences["avoid_outdoor_in_rain"] = 1.0
                        changes.append("formed a stable preference to avoid outdoor work in rain")

            if changes:
                events.append(
                    Event(
                        event_type=EventType.PROFILE_UPDATED,
                        timestamp=world.current_time,
                        message=f"profile updated: {', '.join(changes)}",
                        actor_id=person.id,
                        target_ids=[person.id],
                        payload={"changes": changes},
                    )
                )

            person.working_memory.current_intent = None
            person.working_memory.recent_observation_changes.clear()
            person.working_memory.recent_events.clear()
            person.working_memory.recent_outcomes.clear()
            person.working_memory.episodic_buffer.clear()

        world.last_consolidation_day = world.current_time.date()
        return events

    def build_model_input(self, person: Person, observation: Observation) -> str:
        wm = person.working_memory
        return "\n".join(
            [
                f"OBSERVATION: {observation.text}",
                f"ACTIVE_GOAL: {wm.active_goal}",
                f"CURRENT_INTENT: {wm.current_intent}",
                f"RECENT_OBS_CHANGES: {list(wm.recent_observation_changes)}",
                f"RECENT_EVENTS: {list(wm.recent_events)}",
                f"RECENT_OUTCOMES: {list(wm.recent_outcomes)}",
                f"PROFILE_RULES: {person.profile.learned_rules}",
                f"PROFILE_PREFERENCES: {person.profile.preferences}",
            ]
        )

    def _remember_event(self, person: Person, event: Event) -> None:
        person.working_memory.recent_events.append(event.message)
        person.working_memory.episodic_buffer.append(
            {
                "timestamp": event.timestamp.isoformat(),
                "event_type": event.event_type.value,
                "message": event.message,
                "payload": dict(event.payload),
            }
        )

        if event.event_type is EventType.TASK_ASSIGNED:
            person.working_memory.active_goal = event.payload["task_id"]
        if event.event_type is EventType.ACTION_STARTED and event.actor_id == person.id:
            person.working_memory.current_intent = event.payload["label"]
        if event.event_type in {
            EventType.ACTION_COMPLETED,
            EventType.ACTION_FAILED,
            EventType.ACTION_INTERRUPTED,
        } and event.actor_id == person.id:
            person.working_memory.recent_outcomes.append(event.message)
            person.working_memory.current_intent = None
            if event.payload.get("task_completed"):
                person.working_memory.active_goal = None

    def _event_relevant(self, person: Person, event: Event) -> bool:
        if person.id == event.actor_id:
            return True
        if person.id in event.target_ids:
            return True
        if event.location_id and event.location_id == person.location_id:
            return True
        return False


class SimulationEngine:
    def __init__(
        self,
        world: WorldState,
        policy: DecisionPolicy,
        scheduled_events: list[ScheduledWorldEvent],
    ) -> None:
        self.world = world
        self.policy = policy
        self.scheduled_events = sorted(scheduled_events, key=lambda item: item.at)
        self.inspector = Inspector()
        self.differ = ObservationDiffer()
        self.memory = MemoryManager()
        self.logs: list[str] = []
        self.event_history: list[Event] = []
        self.tick_history: list[dict[str, Any]] = []

    def run_until(self, end_time: datetime) -> list[str]:
        while self.world.current_time < end_time:
            self.step()
        return self.logs

    def step(self) -> None:
        previous_time = self.world.current_time
        self.world.advance()

        events: list[Event] = []
        events.extend(self._fire_scheduled_events())
        events.extend(self._progress_actions())

        if self._should_consolidate(previous_time, self.world.current_time):
            events.extend(self.memory.consolidate(self.world))
            events.extend(self._return_borrowed_tools())

        self.memory.ingest_events(self.world, events)

        decision_events: list[Event] = []
        for person in self.world.people.values():
            if not person.autonomous:
                continue

            observation = self.inspector.capture(person, self.world)
            delta = self.differ.diff(person.last_observation, observation)
            self.memory.remember_observation_delta(person, delta)
            relevant_events = [event for event in events if self._event_relevant(person, event)]
            trigger_reasons = self._build_trigger_reasons(person, delta, relevant_events)

            if person.current_action and self._should_interrupt(person, relevant_events):
                decision_events.extend(self._interrupt_action(person))
                trigger_reasons.append("high_priority_interrupt")

            if person.current_action is None and trigger_reasons:
                decision = self.policy.decide(person, observation, trigger_reasons, self.world)
                decision_events.extend(self._start_action(person, decision, observation, trigger_reasons))

            person.last_observation = observation

        self.memory.ingest_events(self.world, decision_events)
        for event in events + decision_events:
            self._log_event(event)
        self._record_tick_snapshot()

    def _fire_scheduled_events(self) -> list[Event]:
        events: list[Event] = []
        for scheduled in self.scheduled_events:
            if scheduled.fired or scheduled.at > self.world.current_time:
                continue
            scheduled.fired = True
            events.extend(scheduled.callback(self.world))
        return events

    def _progress_actions(self) -> list[Event]:
        events: list[Event] = []
        for person in self.world.people.values():
            if person.current_action is None:
                continue
            person.current_action.remaining_ticks -= 1
            self._advance_go_action_position(person)
            if person.current_action.remaining_ticks > 0:
                continue
            events.extend(self._resolve_action(person))
        return events

    def _advance_go_action_position(self, person: Person) -> None:
        action = person.current_action
        if action is None or action.action_type is not ActionType.GO:
            return
        route = action.payload.get("route")
        if not isinstance(route, list) or not route:
            return
        elapsed_ticks = action.total_ticks - action.remaining_ticks
        route_index = min(elapsed_ticks, len(route) - 1)
        next_location_id = route[route_index]
        if next_location_id in self.world.locations:
            person.location_id = next_location_id

    def _resolve_action(self, person: Person) -> list[Event]:
        action = person.current_action
        if action is None:
            return []

        person.current_action = None
        now = self.world.current_time

        if action.action_type is ActionType.GO:
            route = action.payload.get("route") or [person.location_id, action.target]
            origin = route[0]
            person.location_id = action.target
            return [
                Event(
                    event_type=EventType.ACTION_COMPLETED,
                    timestamp=now,
                    message=(
                        f"{person.name} completed {action.label} "
                        f"via {' -> '.join(route)}"
                    ),
                    actor_id=person.id,
                    target_ids=[person.id],
                    payload={
                        "action_type": action.action_type,
                        "label": action.label,
                        "origin_location_id": origin,
                        "target_location_id": action.target,
                        "route": list(route),
                    },
                )
            ]

        if action.action_type is ActionType.USE:
            tool = action.payload.get("tool")
            if not tool:
                return [
                    Event(
                        event_type=EventType.ACTION_FAILED,
                        timestamp=now,
                        message=f"{person.name} failed {action.label} because no tool was specified",
                        actor_id=person.id,
                        target_ids=[person.id],
                        payload={"action_type": action.action_type, "reason": "missing_tool_name"},
                    )
                ]

            source_location_id = action.payload.get("source_location", person.location_id)
            source_location = self.world.location(source_location_id)
            if tool in source_location.tools:
                source_location.tools.remove(tool)
                person.inventory.append(tool)
                return [
                    Event(
                        event_type=EventType.TOOL_ACQUIRED,
                        timestamp=now,
                        message=f"{person.name} acquired {tool} from {source_location.id}",
                        actor_id=person.id,
                        target_ids=[person.id],
                        location_id=person.location_id,
                        payload={"tool": tool},
                    ),
                    Event(
                        event_type=EventType.ACTION_COMPLETED,
                        timestamp=now,
                        message=f"{person.name} completed {action.label}",
                        actor_id=person.id,
                        target_ids=[person.id],
                        payload={"action_type": action.action_type, "label": action.label},
                    ),
                ]
            return [
                Event(
                    event_type=EventType.ACTION_FAILED,
                    timestamp=now,
                    message=f"{person.name} failed {action.label} because {tool} was unavailable",
                    actor_id=person.id,
                    target_ids=[person.id],
                    payload={"action_type": action.action_type, "reason": "tool_unavailable"},
                )
            ]

        if action.action_type is ActionType.DO:
            task = self.world.tasks[action.payload["task_id"]]
            if task.required_tool and task.required_tool not in person.inventory:
                return [
                    Event(
                        event_type=EventType.ACTION_FAILED,
                        timestamp=now,
                        message=f"{person.name} failed {action.label} because {task.required_tool} is missing",
                        actor_id=person.id,
                        target_ids=[person.id],
                        payload={
                            "action_type": action.action_type,
                            "reason": "missing_tool",
                            "task_id": task.id,
                            "required_tool": task.required_tool,
                        },
                    )
                ]

            task.progress = task.target_progress
            task.completed = True
            task.active = False
            person.fatigue = min(100, person.fatigue + 10)
            return [
                Event(
                    event_type=EventType.ACTION_COMPLETED,
                    timestamp=now,
                    message=f"{person.name} completed {action.label} and finished task {task.id}",
                    actor_id=person.id,
                    target_ids=[person.id],
                    location_id=person.location_id,
                    payload={
                        "action_type": action.action_type,
                        "label": action.label,
                        "task_id": task.id,
                        "task_completed": True,
                    },
                )
            ]

        if action.action_type is ActionType.REST:
            person.fatigue = max(0, person.fatigue - 15)
            person.hunger = max(0, person.hunger - 10)
            person.emotion = "calm"
            return [
                Event(
                    event_type=EventType.ACTION_COMPLETED,
                    timestamp=now,
                    message=f"{person.name} completed {action.label}",
                    actor_id=person.id,
                    target_ids=[person.id],
                    payload={"action_type": action.action_type, "label": action.label},
                )
            ]

        return [
            Event(
                event_type=EventType.ACTION_COMPLETED,
                timestamp=now,
                message=f"{person.name} completed {action.label}",
                actor_id=person.id,
                target_ids=[person.id],
                payload={"action_type": action.action_type, "label": action.label},
            )
        ]

    def _build_trigger_reasons(
        self,
        person: Person,
        delta: ObservationDelta,
        relevant_events: list[Event],
    ) -> list[str]:
        triggers: list[str] = []
        if delta.significant:
            triggers.append(f"observation_change:{'; '.join(delta.messages)}")
        for event in relevant_events:
            if event.event_type in {
                EventType.DECISION,
                EventType.TASK_ASSIGNED,
                EventType.WEATHER_CHANGED,
                EventType.ACTION_COMPLETED,
                EventType.ACTION_FAILED,
                EventType.ACTION_INTERRUPTED,
                EventType.TOOL_ACQUIRED,
            }:
                triggers.append(f"event:{event.event_type.value}")
        if person.current_action is None and not triggers and person.last_observation is None:
            triggers.append("initial_bootstrap")
        return triggers

    def _start_action(
        self,
        person: Person,
        decision: PolicyDecision,
        observation: Observation,
        trigger_reasons: list[str],
    ) -> list[Event]:
        decision_payload = {
            "reason": decision.reason,
            "think": decision.think,
            "trigger_reasons": trigger_reasons,
            "model_input": self.memory.build_model_input(person, observation),
            "action": None
            if decision.action is None
            else {
                "action_type": decision.action.action_type.value,
                "target": decision.action.target,
                "label": decision.action.label,
                "payload": dict(decision.action.payload),
                "duration_ticks": decision.action.duration_ticks,
            },
            "policy_metadata": dict(decision.metadata),
        }
        events = [
            Event(
                event_type=EventType.DECISION,
                timestamp=self.world.current_time,
                message=(
                    f"DECISION {person.name}: triggers={trigger_reasons} think={decision.think} "
                    f"action={'null' if decision.action is None else decision.action.label} reason={decision.reason}"
                ),
                actor_id=person.id,
                target_ids=[person.id],
                payload=decision_payload,
            )
        ]

        if decision.action is None:
            return events

        invalid_reason = self._validate_action_plan(person, decision.action)
        if invalid_reason:
            events.append(
                Event(
                    event_type=EventType.ACTION_FAILED,
                    timestamp=self.world.current_time,
                    message=(
                        f"{person.name} could not start {decision.action.label} "
                        f"because {invalid_reason}"
                    ),
                    actor_id=person.id,
                    target_ids=[person.id],
                    payload={
                        "action_type": decision.action.action_type,
                        "label": decision.action.label,
                        "reason": "invalid_action_plan",
                        "detail": invalid_reason,
                        "policy_metadata": dict(decision.metadata),
                    },
                )
            )
            return events

        person.current_action = ActionInstance(
            action_type=decision.action.action_type,
            target=decision.action.target,
            total_ticks=decision.action.duration_ticks,
            remaining_ticks=decision.action.duration_ticks,
            label=decision.action.label,
            started_at=self.world.current_time,
            payload=self._build_action_payload(person, decision.action),
            interruptible=decision.action.interruptible,
        )
        events.append(
            Event(
                event_type=EventType.ACTION_STARTED,
                timestamp=self.world.current_time,
                message=f"{person.name} started {decision.action.label}",
                actor_id=person.id,
                target_ids=[person.id],
                payload={
                    "action_type": decision.action.action_type,
                    "label": decision.action.label,
                    "reason": decision.reason,
                    "policy_metadata": dict(decision.metadata),
                },
            )
        )
        return events

    def _build_action_payload(self, person: Person, action: Any) -> dict[str, Any]:
        payload = dict(action.payload)
        if action.action_type is ActionType.GO:
            payload["route"] = self.world.route_between(person.location_id, action.target)
        return payload

    def _validate_action_plan(self, person: Person, action: Any) -> str | None:
        if action.duration_ticks < 1:
            return "duration_ticks must be at least 1"

        if action.action_type is ActionType.GO:
            if action.target not in self.world.locations:
                return f"unknown location target: {action.target}"
            required_ticks = self.world.distance_in_ticks(person.location_id, action.target)
            if action.duration_ticks < required_ticks:
                return (
                    f"GO duration {action.duration_ticks} is shorter than route "
                    f"distance {required_ticks}"
                )
            return None

        if action.action_type is ActionType.DO:
            task_id = action.payload.get("task_id") or action.target
            if task_id not in self.world.tasks:
                return f"unknown task target: {task_id}"
            task = self.world.tasks[task_id]
            if task.completed:
                return f"task already completed: {task_id}"
            if person.location_id != task.location_id:
                return (
                    f"person at {person.location_id} cannot do task {task_id} "
                    f"at {task.location_id}"
                )
            return None

        if action.action_type is ActionType.USE:
            source_location_id = action.payload.get("source_location")
            if source_location_id and source_location_id not in self.world.locations:
                return f"unknown source location: {source_location_id}"
            if source_location_id and source_location_id != person.location_id:
                return (
                    f"person at {person.location_id} cannot use tool source "
                    f"at {source_location_id}"
                )
            return None

        if action.action_type is ActionType.REST and action.target:
            if action.target not in self.world.locations:
                return f"unknown rest location: {action.target}"
            return None

        return None

    def _should_interrupt(self, person: Person, relevant_events: list[Event]) -> bool:
        if person.current_action is None or not person.current_action.interruptible:
            return False
        return any(event.priority >= EventPriority.HIGH for event in relevant_events)

    def _interrupt_action(self, person: Person) -> list[Event]:
        action = person.current_action
        if action is None:
            return []
        person.current_action = None
        return [
            Event(
                event_type=EventType.ACTION_INTERRUPTED,
                timestamp=self.world.current_time,
                message=f"{person.name} interrupted {action.label}",
                actor_id=person.id,
                target_ids=[person.id],
                location_id=person.location_id,
                payload={
                    "action_type": action.action_type,
                    "label": action.label,
                    "reason": "high_priority_event",
                },
            )
        ]

    def _return_borrowed_tools(self) -> list[Event]:
        events: list[Event] = []
        warehouse = self.world.location("warehouse")
        for person in self.world.people.values():
            while "broom" in person.inventory:
                person.inventory.remove("broom")
                warehouse.tools.append("broom")
                events.append(
                    Event(
                        event_type=EventType.TOOL_RETURNED,
                        timestamp=self.world.current_time,
                        message=f"{person.name} returned broom during nightly reset",
                        actor_id=person.id,
                        target_ids=[person.id],
                        payload={"tool": "broom"},
                    )
                )
        return events

    def _event_relevant(self, person: Person, event: Event) -> bool:
        if event.actor_id == person.id:
            return True
        if person.id in event.target_ids:
            return True
        if event.location_id and event.location_id == person.location_id:
            return True
        return False

    def _should_consolidate(self, previous_time: datetime, current_time: datetime) -> bool:
        if self.world.last_consolidation_day == current_time.date():
            return False
        boundary = datetime.combine(current_time.date(), time(hour=NIGHT_CONSOLIDATION_HOUR))
        if previous_time.date() == current_time.date():
            return previous_time < boundary <= current_time
        previous_boundary = datetime.combine(previous_time.date(), time(hour=NIGHT_CONSOLIDATION_HOUR))
        return previous_time < previous_boundary or current_time >= boundary

    def _log_event(self, event: Event) -> None:
        stamp = event.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        self.logs.append(f"[{stamp}] {event.message}")
        self.event_history.append(event)

    def _record_tick_snapshot(self) -> None:
        self.tick_history.append(
            {
                "timestamp": self.world.current_time.isoformat(),
                "weather": self.world.weather.value,
                "people": {
                    person_id: {
                        "location_id": person.location_id,
                        "inventory": list(person.inventory),
                        "hunger": person.hunger,
                        "fatigue": person.fatigue,
                        "active_goal": person.working_memory.active_goal,
                        "current_intent": person.working_memory.current_intent,
                        "current_action": None
                        if person.current_action is None
                        else {
                            "label": person.current_action.label,
                            "remaining_ticks": person.current_action.remaining_ticks,
                            "target": person.current_action.target,
                        },
                        "profile_rules": dict(person.profile.learned_rules),
                        "profile_preferences": dict(person.profile.preferences),
                    }
                    for person_id, person in self.world.people.items()
                },
                "tasks": {
                    task_id: {
                        "active": task.active,
                        "completed": task.completed,
                        "progress": task.progress,
                        "location_id": task.location_id,
                    }
                    for task_id, task in self.world.tasks.items()
                },
            }
        )
