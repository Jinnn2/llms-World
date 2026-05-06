from __future__ import annotations

import sys
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from digital_human_world.models import ActionPlan, ActionType
from digital_human_world.policy import PolicyDecision
from digital_human_world.reporting import build_summary
from digital_human_world.scenario import build_demo_engine


class _InvalidTargetPolicy:
    def decide(self, person, observation, trigger_reasons, world):
        del person, observation, trigger_reasons, world
        return PolicyDecision(
            think="I will go somewhere impossible.",
            action=ActionPlan(
                action_type=ActionType.GO,
                target="missing_location",
                duration_ticks=1,
                label="GO missing_location",
            ),
            reason="test_invalid_target",
            metadata={"policy_source": "test"},
        )


class SimulationSmokeTest(unittest.TestCase):
    def test_demo_profile_and_task_outcome(self) -> None:
        engine, end_time = build_demo_engine()
        logs = engine.run_until(end_time)

        lin = engine.world.people["lin"]

        self.assertTrue(any("profile updated" in line for line in logs))
        self.assertEqual(
            lin.profile.learned_rules.get("clean_square_requires_broom"),
            "broom",
        )
        self.assertGreaterEqual(
            lin.profile.preferences.get("avoid_outdoor_in_rain", 0.0),
            1.0,
        )
        self.assertTrue(engine.world.tasks["clean_square"].completed)

    def test_validation_summary_tracks_v1_acceptance_markers(self) -> None:
        engine, end_time = build_demo_engine()
        engine.run_until(end_time)

        summary = build_summary(engine, run_metadata={"policy_mode": "heuristic"})

        self.assertTrue(summary["acceptance"]["v1_pass"])
        self.assertEqual(summary["acceptance"]["failures"], [])
        self.assertTrue(summary["behavioral_markers"]["missing_tool_failure"])
        self.assertTrue(summary["behavioral_markers"]["rain_interrupt"])
        self.assertTrue(summary["behavioral_markers"]["profile_update"])
        self.assertTrue(summary["behavioral_markers"]["learned_broom_rule"])
        self.assertTrue(summary["behavioral_markers"]["learned_rain_preference"])

    def test_invalid_action_plan_is_rejected_as_world_event(self) -> None:
        engine, _ = build_demo_engine(policy=_InvalidTargetPolicy())
        engine.step()

        self.assertIsNone(engine.world.people["lin"].current_action)
        self.assertTrue(
            any(
                event.payload.get("reason") == "invalid_action_plan"
                and event.payload.get("detail") == "unknown location target: missing_location"
                for event in engine.event_history
            )
        )


if __name__ == "__main__":
    unittest.main()
