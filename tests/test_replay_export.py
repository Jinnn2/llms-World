from __future__ import annotations

import sys
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from digital_human_world.replay_export import build_world_view_replay
from digital_human_world.reporting import build_summary
from digital_human_world.scenario import build_demo_engine


class WorldViewReplayExportTest(unittest.TestCase):
    def test_replay_export_uses_simulation_state(self) -> None:
        engine, end_time = build_demo_engine()
        engine.run_until(end_time)
        summary = build_summary(engine, run_metadata={"policy_mode": "heuristic"})

        payload = build_world_view_replay(engine, summary=summary)

        location_ids = {location["id"] for location in payload["locations"]}
        frame_location_ids = {frame["locationId"] for frame in payload["replayFrames"]}
        frame_types = {frame["eventType"] for frame in payload["replayFrames"]}

        self.assertEqual(payload["schemaVersion"], 1)
        self.assertEqual(payload["acceptance"]["v1_pass"], True)
        self.assertIn(["road", "square"], payload["links"])
        self.assertTrue(frame_location_ids.issubset(location_ids))
        self.assertIn("failure", frame_types)
        self.assertIn("interrupt", frame_types)
        self.assertIn("memory", frame_types)
        self.assertTrue(all(frame["durationMs"] >= 900 for frame in payload["replayFrames"]))

    def test_public_replay_metadata_does_not_export_base_url(self) -> None:
        engine, end_time = build_demo_engine()
        engine.run_until(end_time)
        summary = build_summary(
            engine,
            run_metadata={
                "policy_mode": "heuristic",
                "configured_model": "local-model",
                "base_url": "https://example.invalid/v1",
                "end_time": end_time.isoformat(),
            },
        )

        payload = build_world_view_replay(engine, summary=summary)

        self.assertEqual(
            set(payload["runMetadata"].keys()),
            {"policy_mode", "model", "end_time"},
        )
        self.assertNotIn("base_url", payload["runMetadata"])
        self.assertNotIn("configured_model", payload["runMetadata"])


if __name__ == "__main__":
    unittest.main()
