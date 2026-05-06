from __future__ import annotations

import sys
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from digital_human_world.config import PolicyConfig
from digital_human_world.engine import Inspector
from digital_human_world.llm_policy import LLMProtoHumanPolicy, build_policy_from_config
from digital_human_world.scenario import build_demo_engine


class _FakeClient:
    def __init__(self, response_text: str) -> None:
        self.response_text = response_text

    def create_chat_completion(self, **kwargs: object) -> str:
        del kwargs
        return self.response_text


class LLMPolicyTest(unittest.TestCase):
    def test_build_policy_falls_back_without_model(self) -> None:
        policy, mode = build_policy_from_config(
            PolicyConfig(
                mode="auto",
                api_key="test-key",
                base_url="https://example.com/v1",
                model=None,
            )
        )

        self.assertEqual(mode, "heuristic_auto")
        self.assertIsNotNone(policy)

    def test_llm_policy_compiles_json_action(self) -> None:
        engine, _ = build_demo_engine()
        lin = engine.world.people["lin"]
        lin.working_memory.active_goal = "clean_square"

        observation = Inspector().capture(lin, engine.world)
        policy = LLMProtoHumanPolicy(
            client=_FakeClient(
                """
                {
                  "think": "I should go to the warehouse first.",
                  "reason": "test_go_warehouse",
                  "action": {
                    "action_type": "GO",
                    "target": "warehouse",
                    "payload": {}
                  }
                }
                """
            ),
            model="fake-model",
        )

        decision = policy.decide(lin, observation, ["event:task_assigned"], engine.world)

        self.assertEqual(decision.reason, "test_go_warehouse")
        self.assertIsNotNone(decision.action)
        self.assertEqual(decision.action.action_type.value, "GO")
        self.assertEqual(decision.action.target, "warehouse")
        self.assertGreaterEqual(decision.action.duration_ticks, 1)

    def test_llm_policy_falls_back_on_invalid_json(self) -> None:
        engine, _ = build_demo_engine()
        lin = engine.world.people["lin"]
        lin.working_memory.active_goal = "clean_square"

        observation = Inspector().capture(lin, engine.world)
        policy = LLMProtoHumanPolicy(
            client=_FakeClient("not json"),
            model="fake-model",
        )

        decision = policy.decide(lin, observation, ["event:task_assigned"], engine.world)

        self.assertTrue(decision.metadata["fallback_used"])
        self.assertEqual(decision.metadata["policy_source"], "llm_fallback")
        self.assertTrue(decision.reason.startswith("llm_fallback::"))
        self.assertIsNotNone(decision.action)


if __name__ == "__main__":
    unittest.main()
