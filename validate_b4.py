from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from digital_human_world.reporting import write_town_artifacts
from digital_human_world.replay_export import write_world_view_replay
from digital_human_world.scenario import build_town_engine


def main() -> None:
    engine, end_time = build_town_engine()
    engine.run_until(end_time)

    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_dir = ROOT / "artifacts" / "town_b4" / run_id
    summary = write_town_artifacts(
        engine,
        output_dir,
        run_metadata={
            "scenario": "town_b4",
            "policy_mode": "heuristic",
            "end_time": end_time.isoformat(),
        },
    )
    replay_artifact_path = output_dir / "world_view_replay.json"
    frontend_replay_path = ROOT / "src" / "web" / "data" / "generatedTownReplay.json"
    replay_payload = write_world_view_replay(
        engine,
        replay_artifact_path,
        summary=summary,
    )
    write_world_view_replay(
        engine,
        frontend_replay_path,
        summary=summary,
    )

    print("== B4 Town Summary ==")
    print(f"b4_pass: {summary['acceptance']['b4_pass']}")
    print(f"acceptance_failures: {summary['acceptance']['failures']}")
    print(f"autonomous_people: {len(summary['autonomous_people'])}")
    print(f"tasks: {summary['tasks']}")
    print(f"person_event_counts: {summary['person_event_counts']}")
    print(f"world_view_frames: {len(replay_payload['replayFrames'])}")
    print(f"world_view_replay: {replay_artifact_path}")
    print(f"frontend_replay: {frontend_replay_path}")
    print(f"artifacts_dir: {output_dir}")


if __name__ == "__main__":
    main()
