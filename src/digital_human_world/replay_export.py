from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .engine import SimulationEngine
from .models import Event, EventType, LocationKind, Weather


_LOCATION_LAYOUT: dict[str, tuple[int, int]] = {
    "home": (15, 48),
    "farm_house": (17, 70),
    "craft_house": (18, 28),
    "cottage": (55, 78),
    "lodge": (74, 16),
    "road": (38, 48),
    "warehouse": (36, 18),
    "square": (63, 48),
    "workshop": (84, 27),
    "field": (82, 74),
    "grove": (90, 54),
}


def write_world_view_replay(
    engine: SimulationEngine,
    path: str | Path,
    *,
    summary: dict[str, Any],
) -> dict[str, Any]:
    payload = build_world_view_replay(engine, summary=summary)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return payload


def build_world_view_replay(
    engine: SimulationEngine,
    *,
    summary: dict[str, Any],
) -> dict[str, Any]:
    frames = _build_replay_frames(engine)
    return {
        "schemaVersion": 1,
        "source": "digital_human_world.validation",
        "generatedAt": datetime.now().isoformat(timespec="seconds"),
        "runMetadata": _public_run_metadata(summary.get("run_metadata", {})),
        "acceptance": summary.get("acceptance", {}),
        "locations": _build_locations(engine),
        "links": _build_links(engine),
        "people": _build_people(engine),
        "replayFrames": frames,
        "metrics": _build_metrics(summary, frames),
    }


def _public_run_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    return {
        "policy_mode": metadata.get("policy_mode"),
        "model": metadata.get("model"),
        "end_time": metadata.get("end_time"),
    }


def _build_locations(engine: SimulationEngine) -> list[dict[str, Any]]:
    locations = []
    for location_id, location in engine.world.locations.items():
        x, y = _LOCATION_LAYOUT.get(location_id, (50, 50))
        locations.append(
            {
                "id": location.id,
                "name": location.name,
                "kind": location.kind.value,
                "x": x,
                "y": y,
            }
        )
    return locations


def _build_links(engine: SimulationEngine) -> list[list[str]]:
    seen: set[tuple[str, str]] = set()
    links: list[list[str]] = []
    for location_id, location in engine.world.locations.items():
        for neighbor_id in location.neighbors:
            edge = tuple(sorted((location_id, neighbor_id)))
            if edge in seen:
                continue
            seen.add(edge)
            links.append([edge[0], edge[1]])
    return links


def _build_people(engine: SimulationEngine) -> list[dict[str, Any]]:
    return [
        {
            "id": person.id,
            "name": person.name,
            "homeId": person.home_id,
            "autonomous": person.autonomous,
            "traits": list(person.profile.stable_traits),
        }
        for person in engine.world.people.values()
        if person.autonomous
    ]


def _build_replay_frames(engine: SimulationEngine) -> list[dict[str, Any]]:
    if not engine.event_history:
        return []

    first_day = engine.event_history[0].timestamp.date()
    tick_by_timestamp = {
        tick["timestamp"]: tick for tick in engine.tick_history
    }

    frames = []
    previous_rest_reason_by_person: dict[str, str | None] = {}

    for event in engine.event_history:
        if not _should_include_event(event):
            continue

        tick = tick_by_timestamp.get(event.timestamp.isoformat())
        focus_person_id = _focus_person_id(engine, event)
        if _is_repeated_rest_decision(
            event,
            previous_rest_reason_by_person.get(focus_person_id),
        ):
            continue

        people_state = _people_state(engine, tick)
        person_state = people_state.get(focus_person_id, _person_state(tick))
        frame = _frame_from_event(event, person_state, people_state, focus_person_id, first_day)
        frames.append(frame)

        if event.event_type is EventType.DECISION and frame["action"].startswith("REST"):
            previous_rest_reason_by_person[focus_person_id] = event.payload.get("reason")
        elif event.event_type is not EventType.ACTION_COMPLETED:
            previous_rest_reason_by_person[focus_person_id] = None

    _apply_frame_durations(frames)
    return frames


def _should_include_event(event: Event) -> bool:
    if event.event_type in {
        EventType.TASK_ASSIGNED,
        EventType.DECISION,
        EventType.ACTION_FAILED,
        EventType.ACTION_INTERRUPTED,
        EventType.TOOL_ACQUIRED,
        EventType.WEATHER_CHANGED,
        EventType.PROFILE_UPDATED,
        EventType.TOOL_RETURNED,
    }:
        return True
    if event.event_type is EventType.ACTION_COMPLETED:
        return bool(event.payload.get("task_completed"))
    return False


def _is_repeated_rest_decision(
    event: Event,
    previous_rest_reason: str | None,
) -> bool:
    if event.event_type is not EventType.DECISION:
        return False
    action = event.payload.get("action") or {}
    if not isinstance(action, dict):
        return False
    label = str(action.get("label") or "")
    if not label.startswith("REST"):
        return False
    return previous_rest_reason == event.payload.get("reason")


def _focus_person_id(engine: SimulationEngine, event: Event) -> str:
    if event.actor_id and event.actor_id in engine.world.people:
        if engine.world.people[event.actor_id].autonomous:
            return event.actor_id
    for target_id in event.target_ids:
        if target_id in engine.world.people and engine.world.people[target_id].autonomous:
            return target_id
    for person in engine.world.people.values():
        if person.autonomous:
            return person.id
    return "lin"


def _person_state(tick: dict[str, Any] | None, person_id: str = "lin") -> dict[str, Any]:
    if tick is None:
        return {}
    state = dict(tick.get("people", {}).get(person_id, {}))
    state["weather"] = tick.get("weather")
    return state


def _people_state(engine: SimulationEngine, tick: dict[str, Any] | None) -> dict[str, Any]:
    states: dict[str, Any] = {}
    for person in engine.world.people.values():
        if not person.autonomous:
            continue
        state = _person_state(tick, person.id)
        current_action = state.get("current_action") or {}
        states[person.id] = {
            "id": person.id,
            "name": person.name,
            "locationId": state.get("location_id") or person.location_id,
            "homeId": person.home_id,
            "action": current_action.get("label") or "IDLE",
            "activeGoal": state.get("active_goal"),
            "intent": state.get("current_intent") or current_action.get("label") or "Idle",
            "inventory": list(state.get("inventory") or []),
            "hunger": state.get("hunger", person.hunger),
            "fatigue": state.get("fatigue", person.fatigue),
            "profileRules": sorted((state.get("profile_rules") or {}).keys()),
            "profilePreferences": sorted((state.get("profile_preferences") or {}).keys()),
        }
    return states


def _frame_from_event(
    event: Event,
    person_state: dict[str, Any],
    people_state: dict[str, Any],
    focus_person_id: str,
    first_day: datetime.date,
) -> dict[str, Any]:
    timestamp = event.timestamp
    current_action = person_state.get("current_action") or {}
    action_from_decision = event.payload.get("action") or {}
    action = (
        current_action.get("label")
        or action_from_decision.get("label")
        or event.payload.get("label")
        or _fallback_action_label(event)
    )
    location_id = person_state.get("location_id") or event.location_id or "home"
    profile_rules = sorted((person_state.get("profile_rules") or {}).keys())
    profile_preferences = sorted((person_state.get("profile_preferences") or {}).keys())

    return {
        "time": _format_time_label(timestamp, first_day),
        "timestamp": timestamp.isoformat(),
        "day": (timestamp.date() - first_day).days + 1,
        "weather": _weather_value(event, person_state),
        "focusPersonId": focus_person_id,
        "people": _people_for_frame(event, people_state, focus_person_id, action),
        "locationId": location_id,
        "action": action,
        "activeGoal": person_state.get("active_goal"),
        "intent": _intent_for_event(event),
        "inventory": list(person_state.get("inventory") or []),
        "profileRules": profile_rules,
        "profilePreferences": profile_preferences,
        "workingNotes": _notes_for_event(event),
        "eventType": _event_type_for_frontend(event),
        "event": _event_text(event),
        "sourceEventType": event.event_type.value,
    }


def _people_for_frame(
    event: Event,
    people_state: dict[str, Any],
    focus_person_id: str,
    focus_action: str,
) -> dict[str, Any]:
    people = {person_id: dict(state) for person_id, state in people_state.items()}
    if focus_person_id in people:
        people[focus_person_id]["action"] = focus_action
        people[focus_person_id]["intent"] = _intent_for_event(event)
    return people


def _format_time_label(timestamp: datetime, first_day: datetime.date) -> str:
    day = (timestamp.date() - first_day).days + 1
    clock = timestamp.strftime("%H:%M:%S")
    if timestamp.hour >= 21:
        return f"Night {clock}"
    return f"Day {day} {clock}"


def _weather_value(event: Event, person_state: dict[str, Any]) -> str:
    payload_weather = event.payload.get("weather")
    if payload_weather:
        return str(payload_weather)
    state_weather = person_state.get("weather")
    if state_weather:
        return str(state_weather)
    if "rain" in event.message.lower():
        return Weather.RAIN.value
    return Weather.CLEAR.value


def _fallback_action_label(event: Event) -> str:
    if event.event_type is EventType.DECISION:
        return "IDLE"
    if event.event_type is EventType.PROFILE_UPDATED:
        return "CONSOLIDATE"
    return event.event_type.value.upper()


def _intent_for_event(event: Event) -> str:
    if event.event_type is EventType.DECISION:
        return str(event.payload.get("think") or event.payload.get("reason") or "Choose next action")
    if event.event_type is EventType.PROFILE_UPDATED:
        return "Night profile update"
    if event.event_type is EventType.ACTION_FAILED:
        return "Handle failed action"
    if event.event_type is EventType.ACTION_INTERRUPTED:
        return "Respond to interruption"
    if event.event_type is EventType.WEATHER_CHANGED:
        return "Observe weather change"
    if event.event_type is EventType.TOOL_ACQUIRED:
        return "Update inventory"
    if event.event_type is EventType.TASK_ASSIGNED:
        return "Receive assigned goal"
    return "Update world state"


def _notes_for_event(event: Event) -> list[str]:
    notes: list[str] = []
    if event.event_type is EventType.DECISION:
        reason = event.payload.get("reason")
        if reason:
            notes.append(f"reason: {reason}")
        for trigger in event.payload.get("trigger_reasons", [])[:3]:
            notes.append(str(trigger))
    elif event.event_type is EventType.PROFILE_UPDATED:
        notes.extend(str(change) for change in event.payload.get("changes", []))
    elif event.event_type is EventType.ACTION_FAILED:
        reason = event.payload.get("reason")
        if reason:
            notes.append(f"failure: {reason}")
        required_tool = event.payload.get("required_tool")
        if required_tool:
            notes.append(f"required_tool: {required_tool}")
    elif event.event_type is EventType.WEATHER_CHANGED:
        notes.append(f"weather: {event.payload.get('weather', 'changed')}")
        if event.payload.get("outdoor_exposure"):
            notes.append("outdoor exposure")
    elif event.event_type is EventType.TOOL_ACQUIRED:
        notes.append(f"tool: {event.payload.get('tool')}")
    elif event.event_type is EventType.TASK_ASSIGNED:
        notes.append(f"task: {event.payload.get('task_id')}")

    if not notes:
        notes.append(event.message)
    return notes


def _event_type_for_frontend(event: Event) -> str:
    if event.event_type is EventType.TASK_ASSIGNED:
        return "task"
    if event.event_type is EventType.DECISION:
        return "decision"
    if event.event_type is EventType.ACTION_FAILED:
        return "failure"
    if event.event_type is EventType.ACTION_INTERRUPTED:
        return "interrupt"
    if event.event_type is EventType.TOOL_ACQUIRED:
        return "tool"
    if event.event_type is EventType.WEATHER_CHANGED:
        return "weather"
    if event.event_type is EventType.PROFILE_UPDATED:
        return "memory"
    if event.event_type is EventType.ACTION_COMPLETED:
        return "complete"
    return "action"


def _event_text(event: Event) -> str:
    if event.event_type is EventType.DECISION:
        action = event.payload.get("action")
        action_label = "idle"
        if isinstance(action, dict):
            action_label = str(action.get("label") or action.get("action_type") or "action")
        return f"{event.payload.get('think', 'Decision made')} -> {action_label}"
    return event.message


def _apply_frame_durations(frames: list[dict[str, Any]]) -> None:
    for index, frame in enumerate(frames):
        if index == len(frames) - 1:
            frame["durationMs"] = 1800
            continue
        start = datetime.fromisoformat(frame["timestamp"])
        end = datetime.fromisoformat(frames[index + 1]["timestamp"])
        delta_seconds = max(1.0, (end - start).total_seconds())
        frame["durationMs"] = int(max(900, min(4200, delta_seconds * 45)))


def _build_metrics(summary: dict[str, Any], frames: list[dict[str, Any]]) -> list[dict[str, str]]:
    acceptance = summary.get("acceptance", {})
    pass_value = acceptance.get("b4_pass", acceptance.get("v1_pass"))
    pass_label = "B4 acceptance" if "b4_pass" in acceptance else "V1 acceptance"
    return [
        {
            "label": pass_label,
            "value": "PASS" if pass_value else "FAIL",
            "tone": "green" if pass_value else "red",
        },
        {
            "label": "Replay frames",
            "value": str(len(frames)),
            "tone": "indigo",
        },
        {
            "label": "Policy",
            "value": str(summary.get("run_metadata", {}).get("policy_mode", "unknown")),
            "tone": "teal",
        },
        {
            "label": "Decisions",
            "value": str(summary.get("decision_stats", {}).get("total", 0)),
            "tone": "amber",
        },
    ]
