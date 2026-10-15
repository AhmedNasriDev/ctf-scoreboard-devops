"""Unit tests for the pure scoring logic.

These are the fast tests. They touch nothing but arithmetic, they run in
milliseconds, and they are therefore the first thing the pipeline runs and
the first thing that should fail when the logic is wrong.

Most of them test a *boundary*: the first solve, the last decaying solve, the
first floored solve, and the empty case. That is deliberate. A test suite
made of middle-of-the-range values passes happily while the edges are broken,
and the edges are where defects live.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from scoreboard.scoring import (
    ChallengeSpec,
    SolveRecord,
    average_score,
    last_solve_time,
    normalise_flag,
    points_for,
    rank_teams,
    static_points_for,
    total_points,
)

T0 = datetime(2026, 3, 1, 12, 0, tzinfo=UTC)

# base 500, floor 100, decaying over 8 solves: each solve costs 50 points.
SPEC = ChallengeSpec(slug="demo", base_points=500, min_points=100, decay_solves=8)


def test_first_solver_gets_full_base_points():
    assert points_for(SPEC, 1) == 500


def test_value_decays_by_one_step_per_solve():
    # span 400 over 8 solves = 50 per solve
    assert points_for(SPEC, 2) == 450
    assert points_for(SPEC, 3) == 400


def test_last_decaying_solve_is_one_step_above_the_floor():
    # n - 1 == 7 < 8, so still decaying: 500 - 400*7//8 = 500 - 350
    assert points_for(SPEC, 8) == 150


def test_first_floored_solve_is_exactly_the_floor():
    # n - 1 == 8 == decay_solves: the floor begins here
    assert points_for(SPEC, 9) == 100


def test_value_never_falls_below_the_floor():
    assert points_for(SPEC, 50) == 100
    assert points_for(SPEC, 10_000) == 100


def test_a_solve_count_below_one_is_treated_as_the_first_solve():
    assert points_for(SPEC, 0) == 500
    assert points_for(SPEC, -3) == 500


def test_a_challenge_that_does_not_decay_is_always_worth_its_base():
    flat = ChallengeSpec(slug="flat", base_points=100, min_points=100, decay_solves=1)
    assert [points_for(flat, n) for n in (1, 2, 99)] == [100, 100, 100]


def test_a_floor_above_the_base_is_rejected():
    bad = ChallengeSpec(slug="bad", base_points=100, min_points=400, decay_solves=5)
    with pytest.raises(ValueError, match="exceeds"):
        points_for(bad, 1)


def test_a_non_positive_decay_window_is_rejected():
    bad = ChallengeSpec(slug="bad", base_points=100, min_points=10, decay_solves=0)
    with pytest.raises(ValueError, match="at least 1"):
        points_for(bad, 1)


def test_static_mode_ignores_the_solve_count():
    assert static_points_for(SPEC, 1) == 500
    assert static_points_for(SPEC, 99) == 500


# ---------------------------------------------------------------------------
# aggregation
# ---------------------------------------------------------------------------


def _solve(team: str, points: int, minutes: int) -> SolveRecord:
    return SolveRecord(
        team=team, challenge="c", points=points, at=T0 + timedelta(minutes=minutes)
    )


def test_total_of_no_solves_is_zero():
    assert total_points([]) == 0


def test_total_sums_the_solves():
    assert total_points([_solve("a", 100, 0), _solve("a", 250, 5)]) == 350


def test_last_solve_time_of_a_team_that_has_never_scored_is_none():
    assert last_solve_time([]) is None


def test_last_solve_time_is_the_most_recent_not_the_last_added():
    solves = [_solve("a", 100, 30), _solve("a", 100, 5)]
    assert last_solve_time(solves) == T0 + timedelta(minutes=30)


def test_average_of_an_empty_competition_is_zero():
    # The scoreboard is requested before anybody registers, every time.
    assert average_score([]) == 0.0


def test_average_is_the_mean():
    assert average_score([100, 200, 300]) == 200.0


# ---------------------------------------------------------------------------
# ranking
# ---------------------------------------------------------------------------


def test_ranking_orders_by_points_descending():
    standings = rank_teams(
        {
            "low": [_solve("low", 100, 0)],
            "high": [_solve("high", 900, 0)],
            "mid": [_solve("mid", 500, 0)],
        }
    )
    assert [s.team for s in standings] == ["high", "mid", "low"]
    assert [s.rank for s in standings] == [1, 2, 3]


def test_equal_points_are_broken_by_who_got_there_first():
    # The names run in the opposite order to the times on purpose. A ranking
    # that dropped the time tiebreak and fell back to the name would put
    # "aardvark" first and pass a test written with friendlier names, which
    # is how a broken tiebreak survives a test suite.
    standings = rank_teams(
        {
            "aardvark": [_solve("aardvark", 300, 90)],
            "zebra": [_solve("zebra", 300, 10)],
        }
    )
    assert [s.team for s in standings] == ["zebra", "aardvark"]


def test_a_team_with_no_solves_ranks_below_every_scorer():
    standings = rank_teams(
        {
            "idle": [],
            "busy": [_solve("busy", 10, 0)],
        }
    )
    assert [s.team for s in standings] == ["busy", "idle"]
    assert standings[1].points == 0
    assert standings[1].last_solve is None


def test_teams_with_no_solves_are_ordered_by_name_so_the_page_is_stable():
    standings = rank_teams({"zulu": [], "alpha": [], "mike": []})
    assert [s.team for s in standings] == ["alpha", "mike", "zulu"]


def test_ranking_an_empty_competition_returns_nothing():
    assert rank_teams({}) == []


def test_solve_count_is_reported_per_team():
    standings = rank_teams(
        {"a": [_solve("a", 10, 1), _solve("a", 20, 2)], "b": [_solve("b", 5, 1)]}
    )
    assert {s.team: s.solves for s in standings} == {"a": 2, "b": 1}


# ---------------------------------------------------------------------------
# flag handling
# ---------------------------------------------------------------------------


def test_surrounding_whitespace_is_forgiven():
    assert normalise_flag("  UEM9{x}\n") == "UEM9{x}"


def test_case_is_not_forgiven():
    assert normalise_flag("UEM9{X}") != normalise_flag("uem9{x}")
