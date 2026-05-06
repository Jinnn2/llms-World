from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from .engine import SimulationEngine
from .models import Event, EventType


def write_validation_artifacts(
    engine: SimulationEngine,
    output_dir: str | Path,
    *,
    run_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    events_path = target_dir / "events.jsonl"
    ticks_path = target_dir / "ticks.jsonl"
    text_log_path = target_dir / "events.log"
    summary_path = target_dir / "summary.json"

    _write_events_jsonl(events_path, engine.event_history)
    _write_jsonl(ticks_path, engine.tick_history)
    text_log_path.write_text("\n".join(engine.logs) + "\n", encoding="utf-8")

    summary = build_summary(engine, run_metadata=run_metadata or {})
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return summary


def build_summary(
    engine: SimulationEngine,
    *,
    run_metadata: dict[str, Any],
) -> dict[str, Any]:
    counts = Counter(event.event_type.value for event in engine.event_history)
    decision_events = [
        event for event in engine.event_history if event.event_type is EventType.DECISION
    ]
    fallback_count = sum(
        1
        for event in decision_events
        if event.payload.get("policy_metadata", {}).get("fallback_used")
    )

    llm_count = sum(
        1
        for event in decision_events
        if event.payload.get("policy_metadata", {}).get("policy_source") == "llm"
    )
    heur_count = sum(
        1
        for event in decision_events
        if event.payload.get("policy_metadata", {}).get("policy_source") == "heuristic"
    )

    lin = engine.world.people["lin"]
    clean_task = engine.world.tasks["clean_square"]
    learned_broom_rule = (
        lin.profile.learned_rules.get("clean_square_requires_broom") == "broom"
    )
    learned_rain_preference = (
        lin.profile.preferences.get("avoid_outdoor_in_rain", 0.0) >= 1.0
    )
    missing_tool_failure = any(
        event.event_type is EventType.ACTION_FAILED
        and event.payload.get("reason") == "missing_tool"
        and event.payload.get("task_id") == "clean_square"
        for event in engine.event_history
    )
    rain_interrupt = any(
        event.event_type is EventType.ACTION_INTERRUPTED
        and event.payload.get("reason") == "high_priority_event"
        for event in engine.event_history
    )
    profile_update = any(
        event.event_type is EventType.PROFILE_UPDATED for event in engine.event_history
    )
    accepted = (
        clean_task.completed
        and learned_broom_rule
        and learned_rain_preference
        and missing_tool_failure
        and rain_interrupt
        and profile_update
    )
    failures = []
    if not clean_task.completed:
        failures.append("clean_square_not_completed")
    if not learned_broom_rule:
        failures.append("broom_rule_not_consolidated")
    if not learned_rain_preference:
        failures.append("rain_preference_not_consolidated")
    if not missing_tool_failure:
        failures.append("missing_tool_experience_absent")
    if not rain_interrupt:
        failures.append("rain_interrupt_absent")
    if not profile_update:
        failures.append("profile_update_absent")

    return {
        "run_metadata": run_metadata,
        "event_counts": dict(counts),
        "decision_stats": {
            "total": len(decision_events),
            "llm": llm_count,
            "heuristic": heur_count,
            "fallback": fallback_count,
        },
        "outcome": {
            "task_completed": clean_task.completed,
            "final_location": lin.location_id,
            "inventory": list(lin.inventory),
            "profile_rules": dict(lin.profile.learned_rules),
            "profile_preferences": dict(lin.profile.preferences),
        },
        "behavioral_markers": {
            "missing_tool_failure": missing_tool_failure,
            "rain_interrupt": rain_interrupt,
            "profile_update": profile_update,
            "learned_broom_rule": learned_broom_rule,
            "learned_rain_preference": learned_rain_preference,
        },
        "acceptance": {
            "v1_pass": accepted,
            "failures": failures,
        },
        "artifacts": {
            "ticks": len(engine.tick_history),
            "events": len(engine.event_history),
        },
    }


def _write_events_jsonl(path: Path, events: list[Event]) -> None:
    records = []
    for event in events:
        records.append(
            {
                "timestamp": event.timestamp.isoformat(),
                "event_type": event.event_type.value,
                "message": event.message,
                "priority": int(event.priority),
                "actor_id": event.actor_id,
                "target_ids": event.target_ids,
                "location_id": event.location_id,
                "payload": _make_json_safe(event.payload),
            }
        )
    _write_jsonl(path, records)


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(_make_json_safe(row), ensure_ascii=False) + "\n")


def _make_json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _make_json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_make_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_make_json_safe(item) for item in value]
    if hasattr(value, "value"):
        return _make_json_safe(value.value)
    return value
