from __future__ import annotations

import sys
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from digital_human_world.models import EventType
from digital_human_world.reporting import build_town_summary, events_for_person
from digital_human_world.scenario import build_town_engine


class TownSimulationTest(unittest.TestCase):
    def test_town_day_completes_with_five_autonomous_people(self) -> None:
        engine, end_time = build_town_engine()
        engine.run_until(end_time)

        summary = build_town_summary(engine, run_metadata={"scenario": "town_b4"})

        self.assertTrue(summary["acceptance"]["b4_pass"])
        self.assertEqual(summary["acceptance"]["failures"], [])
        self.assertEqual(len(summary["autonomous_people"]), 5)
        self.assertTrue(all(summary["tasks"].values()))
        self.assertTrue(
            all(count > 0 for count in summary["person_event_counts"].values())
        )

    def test_people_have_separate_memory_and_event_logs(self) -> None:
        engine, end_time = build_town_engine()
        engine.run_until(end_time)

        autonomous_ids = [
            person.id for person in engine.world.people.values() if person.autonomous
        ]
        memory_ids = {
            id(engine.world.people[person_id].working_memory)
            for person_id in autonomous_ids
        }

        self.assertEqual(len(memory_ids), len(autonomous_ids))
        for person_id in autonomous_ids:
            person_events = events_for_person(engine, person_id)
            self.assertTrue(person_events)
            self.assertTrue(
                any(event.actor_id == person_id for event in person_events),
                msg=f"{person_id} never acted",
            )

    def test_town_movement_uses_declared_location_graph(self) -> None:
        engine, end_time = build_town_engine()
        engine.run_until(end_time)

        invalid_moves = []
        for event in engine.event_history:
            if event.event_type is not EventType.ACTION_COMPLETED:
                continue
            route = event.payload.get("route")
            if not route:
                continue
            for origin, target in zip(route, route[1:]):
                if target not in engine.world.location(origin).neighbors:
                    invalid_moves.append((origin, target))

        invalid_action_failures = [
            event
            for event in engine.event_history
            if event.event_type is EventType.ACTION_FAILED
            and event.payload.get("reason") == "invalid_action_plan"
        ]

        self.assertEqual(invalid_moves, [])
        self.assertEqual(invalid_action_failures, [])


if __name__ == "__main__":
    unittest.main()
