from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from digital_human_world.reporting import write_town_artifacts
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

    print("== B4 Town Summary ==")
    print(f"b4_pass: {summary['acceptance']['b4_pass']}")
    print(f"acceptance_failures: {summary['acceptance']['failures']}")
    print(f"autonomous_people: {len(summary['autonomous_people'])}")
    print(f"tasks: {summary['tasks']}")
    print(f"person_event_counts: {summary['person_event_counts']}")
    print(f"artifacts_dir: {output_dir}")


if __name__ == "__main__":
    main()
