"""Tests that go through the HTTP layer.

Slower than the unit tests because each one builds an application and a
database. Still well under a second each, which is the budget: a suite you
are reluctant to run is a suite that does not get run.
"""

from __future__ import annotations

import io

from fastapi.testclient import TestClient

from conftest import ADMIN_TOKEN, FLAGS
from scoreboard.app import create_app
from scoreboard.config import Settings


def _unreachable(tmp_path, challenges_file):
    """Settings whose SQLite path sits under a regular file, so it cannot be
    opened by anyone, root included. Returns the settings and the blocker."""
    blocker = tmp_path / "not-a-directory"
    blocker.write_text("")
    settings = Settings(
        database_url=f"sqlite:///{blocker}/scoreboard.db",
        challenges_file=challenges_file,
        log_format="text",
        log_level="CRITICAL",
    )
    return settings, blocker


# ---------------------------------------------------------------------------
# meta endpoints
# ---------------------------------------------------------------------------


def test_root_advertises_the_documentation(client):
    body = client.get("/").json()
    assert body["docs"] == "/docs"


def test_liveness_does_not_depend_on_anything_external(tmp_path, challenges_file):
    # The database is unreachable from the start. The process must stay up
    # and alive -- restarting it would not bring the database back.
    settings, _ = _unreachable(tmp_path, challenges_file)
    with TestClient(create_app(settings)) as c:
        assert c.get("/healthz").json() == {"status": "ok"}
        assert c.get("/scoreboard").status_code == 503


def test_readiness_reports_the_database(tmp_path, challenges_file):
    # Not ready while the database is unreachable; ready by itself, without a
    # restart, once it can be reached. This is what lab sheet 4, Part C observes.
    settings, blocker = _unreachable(tmp_path, challenges_file)
    with TestClient(create_app(settings)) as c:
        r = c.get("/readyz")
        assert r.status_code == 503
        assert r.json()["database"] is False
        blocker.unlink()
        blocker.mkdir()
        r = c.get("/readyz")
        assert r.status_code == 200
        assert r.json()["database"] is True
        assert len(c.get("/challenges").json()["challenges"]) == 6


def test_version_reports_the_build_the_pipeline_stamped(client):
    body = client.get("/version").json()
    assert body["commit"] == "testsha"
    assert body["scoring_mode"] == "decay"


def test_metrics_are_exposed_in_the_prometheus_text_format(client):
    client.get("/healthz")
    text = client.get("/metrics").text
    assert "scoreboard_http_requests_total" in text
    assert "scoreboard_build_info" in text


def test_every_response_carries_a_request_id(client):
    assert client.get("/healthz").headers["x-request-id"]


def test_an_inbound_request_id_is_preserved(client):
    r = client.get("/healthz", headers={"x-request-id": "abc123"})
    assert r.headers["x-request-id"] == "abc123"


# ---------------------------------------------------------------------------
# challenges
# ---------------------------------------------------------------------------


def test_the_competition_is_loaded_from_the_yaml_file(client):
    slugs = [c["slug"] for c in client.get("/challenges").json()["challenges"]]
    assert "warmup-banner" in slugs
    assert len(slugs) == 6


def test_the_challenge_list_never_contains_a_flag_or_its_hash(client):
    body = client.get("/challenges").text
    assert "flag" not in body.lower()


def test_an_unsolved_challenge_is_worth_its_base_points(client):
    chals = {c["slug"]: c for c in client.get("/challenges").json()["challenges"]}
    assert chals["the-long-game"]["current_value"] == 500
    assert chals["the-long-game"]["solves"] == 0


# ---------------------------------------------------------------------------
# teams
# ---------------------------------------------------------------------------


def test_a_team_can_register(client):
    assert client.post("/teams", json={"name": "alpha"}).status_code == 201


def test_a_name_cannot_be_registered_twice(client):
    client.post("/teams", json={"name": "alpha"})
    assert client.post("/teams", json={"name": "alpha"}).status_code == 409


def test_a_one_character_name_is_rejected(client):
    assert client.post("/teams", json={"name": "a"}).status_code == 422


def test_an_unknown_team_is_not_found(client):
    assert client.get("/teams/nobody").status_code == 404


def test_a_new_team_has_no_points_and_no_solves(client):
    client.post("/teams", json={"name": "alpha"})
    body = client.get("/teams/alpha").json()
    assert body["points"] == 0
    assert body["solves"] == []


# ---------------------------------------------------------------------------
# submitting
# ---------------------------------------------------------------------------


def _submit(client, team, slug, flag=None):
    return client.post(
        "/submit",
        json={"team": team, "challenge": slug, "flag": flag or FLAGS[slug]},
    )


def test_a_correct_flag_scores(registered):
    r = _submit(registered, "alpha", "the-long-game")
    assert r.status_code == 200
    assert r.json()["correct"] is True
    assert r.json()["points"] == 500


def test_the_first_solver_is_told_so(registered):
    assert _submit(registered, "alpha", "carved-out").json()["first_blood"] is True


def test_the_second_solver_is_not(registered):
    _submit(registered, "alpha", "carved-out")
    assert _submit(registered, "bravo", "carved-out").json()["first_blood"] is False


def test_the_second_solver_scores_less_than_the_first(registered):
    first = _submit(registered, "alpha", "the-long-game").json()["points"]
    second = _submit(registered, "bravo", "the-long-game").json()["points"]
    assert second < first


def test_a_wrong_flag_scores_nothing_and_is_not_an_error(registered):
    r = _submit(registered, "alpha", "carved-out", flag="UEM9{wrong}")
    assert r.status_code == 200
    assert r.json() == {
        "correct": False,
        "points": 0,
        "message": "incorrect flag",
        "first_blood": False,
    }


def test_a_wrong_attempt_is_recorded(registered):
    _submit(registered, "alpha", "carved-out", flag="UEM9{wrong}")
    assert registered.get("/teams/alpha").json()["attempts"] == 1


def test_surrounding_whitespace_in_a_submission_is_forgiven(registered):
    flag = "  " + FLAGS["warmup-banner"] + "\n"
    assert _submit(registered, "alpha", "warmup-banner", flag=flag).json()["correct"]


def test_a_challenge_cannot_be_solved_twice_by_the_same_team(registered):
    _submit(registered, "alpha", "carved-out")
    assert _submit(registered, "alpha", "carved-out").status_code == 409


def test_submitting_for_an_unknown_team_is_not_found(client):
    assert _submit(client, "ghost", "carved-out").status_code == 404


def test_submitting_an_unknown_challenge_is_not_found(registered):
    r = registered.post(
        "/submit", json={"team": "alpha", "challenge": "nope", "flag": "x"}
    )
    assert r.status_code == 404


def test_a_solve_raises_the_teams_total(registered):
    _submit(registered, "alpha", "the-long-game")
    assert registered.get("/teams/alpha").json()["points"] == 500


def test_the_solve_count_on_the_challenge_list_goes_up(registered):
    _submit(registered, "alpha", "carved-out")
    chals = {c["slug"]: c for c in registered.get("/challenges").json()["challenges"]}
    assert chals["carved-out"]["solves"] == 1


# ---------------------------------------------------------------------------
# the scoreboard
# ---------------------------------------------------------------------------


def test_the_scoreboard_of_an_empty_competition_is_empty_not_an_error(client):
    r = client.get("/scoreboard")
    assert r.status_code == 200
    assert r.json() == {"standings": [], "teams": 0}


def test_registered_teams_appear_even_before_they_score(registered):
    body = registered.get("/scoreboard").json()
    assert body["teams"] == 3
    assert all(row["points"] == 0 for row in body["standings"])


def test_the_scoreboard_ranks_by_points(registered):
    _submit(registered, "alpha", "the-long-game")  # 500
    _submit(registered, "bravo", "warmup-banner")  # 100
    standings = registered.get("/scoreboard").json()["standings"]
    assert standings[0]["team"] == "alpha"
    assert standings[0]["rank"] == 1
    assert standings[1]["team"] == "bravo"


def test_a_team_that_never_scored_is_last(registered):
    _submit(registered, "alpha", "warmup-banner")
    _submit(registered, "bravo", "carved-out")
    standings = registered.get("/scoreboard").json()["standings"]
    assert standings[-1]["points"] == 0
    assert standings[-1]["last_solve"] is None


# ---------------------------------------------------------------------------
# administration
# ---------------------------------------------------------------------------


def test_an_admin_endpoint_refuses_a_request_with_no_token(registered):
    assert registered.post("/admin/reset").status_code == 401


def test_an_admin_endpoint_refuses_a_wrong_token(registered):
    r = registered.post("/admin/reset", headers={"x-admin-token": "wrong"})
    assert r.status_code == 401


def test_reset_clears_the_competition(registered):
    _submit(registered, "alpha", "carved-out")
    r = registered.post("/admin/reset", headers={"x-admin-token": ADMIN_TOKEN})
    assert r.status_code == 200
    assert registered.get("/scoreboard").json()["teams"] == 0


def test_teams_can_be_imported_from_csv(client):
    csv_bytes = b"name,country\ndelta,DZ\necho,FR\n"
    r = client.post(
        "/admin/teams/import",
        headers={"x-admin-token": ADMIN_TOKEN},
        files={"file": ("teams.csv", io.BytesIO(csv_bytes), "text/csv")},
    )
    assert r.json() == {"added": 2, "skipped": 0}
    assert client.get("/teams/delta").json()["country"] == "DZ"


def test_importing_a_name_that_already_exists_skips_it(client):
    client.post("/teams", json={"name": "delta"})
    csv_bytes = b"name,country\ndelta,DZ\nfoxtrot,DZ\n"
    r = client.post(
        "/admin/teams/import",
        headers={"x-admin-token": ADMIN_TOKEN},
        files={"file": ("teams.csv", io.BytesIO(csv_bytes), "text/csv")},
    )
    assert r.json() == {"added": 1, "skipped": 1}


def test_timestamps_come_back_in_utc_on_every_backend(registered):
    # SQLite drops the timezone unless the column type puts it back. This
    # test is the guard: it passes on SQLite and on Postgres, and it fails
    # the day somebody replaces UTCDateTime with a plain DateTime.
    _submit(registered, "alpha", "carved-out")
    at = registered.get("/teams/alpha").json()["solves"][0]["at"]
    assert at.endswith("+00:00")
