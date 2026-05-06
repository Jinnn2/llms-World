from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class PolicyConfig:
    mode: str = "auto"
    api_key: str | None = None
    base_url: str = "https://api.openai.com/v1"
    model: str | None = None
    timeout_seconds: int = 30
    temperature: float | None = None
    max_tokens: int = 180
    max_retries: int = 2
    fallback_to_heuristic: bool = True


def load_policy_config(env_path: str | Path = ".env") -> PolicyConfig:
    _load_env_file(env_path)
    return PolicyConfig(
        mode=os.getenv("DHW_POLICY_MODE", "auto").strip().lower() or "auto",
        api_key=_none_if_blank(os.getenv("OPENAI_API_KEY")),
        base_url=(os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1").rstrip("/"),
        model=_none_if_blank(os.getenv("OPENAI_MODEL")),
        timeout_seconds=_int_env("DHW_TIMEOUT_SECONDS", default=30),
        temperature=_optional_float_env("DHW_TEMPERATURE"),
        max_tokens=_int_env("DHW_MAX_TOKENS", default=180),
        max_retries=_int_env("DHW_MAX_RETRIES", default=2),
        fallback_to_heuristic=_bool_env("DHW_FALLBACK_TO_HEURISTIC", default=True),
    )


def _load_env_file(env_path: str | Path) -> None:
    path = Path(env_path)
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _none_if_blank(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _float_env(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _optional_float_env(name: str) -> float | None:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def _bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}
