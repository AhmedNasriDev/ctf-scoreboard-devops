"""Tests for loading the competition definition."""

from __future__ import annotations

import pytest

from scoreboard.challenges import ChallengeFileError, flag_hash, load, parse


def test_an_empty_document_defines_no_challenges():
    assert parse("") == []


def test_a_plaintext_flag_is_hashed_at_load_time():
    [c] = parse(
        "challenges:\n"
        "  - slug: a\n"
        "    title: A\n"
        "    points: 100\n"
        "    flag: UEM9{hello}\n"
    )
    assert c.flag_hash == flag_hash("UEM9{hello}")
    assert len(c.flag_hash) == 64


def test_an_already_hashed_flag_is_taken_as_is():
    digest = "a" * 64
    [c] = parse(
        f"challenges:\n  - slug: a\n    title: A\n    points: 1\n"
        f"    flag_sha256: {digest}\n"
    )
    assert c.flag_hash == digest


def test_defaults_are_applied():
    [c] = parse(
        "challenges:\n  - slug: a\n    title: A\n    points: 400\n    flag: x\n"
    )
    assert c.category == "misc"
    assert c.min_points == 50
    assert c.decay_solves == 10


def test_a_challenge_with_no_flag_is_rejected():
    with pytest.raises(ChallengeFileError, match="flag"):
        parse("challenges:\n  - slug: a\n    title: A\n    points: 1\n")


def test_a_challenge_with_no_points_is_rejected():
    with pytest.raises(ChallengeFileError, match="points"):
        parse("challenges:\n  - slug: a\n    title: A\n    flag: x\n")


def test_a_truncated_hash_is_rejected():
    with pytest.raises(ChallengeFileError, match="64 hex"):
        parse(
            "challenges:\n  - slug: a\n    title: A\n    points: 1\n"
            "    flag_sha256: abc\n"
        )


def test_a_duplicate_slug_is_rejected():
    doc = (
        "challenges:\n"
        "  - slug: a\n    title: A\n    points: 1\n    flag: x\n"
        "  - slug: a\n    title: B\n    points: 1\n    flag: y\n"
    )
    with pytest.raises(ChallengeFileError, match="duplicate"):
        parse(doc)


def test_malformed_yaml_is_reported_as_such():
    with pytest.raises(ChallengeFileError, match="not valid YAML"):
        parse("challenges:\n  - slug: a\n   bad indent: [\n")


def test_a_document_without_a_challenges_key_is_rejected():
    with pytest.raises(ChallengeFileError, match="challenges"):
        parse("something_else: 1\n")


def test_a_missing_file_is_reported_clearly():
    with pytest.raises(ChallengeFileError, match="not found"):
        load("/nonexistent/challenges.yaml")


def test_the_shipped_competition_file_is_valid():
    # Guards against a typo in data/challenges.yaml reaching the pipeline.
    defs = load("data/challenges.yaml")
    assert len(defs) >= 5
    assert all(len(d.flag_hash) == 64 for d in defs)
    assert len({d.slug for d in defs}) == len(defs)
