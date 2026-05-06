from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from digital_human_world.config import load_policy_config
from digital_human_world.llm_policy import build_policy_from_config
from digital_human_world.scenario import build_demo_engine


def main() -> None:
    config = load_policy_config(ROOT / ".env")
    policy, policy_mode = build_policy_from_config(config)
    engine, end_time = build_demo_engine(policy=policy)
    logs = engine.run_until(end_time)

    print("== Digital Human World v1 demo ==")
    print(f"policy_mode: {policy_mode}")
    for line in logs:
        print(line)

    lin = engine.world.people["lin"]
    print("\n== Final profile ==")
    print(f"rules: {lin.profile.learned_rules}")
    print(f"preferences: {lin.profile.preferences}")
    print(f"inventory: {lin.inventory}")
    print(f"location: {lin.location_id}")
    print(f"task completed: {engine.world.tasks['clean_square'].completed}")


if __name__ == "__main__":
    main()
