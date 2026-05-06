from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from .models import ActionPlan, ActionType, Observation, Person, Weather, WorldState


@dataclass(slots=True)
class PolicyDecision:
    think: str
    action: ActionPlan | None
    reason: str
    metadata: dict[str, Any] = field(default_factory=dict)


class DecisionPolicy(Protocol):
    def decide(
        self,
        person: Person,
        observation: Observation,
        trigger_reasons: list[str],
        world: WorldState,
    ) -> PolicyDecision: ...


class HeuristicProtoHumanPolicy:
    """A deterministic stand-in for the future compact neural model."""

    def decide(
        self,
        person: Person,
        observation: Observation,
        trigger_reasons: list[str],
        world: WorldState,
    ) -> PolicyDecision:
        del trigger_reasons

        goal = person.working_memory.active_goal
        recent_text = " | ".join(
            list(person.working_memory.recent_events) + list(person.working_memory.recent_outcomes)
        )
        knows_broom_rule = (
            person.profile.learned_rules.get("clean_square_requires_broom") == "broom"
        )
        avoid_rain = person.profile.preferences.get("avoid_outdoor_in_rain", 0.0) >= 0.5
        recent_missing_broom = "broom is missing" in recent_text
        recent_rain_exposure = "Rain started" in recent_text
        knows_broom_now = knows_broom_rule or recent_missing_broom
        has_broom = "broom" in person.inventory
        at_home = person.location_id == person.home_id
        at_square = person.location_id == "square"
        at_warehouse = person.location_id == "warehouse"

        if observation.weather == Weather.RAIN:
            if world.is_outdoors(person):
                return PolicyDecision(
                    think="Rain started while I am outside. I should go home.",
                    action=self._go(world, person, person.home_id),
                    reason="high_priority_weather",
                    metadata={"policy_source": "heuristic"},
                )
            if at_home and goal == "clean_square":
                if avoid_rain:
                    reason = "profile_prefers_shelter_in_rain"
                elif recent_rain_exposure:
                    reason = "working_memory_remembers_rain_exposure"
                else:
                    reason = "observation_says_it_is_raining"
                return PolicyDecision(
                    think="It is raining. I should wait indoors until the weather clears.",
                    action=ActionPlan(
                        action_type=ActionType.REST,
                        target="home",
                        duration_ticks=3,
                        label="REST at home while rain passes",
                        interruptible=True,
                    ),
                    reason=reason,
                    metadata={"policy_source": "heuristic"},
                )

        if goal == "clean_square":
            task = world.tasks["clean_square"]
            if task.completed:
                person.working_memory.active_goal = None
                if not at_home:
                    return PolicyDecision(
                        think="The task is complete. I can head home.",
                        action=self._go(world, person, person.home_id),
                        reason="task_completed_go_home",
                        metadata={"policy_source": "heuristic"},
                    )
                return PolicyDecision(
                    think="The square is already clean.",
                    action=ActionPlan(
                        action_type=ActionType.REST,
                        target="home",
                        duration_ticks=2,
                        label="REST after finished work",
                    ),
                    reason="task_already_done",
                    metadata={"policy_source": "heuristic"},
                )

            if has_broom and at_square and observation.weather == Weather.CLEAR:
                return PolicyDecision(
                    think="I have the broom and I am at the square. I should clean it now.",
                    action=ActionPlan(
                        action_type=ActionType.DO,
                        target="clean_square",
                        duration_ticks=6,
                        label="DO clean_square",
                        payload={"task_id": "clean_square"},
                    ),
                    reason="perform_cleaning",
                    metadata={"policy_source": "heuristic"},
                )

            if has_broom and not at_square:
                return PolicyDecision(
                    think="I already have the broom. I should go to the square.",
                    action=self._go(world, person, "square"),
                    reason="carry_tool_to_task_site",
                    metadata={"policy_source": "heuristic"},
                )

            if at_warehouse and "broom" in observation.visible_tools:
                return PolicyDecision(
                    think="The broom is here. I should pick it up.",
                    action=ActionPlan(
                        action_type=ActionType.USE,
                        target="broom_rack",
                        duration_ticks=1,
                        label="USE broom_rack",
                        payload={"tool": "broom", "source_location": "warehouse"},
                    ),
                    reason="pick_up_required_tool",
                    metadata={"policy_source": "heuristic"},
                )

            if knows_broom_now and not has_broom:
                return PolicyDecision(
                    think="Cleaning the square requires a broom. I should get one first.",
                    action=self._go(world, person, "warehouse"),
                    reason="working_or_long_term_memory_knows_required_tool",
                    metadata={"policy_source": "heuristic"},
                )

            if at_square and not has_broom:
                return PolicyDecision(
                    think="I should try cleaning the square now.",
                    action=ActionPlan(
                        action_type=ActionType.DO,
                        target="clean_square",
                        duration_ticks=1,
                        label="DO clean_square without tool",
                        payload={"task_id": "clean_square"},
                    ),
                    reason="attempt_task_without_rule",
                    metadata={"policy_source": "heuristic"},
                )

            return PolicyDecision(
                think="I have a cleaning goal. I should inspect the square first.",
                action=self._go(world, person, "square"),
                reason="inspect_task_site_first",
                metadata={"policy_source": "heuristic"},
            )

        if not at_home:
            return PolicyDecision(
                think="I have no active goal. I should go home.",
                action=self._go(world, person, person.home_id),
                reason="return_home_when_idle",
                metadata={"policy_source": "heuristic"},
            )

        return PolicyDecision(
            think="Nothing urgent is happening. I can stay idle until something changes.",
            action=None,
            reason="idle_no_action",
            metadata={"policy_source": "heuristic"},
        )

    def _go(self, world: WorldState, person: Person, target_location: str) -> ActionPlan:
        return ActionPlan(
            action_type=ActionType.GO,
            target=target_location,
            duration_ticks=world.distance_in_ticks(person.location_id, target_location),
            label=f"GO {target_location}",
            interruptible=True,
        )
