"""Configuration.

Every setting comes from an environment variable. Nothing is read from a file
that lives only on a developer's machine, and nothing is hardcoded. That is a
deliberate property of this application: from lab sheet 3 onwards it runs in a
container, and from lab sheet 4 onwards in a cluster, where the only way in is the
environment.

See .env.example for the full list with defaults.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _as_bool(raw: str | None, default: bool) -> bool:
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _as_float(raw: str | None, default: float) -> float:
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _as_int(raw: str | None, default: int) -> int:
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    """Immutable snapshot of the environment, read once at startup."""

    # --- service identity -------------------------------------------------
    service_name: str = "ctf-scoreboard"
    # Set by the pipeline from the commit SHA. Reported by GET /version, which
    # is how you tell which build is actually running during a canary or a
    # blue-green cutover (lab sheet 5).
    build_sha: str = "dev"
    build_time: str = "unknown"
    environment: str = "local"

    # --- storage ----------------------------------------------------------
    database_url: str = "sqlite:///./data/scoreboard.db"

    # --- domain -----------------------------------------------------------
    challenges_file: str = "data/challenges.yaml"
    # "decay"  : a challenge is worth less once many teams have solved it
    # "static" : every solve is worth the challenge's base points
    # Switching this between two running versions makes a canary genuinely
    # behave differently, which is the point of the canary in lab sheet 5, Part D.
    scoring_mode: str = "decay"

    # --- administration ---------------------------------------------------
    # No default. If it is unset the admin endpoints refuse every request,
    # which is the correct behaviour for a missing secret: fail closed.
    admin_token: str | None = None

    # --- outbound ---------------------------------------------------------
    # Optional webhook called on a first blood. Left empty, nothing is sent.
    webhook_url: str = ""
    webhook_timeout_s: float = 2.0

    # --- deliberate, controllable misbehaviour ----------------------------
    # These exist so that lab sheet 5 has an error budget to spend (Part C) and
    # a canary analysis has something to reject. Default: off.
    error_rate: float = 0.0  # fraction of /scoreboard requests that return 500
    slow_scoreboard_ms: int = 0  # artificial delay added to /scoreboard

    # --- server -----------------------------------------------------------
    host: str = "0.0.0.0"  # noqa: S104 - a container must bind all interfaces
    port: int = 8000
    log_level: str = "INFO"
    log_format: str = "json"  # "json" or "text"

    extra: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            service_name=os.getenv("SERVICE_NAME", "ctf-scoreboard"),
            build_sha=os.getenv("BUILD_SHA", "dev"),
            build_time=os.getenv("BUILD_TIME", "unknown"),
            environment=os.getenv("ENVIRONMENT", "local"),
            database_url=os.getenv("DATABASE_URL", "sqlite:///./data/scoreboard.db"),
            challenges_file=os.getenv("CHALLENGES_FILE", "data/challenges.yaml"),
            scoring_mode=os.getenv("SCORING_MODE", "decay"),
            admin_token=os.getenv("ADMIN_TOKEN") or None,
            webhook_url=os.getenv("WEBHOOK_URL", ""),
            webhook_timeout_s=_as_float(os.getenv("WEBHOOK_TIMEOUT_S"), 2.0),
            error_rate=_as_float(os.getenv("ERROR_RATE"), 0.0),
            slow_scoreboard_ms=_as_int(os.getenv("SLOW_SCOREBOARD_MS"), 0),
            host=os.getenv("HOST", "0.0.0.0"),  # noqa: S104
            port=_as_int(os.getenv("PORT"), 8000),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            log_format=os.getenv("LOG_FORMAT", "json"),
        )

    @property
    def data_dir(self) -> Path:
        return Path("data")

    @property
    def admin_enabled(self) -> bool:
        return bool(self.admin_token)
