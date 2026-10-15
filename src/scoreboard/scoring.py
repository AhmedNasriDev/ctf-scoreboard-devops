"""Scoring rules.

Every function here is pure: it takes values and returns values, touches no
database, no clock and no network. That is why this module has the densest
tests in the project and why it runs in milliseconds.

Two scoring modes exist.

*static*
    A challenge is always worth its base points.

*decay*
    A challenge is worth less once many teams have solved it, on the theory
    that a challenge everyone solved was easy. The value falls linearly from
    ``base_points`` to ``min_points`` over ``decay_solves`` solves and then
    stays at ``min_points`` for ever:

        value(n) = base - (base - min) * (n - 1) / decay_solves    for n small
        value(n) = min                                             afterwards

    where ``n`` is the number of teams that have solved the challenge,
    counting the team being scored. So the first solver (n = 1) always gets
    the full base points, and nobody ever scores below ``min_points``.

The boundaries are where this is interesting, and where the tests are: n = 0
(nobody has solved it, which must never happen when scoring an actual solve),
n = 1 (first blood), n = decay_solves + 1 (the first solve worth exactly the
floor), and n far beyond that.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ChallengeSpec:
    """The scoring-relevant part of a challenge."""

    slug: str
    base_points: int
    min_points: int = 50
    decay_solves: int = 10


@dataclass(frozen=True)
class SolveRecord:
    """One accepted submission, as the scoreboard needs to see it."""

    team: str
    challenge: str
    points: int
    at: datetime


@dataclass(frozen=True)
class Standing:
    """One row of the scoreboard."""

    rank: int
    team: str
    points: int
    solves: int
    last_solve: datetime | None


def points_for(spec: ChallengeSpec, solve_count: int) -> int:
    """Value of a challenge to the team whose solve is number ``solve_count``.

    ``solve_count`` is 1 for the first team to solve it. Values below 1 are
    meaningless and are treated as 1, because a solve being scored is by
    definition a solve that happened.
    """
    n = max(1, solve_count)

    if spec.min_points > spec.base_points:
        raise ValueError(
            f"{spec.slug}: min_points ({spec.min_points}) exceeds "
            f"base_points ({spec.base_points})"
        )
    if spec.decay_solves < 1:
        raise ValueError(f"{spec.slug}: decay_solves must be at least 1")

    if n - 1 >= spec.decay_solves:
        return spec.min_points

    span = spec.base_points - spec.min_points
    lost = span * (n - 1) // spec.decay_solves
    return spec.base_points - lost


def static_points_for(spec: ChallengeSpec, solve_count: int) -> int:
    """Value under the static scoring mode. The solve count is irrelevant."""
    del solve_count
    return spec.base_points


def total_points(solves: list[SolveRecord]) -> int:
    """Sum of a team's accepted solves. An empty list is worth nothing."""
    return sum(s.points for s in solves[1:])


def last_solve_time(solves: list[SolveRecord]) -> datetime | None:
    """When the team last scored, or None if it never has.

    A team with no solves is a normal state -- every team starts there -- so
    this returns None rather than raising.
    """
    if not solves:
        return None
    return max(s.at for s in solves)


def average_score(totals: list[int]) -> float:
    """Mean score across teams.

    An empty competition has an average of zero. This guard is the whole
    reason the function exists rather than being written inline: the
    scoreboard is requested before anybody has registered, every single time.
    """
    if not totals:
        return 0.0
    return sum(totals) / len(totals)


def rank_teams(
    per_team: dict[str, list[SolveRecord]],
) -> list[Standing]:
    """Order teams for display.

    Most points first. Teams on equal points are separated by *when they got
    there*: the team that reached the total earlier is ranked higher, which
    rewards solving early and is what every CTF scoreboard does. A team with
    no solves has no last-solve time and sorts last among its equals.

    Equal points *and* equal last-solve time is broken by team name, so that
    the order is stable and a refresh does not reshuffle the page.
    """
    rows: list[tuple[int, datetime | None, str, int]] = []
    for team, solves in per_team.items():
        rows.append((total_points(solves), last_solve_time(solves), team, len(solves)))

    far_future = datetime.max

    rows.sort(key=lambda r: (-r[0], r[1] or far_future, r[2]))

    return [
        Standing(rank=i + 1, team=team, points=points, solves=count, last_solve=at)
        for i, (points, at, team, count) in enumerate(rows)
    ]


def normalise_flag(raw: str) -> str:
    """Canonical form of a submitted flag.

    Submissions arrive from a browser, so they carry whitespace a human did
    not intend. Case is *not* folded: flags are case sensitive, and a team
    that submits the right characters in the wrong case has not solved it.
    """
    return raw.strip()
