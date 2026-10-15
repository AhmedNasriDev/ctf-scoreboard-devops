"""Shared test fixtures.

Every test gets a fresh in-memory-ish database in a temporary directory, so
the suite is order independent and leaves nothing behind. A suite that only
passes when run in a particular order is a suite that will fail in the
pipeline, where it is sharded.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from scoreboard.app import create_app
from scoreboard.config import Settings

# The demonstration competition, in the same order as data/challenges.yaml.
FLAGS = {
    "warmup-banner": "UEM9{read_the_banner}",
    "rot-thirteen": "UEM9{caesar_salad_with_13_croutons}",
    "leaky-headers": "UEM9{x_powered_by_too_much}",
    "stack-the-deck": "UEM9{off_by_one_off_by_all}",
    "carved-out": "UEM9{the_filesystem_remembers}",
    "the-long-game": "UEM9{patience_is_a_side_channel}",
}

ADMIN_TOKEN = "test-admin-token-not-a-real-secret"  # noqa: S105


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


@pytest.fixture
def challenges_file(tmp_path) -> str:
    lines = ["challenges:"]
    specs = [
        ("warmup-banner", "Read the banner", "misc", 100, 100, 1),
        ("rot-thirteen", "Caesar had a favourite number", "crypto", 200, 80, 15),
        ("leaky-headers", "Too much information", "web", 300, 100, 12),
        ("stack-the-deck", "Off by one, off by all", "pwn", 400, 120, 8),
        ("carved-out", "What the filesystem forgot", "forensics", 350, 100, 10),
        ("the-long-game", "Patience is a side channel", "crypto", 500, 150, 5),
    ]
    for slug, title, category, points, floor, decay in specs:
        lines += [
            f"  - slug: {slug}",
            f"    title: {title}",
            f"    category: {category}",
            f"    points: {points}",
            f"    min_points: {floor}",
            f"    decay_solves: {decay}",
            f'    flag_sha256: "{_sha(FLAGS[slug])}"',
        ]
    path = tmp_path / "challenges.yaml"
    path.write_text("\n".join(lines) + "\n")
    return str(path)


@pytest.fixture
def settings(tmp_path, challenges_file) -> Settings:
    return Settings(
        database_url=f"sqlite:///{tmp_path}/test.db",
        challenges_file=challenges_file,
        admin_token=ADMIN_TOKEN,
        log_format="text",
        log_level="WARNING",
        build_sha="testsha",
    )


@pytest.fixture
def client(settings) -> Iterator[TestClient]:
    with TestClient(create_app(settings)) as c:
        yield c


@pytest.fixture
def registered(client) -> TestClient:
    for name in ("alpha", "bravo", "charlie"):
        assert client.post("/teams", json={"name": name}).status_code == 201
    return client
