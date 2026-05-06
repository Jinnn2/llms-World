from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Protocol

from .config import PolicyConfig
from .models import ActionPlan, ActionType, Observation, Person, Weather, WorldState
from .policy import DecisionPolicy, HeuristicProtoHumanPolicy, PolicyDecision


class ChatClient(Protocol):
    def create_chat_completion(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        temperature: float | None,
        max_tokens: int,
        timeout_seconds: int,
    ) -> str: ...


@dataclass(slots=True)
class OpenAICompatibleChatClient:
    api_key: str
    base_url: str
    max_retries: int = 2

    def create_chat_completion(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        temperature: float | None,
        max_tokens: int,
        timeout_seconds: int,
    ) -> str:
        body = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
        }
        if temperature is not None:
            body["temperature"] = temperature
        payload = json.dumps(body).encode("utf-8")
        request = urllib.request.Request(
            url=f"{self.base_url}/chat/completions",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )

        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                    response_body = response.read().decode("utf-8")
                break
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="replace")
                last_error = RuntimeError(f"HTTP {exc.code}: {detail}")
                if 500 <= exc.code < 600 and attempt < self.max_retries:
                    time.sleep(0.4 * (attempt + 1))
                    continue
                raise last_error from exc
            except urllib.error.URLError as exc:
                last_error = RuntimeError(f"network error: {exc.reason}")
                if attempt < self.max_retries:
                    time.sleep(0.4 * (attempt + 1))
                    continue
                raise last_error from exc
        else:
            raise RuntimeError(f"request failed after retries: {last_error}")

        data = json.loads(response_body)
        return data["choices"][0]["message"]["content"]


class LLMProtoHumanPolicy:
    def __init__(
        self,
        *,
        client: ChatClient,
        model: str,
        temperature: float | None = None,
        max_tokens: int = 180,
        timeout_seconds: int = 30,
        fallback_policy: DecisionPolicy | None = None,
    ) -> None:
        self.client = client
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout_seconds = timeout_seconds
        self.fallback_policy = fallback_policy or HeuristicProtoHumanPolicy()

    def decide(
        self,
        person: Person,
        observation: Observation,
        trigger_reasons: list[str],
        world: WorldState,
    ) -> PolicyDecision:
        messages = self._build_messages(person, observation, trigger_reasons, world)
        try:
            content = self.client.create_chat_completion(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                timeout_seconds=self.timeout_seconds,
            )
            parsed = self._parse_json_object(content)
            return self._compile_decision(
                parsed,
                person,
                observation,
                world,
                metadata={
                    "policy_source": "llm",
                    "model": self.model,
                    "prompt_messages": messages,
                    "raw_response": content,
                    "parsed_response": parsed,
                    "fallback_used": False,
                },
            )
        except Exception as exc:
            fallback = self.fallback_policy.decide(person, observation, trigger_reasons, world)
            return PolicyDecision(
                think=f"{fallback.think} [llm_fallback: {exc}]",
                action=fallback.action,
                reason=f"llm_fallback::{fallback.reason}",
                metadata={
                    **fallback.metadata,
                    "policy_source": "llm_fallback",
                    "model": self.model,
                    "fallback_used": True,
                    "fallback_error": str(exc),
                    "prompt_messages": messages,
                },
            )

    def _build_messages(
        self,
        person: Person,
        observation: Observation,
        trigger_reasons: list[str],
        world: WorldState,
    ) -> list[dict[str, str]]:
        task_ids = sorted(world.tasks.keys())
        location_ids = sorted(world.locations.keys())
        inventory = list(person.inventory)
        wm = person.working_memory
        profile = person.profile

        system_prompt = (
            "You are not a chatbot. You are the next-action policy for one digital human in a persistent world.\n"
            "Choose exactly one next action that best advances the current goal under the trigger reasons.\n"
            "Return raw JSON only. No markdown, no code fences, no explanation outside the JSON object.\n"
            "The JSON keys must be: think, reason, action.\n"
            "think: one short sentence, under 20 words.\n"
            "reason: short snake_case.\n"
            "action: null or an object with keys action_type, target, payload.\n"
            "Allowed action_type values: GO, DO, USE, SPEAK, REST, LEARN.\n"
            "Use only provided ids for locations and tasks.\n"
            "Never invent world facts, tools, tasks, locations, or neighbors.\n"
            "If recent outcomes show an action failed for a missing tool, do not repeat that DO action. Get the tool first.\n"
            "If it is raining and the person is outdoors, prefer GO home immediately.\n"
            "If it is raining and the person is indoors with an outdoor goal, prefer REST or null until conditions change.\n"
            "Choose the smallest action that safely advances the goal."
        )

        user_prompt = json.dumps(
            {
                "time": world.current_time.isoformat(),
                "trigger_reasons": trigger_reasons,
                "current_location_id": person.location_id,
                "home_id": person.home_id,
                "weather": observation.weather,
                "visible_tools": observation.visible_tools,
                "visible_tasks": observation.visible_tasks,
                "inventory": inventory,
                "observation_text": observation.text,
                "locations": {
                    location_id: {
                        "kind": location.kind,
                        "neighbors": location.neighbors,
                    }
                    for location_id, location in world.locations.items()
                },
                "tasks": {
                    task_id: {
                        "name": task.name,
                        "location_id": task.location_id,
                        "required_tool": task.required_tool,
                        "active": task.active,
                        "completed": task.completed,
                    }
                    for task_id, task in world.tasks.items()
                },
                "working_memory": {
                    "active_goal": wm.active_goal,
                    "current_intent": wm.current_intent,
                    "recent_observation_changes": list(wm.recent_observation_changes),
                    "recent_events": list(wm.recent_events),
                    "recent_outcomes": list(wm.recent_outcomes),
                },
                "profile": {
                    "learned_rules": profile.learned_rules,
                    "preferences": profile.preferences,
                    "skills": profile.skills,
                    "structured_skills": self._build_structured_skills(profile.skills),
                    "habits": profile.habits,
                },
                "available_location_ids": location_ids,
                "available_task_ids": task_ids,
                "action_schema": {
                    "GO": {"target": "location_id", "payload": {}},
                    "DO": {"target": "task_id_or_label", "payload": {"task_id": "task_id"}},
                    "USE": {"target": "tool_source_or_object", "payload": {"tool": "tool_name"}},
                    "SPEAK": {"target": "optional_listener_or_place", "payload": {"text": "utterance"}},
                    "REST": {"target": "location_id", "payload": {"duration_ticks": 3}},
                    "LEARN": {"target": "learning_topic", "payload": {}},
                },
                "guidance": {
                    "rain_rule": (
                        "If it is raining and the person is outdoors, prefer GO home. "
                        "If it is raining and the person is indoors with a non-urgent goal, REST is valid."
                    ),
                    "tool_rule": (
                        "If a task needs a tool and the person does not carry it, acquire the tool first."
                    ),
                    "repeat_failure_rule": (
                        "If recent outcomes mention the same failure reason, avoid repeating the same failed action."
                    ),
                    "structured_skill_rule": (
                        "Treat skills as structured state. Use skill names and levels to judge whether a direct action is appropriate, "
                        "whether a tool should be acquired first, or whether a safer preparatory step is better."
                    ),
                },
                "response_examples": [
                    {
                        "think": "I should go to the square first.",
                        "reason": "inspect_task_site_first",
                        "action": {"action_type": "GO", "target": "square", "payload": {}},
                    },
                    {
                        "think": "It is raining, so I will wait indoors.",
                        "reason": "wait_for_clear_weather",
                        "action": {"action_type": "REST", "target": "home", "payload": {"duration_ticks": 3}},
                    },
                    {
                        "think": "Nothing changed that requires action.",
                        "reason": "idle_no_action",
                        "action": None,
                    },
                    {
                        "think": "Cleaning failed because I need the broom first.",
                        "reason": "get_required_tool_after_failure",
                        "action": {"action_type": "GO", "target": "warehouse", "payload": {}},
                    },
                ],
            },
            ensure_ascii=True,
        )

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def _parse_json_object(self, content: str) -> dict[str, Any]:
        stripped = content.strip()
        if stripped.startswith("```"):
            stripped = stripped.strip("`")
            if stripped.startswith("json"):
                stripped = stripped[4:].strip()

        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            start = stripped.find("{")
            end = stripped.rfind("}")
            if start == -1 or end == -1 or end <= start:
                raise ValueError(f"model did not return JSON: {content!r}")
            return json.loads(stripped[start : end + 1])

    def _compile_decision(
        self,
        raw: dict[str, Any],
        person: Person,
        observation: Observation,
        world: WorldState,
        metadata: dict[str, Any] | None = None,
    ) -> PolicyDecision:
        think = str(raw.get("think") or "").strip() or "No explicit thought."
        reason = str(raw.get("reason") or "llm_policy").strip()
        action_payload = raw.get("action")
        if action_payload in (None, "null"):
            return PolicyDecision(
                think=think,
                action=None,
                reason=reason,
                metadata=metadata or {"policy_source": "llm"},
            )
        if not isinstance(action_payload, dict):
            raise ValueError(f"invalid action payload: {action_payload!r}")

        action_type = ActionType(str(action_payload["action_type"]).upper())
        target = str(action_payload.get("target") or "").strip()
        payload = action_payload.get("payload") or {}
        if not isinstance(payload, dict):
            raise ValueError("action payload.payload must be an object")

        duration_ticks = self._duration_for_action(
            action_type=action_type,
            target=target,
            payload=payload,
            person=person,
            observation=observation,
            world=world,
        )
        label = self._label_for_action(action_type, target)
        return PolicyDecision(
            think=think,
            action=ActionPlan(
                action_type=action_type,
                target=target,
                duration_ticks=duration_ticks,
                label=label,
                payload=payload,
                interruptible=True,
            ),
            reason=reason,
            metadata=metadata or {"policy_source": "llm"},
        )

    def _duration_for_action(
        self,
        *,
        action_type: ActionType,
        target: str,
        payload: dict[str, Any],
        person: Person,
        observation: Observation,
        world: WorldState,
    ) -> int:
        del observation
        if action_type is ActionType.GO:
            if target not in world.locations:
                raise ValueError(f"unknown GO target: {target}")
            return world.distance_in_ticks(person.location_id, target)
        if action_type is ActionType.DO:
            task_id = payload.get("task_id") or target
            if task_id not in world.tasks:
                raise ValueError(f"unknown DO task: {task_id}")
            payload["task_id"] = task_id
            return int(payload.get("duration_ticks", 6))
        if action_type is ActionType.USE:
            if "source_location" not in payload:
                payload["source_location"] = person.location_id
            if "tool" not in payload:
                if target in observation.visible_tools:
                    payload["tool"] = target
                elif target.endswith("_rack") and target[:-5] in observation.visible_tools:
                    payload["tool"] = target[:-5]
                elif len(observation.visible_tools) == 1:
                    payload["tool"] = observation.visible_tools[0]
                else:
                    raise ValueError(f"USE action missing tool field: target={target}")
            return int(payload.get("duration_ticks", 1))
        if action_type is ActionType.SPEAK:
            return int(payload.get("duration_ticks", 1))
        if action_type is ActionType.LEARN:
            return int(payload.get("duration_ticks", 6))
        if action_type is ActionType.REST:
            if not target:
                target = person.home_id
                payload["target"] = target
            return int(payload.get("duration_ticks", 3))
        raise ValueError(f"unsupported action type: {action_type}")

    def _label_for_action(self, action_type: ActionType, target: str) -> str:
        return f"{action_type.value} {target}".strip()

    def _build_structured_skills(self, skills: dict[str, Any]) -> dict[str, Any]:
        structured: dict[str, Any] = {}
        for skill_name, raw_value in skills.items():
            if isinstance(raw_value, dict):
                level = int(raw_value.get("level", 0))
                structured[skill_name] = {
                    "level": level,
                    "status": raw_value.get("status", "known" if level > 0 else "novice"),
                    "can_execute_basic": level >= 1,
                    "notes": raw_value.get("notes", ""),
                }
                continue

            level = int(raw_value)
            structured[skill_name] = {
                "level": level,
                "status": "known" if level > 0 else "novice",
                "can_execute_basic": level >= 1,
                "notes": "",
            }
        return structured


def build_policy_from_config(config: PolicyConfig) -> tuple[DecisionPolicy, str]:
    heuristic = HeuristicProtoHumanPolicy()

    if config.mode == "heuristic":
        return heuristic, "heuristic"

    openai_ready = bool(config.api_key and config.model)
    if config.mode == "openai" and not openai_ready:
        if config.fallback_to_heuristic:
            return heuristic, "heuristic_fallback_missing_openai_config"
        raise RuntimeError("DHW_POLICY_MODE=openai but OPENAI_API_KEY or OPENAI_MODEL is missing")

    if config.mode == "openai" or (config.mode == "auto" and openai_ready):
        client = OpenAICompatibleChatClient(
            api_key=config.api_key or "",
            base_url=config.base_url,
            max_retries=config.max_retries,
        )
        return (
            LLMProtoHumanPolicy(
                client=client,
                model=config.model or "",
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                timeout_seconds=config.timeout_seconds,
                fallback_policy=heuristic,
            ),
            "openai_compatible",
        )

    return heuristic, "heuristic_auto"
