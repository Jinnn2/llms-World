from __future__ import annotations

import sys
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from digital_human_world.scenario import build_demo_engine


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


if __name__ == "__main__":
    unittest.main()
