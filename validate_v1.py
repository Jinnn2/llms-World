from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from digital_human_world.config import load_policy_config
from digital_human_world.llm_policy import build_policy_from_config
from digital_human_world.reporting import write_validation_artifacts
from digital_human_world.scenario import build_demo_engine


def main() -> None:
    config = load_policy_config(ROOT / ".env")
    policy, policy_mode = build_policy_from_config(config)
    engine, end_time = build_demo_engine(policy=policy)
    engine.run_until(end_time)

    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_dir = ROOT / "artifacts" / "validation" / run_id
    summary = write_validation_artifacts(
        engine,
        output_dir,
        run_metadata={
            "policy_mode": policy_mode,
            "model": config.model,
            "base_url": config.base_url,
            "end_time": end_time.isoformat(),
        },
    )

    print("== Validation Summary ==")
    print(f"policy_mode: {summary['run_metadata']['policy_mode']}")
    print(f"model: {summary['run_metadata']['model']}")
    print(f"v1_pass: {summary['acceptance']['v1_pass']}")
    print(f"acceptance_failures: {summary['acceptance']['failures']}")
    print(f"task_completed: {summary['outcome']['task_completed']}")
    print(f"profile_rules: {summary['outcome']['profile_rules']}")
    print(f"profile_preferences: {summary['outcome']['profile_preferences']}")
    print(f"behavioral_markers: {summary['behavioral_markers']}")
    print(f"fallback_count: {summary['decision_stats']['fallback']}")
    print(f"decision_total: {summary['decision_stats']['total']}")
    print(f"events: {summary['artifacts']['events']}")
    print(f"ticks: {summary['artifacts']['ticks']}")
    print(f"artifacts_dir: {output_dir}")


if __name__ == "__main__":
    main()
