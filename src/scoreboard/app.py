"""The HTTP service.

Routes, in the order a visitor meets them:

    GET  /                      service banner
    GET  /healthz               liveness   -- is the process wedged?
    GET  /readyz                readiness  -- can it serve?
    GET  /version               build identity
    GET  /metrics               Prometheus exposition
    GET  /challenges            the competition, without the flags
    POST /teams                 register a team
    GET  /teams/{name}          one team and its solves
    POST /submit                submit a flag
    GET  /scoreboard            the standings
    POST /admin/reset           wipe the competition   (admin token)
    POST /admin/teams/import    bulk import from CSV   (admin token)

The interactive documentation is at /docs.
"""

from __future__ import annotations

import csv
import hmac
import io
import logging
import random
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException, Request, UploadFile
from fastapi import File as FileParam
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import delete, func, select
from sqlalchemy.exc import DBAPIError

from . import challenges as challenge_loader
from . import db, logging_setup, metrics
from .config import Settings
from .models import Challenge, Submission, Team
from .scoring import (
    ChallengeSpec,
    SolveRecord,
    normalise_flag,
    points_for,
    rank_teams,
    static_points_for,
)

log = logging.getLogger("scoreboard")

VERSION = "1.0.0"


# ---------------------------------------------------------------------------
# request and response shapes
# ---------------------------------------------------------------------------


class TeamIn(BaseModel):
    name: str = Field(min_length=2, max_length=64)
    country: str = Field(default="", max_length=64)


class SubmissionIn(BaseModel):
    team: str = Field(min_length=2, max_length=64)
    challenge: str = Field(min_length=1, max_length=64)
    flag: str = Field(min_length=1, max_length=256)


class SubmissionOut(BaseModel):
    correct: bool
    points: int
    message: str
    first_blood: bool = False


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _spec(row: Challenge) -> ChallengeSpec:
    return ChallengeSpec(
        slug=row.slug,
        base_points=row.base_points,
        min_points=row.min_points,
        decay_solves=row.decay_solves,
    )


def _notify(settings: Settings, text: str) -> None:
    """Fire a webhook, and never let it break the request.

    Imported lazily so that a service with no webhook configured does not pay
    for the import, and so that the dependency is visibly optional.
    """
    if not settings.webhook_url:
        return
    try:
        import requests

        requests.post(
            settings.webhook_url,
            json={"text": text},
            timeout=settings.webhook_timeout_s,
        )
    except Exception as exc:  # noqa: BLE001 - a webhook must never 500 a solve
        log.warning("webhook failed", extra={"error": str(exc)})


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    logging_setup.configure(settings.log_level, settings.log_format)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        # A malformed or missing challenge file is a configuration error, so
        # it stops the process at once: a crash loop is the honest signal.
        # An unreachable database is not; see _bring_up.
        app.state.challenge_defs = challenge_loader.load(settings.challenges_file)
        app.state.ready = False
        db.reset()
        metrics.BUILD.labels(
            version=VERSION,
            commit=settings.build_sha,
            environment=settings.environment,
        ).set(1)
        _bring_up(app, settings)
        log.info(
            "started",
            extra={
                "challenges": len(app.state.challenge_defs),
                "database_ready": app.state.ready,
                "scoring_mode": settings.scoring_mode,
                "build_sha": settings.build_sha,
                "admin_enabled": settings.admin_enabled,
            },
        )
        yield
        log.info("stopping")

    app = FastAPI(
        title="CTF Scoreboard",
        version=VERSION,
        summary="A small scoreboard for a capture-the-flag competition.",
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.ready = False

    app.middleware("http")(metrics.metrics_middleware)
    app.middleware("http")(logging_setup.request_id_middleware)

    @app.exception_handler(db.DatabaseUnavailable)
    @app.exception_handler(DBAPIError)
    async def database_unavailable(request: Request, exc: Exception) -> JSONResponse:
        # The database went away, or never arrived. That is "cannot serve
        # right now" (503), not "the code is wrong" (500).
        log.warning("database unavailable", extra={"error": type(exc).__name__})
        return JSONResponse(status_code=503, content={"detail": "database unavailable"})

    _register_routes(app, settings)
    return app


def _bring_up(app: FastAPI, settings: Settings) -> bool:
    """Connect, create the tables and load the competition, once.

    Called at start-up and again from every readiness probe until it
    succeeds, so a pod whose database is down at boot becomes ready by itself
    when the database arrives -- without a restart.
    """
    if app.state.ready:
        return True
    if not db.try_init(settings.database_url):
        return False
    try:
        _reconcile(app.state.challenge_defs)
        with db.session_scope() as s:
            metrics.TEAMS.set(s.scalar(select(func.count()).select_from(Team)) or 0)
    except Exception as exc:  # noqa: BLE001 - not ready yet; the probe retries
        log.error("database reachable but not usable", extra={"error": str(exc)})
        db.reset()
        return False
    app.state.ready = True
    return True


def _load_challenges(settings: Settings) -> int:
    """Read the YAML and reconcile it into the database."""
    return _reconcile(challenge_loader.load(settings.challenges_file))


def _reconcile(defs: list[challenge_loader.ChallengeDef]) -> int:
    """Reconcile challenge definitions into the database.

    Idempotent: running it twice changes nothing. That matters because the
    container restarts, and idempotency is a subject of chapter 5 (lab
    sheet 4, at home).
    """
    with db.session_scope() as s:
        for d in defs:
            row = s.scalar(select(Challenge).where(Challenge.slug == d.slug))
            if row is None:
                s.add(
                    Challenge(
                        slug=d.slug,
                        title=d.title,
                        category=d.category,
                        base_points=d.base_points,
                        min_points=d.min_points,
                        decay_solves=d.decay_solves,
                        flag_hash=d.flag_hash,
                    )
                )
            else:
                row.title = d.title
                row.category = d.category
                row.base_points = d.base_points
                row.min_points = d.min_points
                row.decay_solves = d.decay_solves
                row.flag_hash = d.flag_hash
    return len(defs)


def _require_admin(settings: Settings):
    def dependency(x_admin_token: str = Header(default="")) -> None:
        if not settings.admin_enabled:
            # Fail closed. A service with no admin token configured has no
            # administrator, rather than an administrator anyone can be.
            raise HTTPException(status_code=503, detail="admin interface disabled")
        # Constant-time comparison: a plain == leaks the token one character
        # at a time to anyone who can measure the response.
        if not hmac.compare_digest(x_admin_token, settings.admin_token or ""):
            raise HTTPException(status_code=401, detail="bad admin token")

    return dependency


def _register_routes(app: FastAPI, settings: Settings) -> None:
    admin = Depends(_require_admin(settings))

    def require_ready() -> None:
        # Cheap once the service is up: one attribute check. Until then each
        # request retries the connection, so the service recovers by itself.
        if not app.state.ready and not _bring_up(app, settings):
            raise db.DatabaseUnavailable("the database has not been reached yet")

    ready = Depends(require_ready)

    @app.get("/", tags=["meta"])
    def root() -> dict:
        return {
            "service": settings.service_name,
            "version": VERSION,
            "docs": "/docs",
            "scoreboard": "/scoreboard",
        }

    @app.get("/healthz", tags=["meta"])
    def healthz() -> dict:
        """Liveness. Deliberately checks nothing external.

        If this fails the process is broken and restarting it is the right
        response. It must not depend on the database: restarting the
        container will not bring the database back, it will only add an
        outage of its own.
        """
        return {"status": "ok"}

    @app.get("/readyz", tags=["meta"])
    def readyz() -> JSONResponse:
        """Readiness. Fails when the service cannot serve.

        Here that means the database is unreachable. A failing readiness
        probe takes the pod out of the load balancer and leaves it running,
        so it rejoins by itself when the database comes back.
        """
        ok = _bring_up(app, settings) and db.ping()
        return JSONResponse(
            status_code=200 if ok else 503,
            content={"status": "ready" if ok else "degraded", "database": ok},
        )

    @app.get("/version", tags=["meta"])
    def version() -> dict:
        return {
            "version": VERSION,
            "commit": settings.build_sha,
            "built": settings.build_time,
            "environment": settings.environment,
            "scoring_mode": settings.scoring_mode,
        }

    @app.get("/metrics", include_in_schema=False)
    def prometheus_metrics():
        return metrics.render()

    @app.get("/challenges", tags=["competition"], dependencies=[ready])
    def list_challenges() -> dict:
        with db.session_scope() as s:
            rows = s.scalars(select(Challenge).order_by(Challenge.slug)).all()
            counts = dict(
                s.execute(
                    select(Submission.challenge_id, func.count())
                    .where(Submission.correct.is_(True))
                    .group_by(Submission.challenge_id)
                ).all()
            )
            out = []
            for row in rows:
                solves = counts.get(row.id, 0)
                if settings.scoring_mode == "static":
                    value = static_points_for(_spec(row), solves + 1)
                else:
                    value = points_for(_spec(row), solves + 1)
                out.append(
                    {
                        "slug": row.slug,
                        "title": row.title,
                        "category": row.category,
                        "base_points": row.base_points,
                        "current_value": value,
                        "solves": solves,
                    }
                )
        return {"challenges": out, "scoring_mode": settings.scoring_mode}

    @app.post("/teams", status_code=201, tags=["competition"], dependencies=[ready])
    def register_team(payload: TeamIn) -> dict:
        name = payload.name.strip()
        with db.session_scope() as s:
            if s.scalar(select(Team).where(Team.name == name)):
                raise HTTPException(status_code=409, detail="team already registered")
            s.add(Team(name=name, country=payload.country.strip()))
        with db.session_scope() as s:
            metrics.TEAMS.set(s.scalar(select(func.count()).select_from(Team)) or 0)
        log.info("team registered", extra={"team": name})
        return {"team": name, "registered": True}

    @app.get("/teams/{name}", tags=["competition"], dependencies=[ready])
    def get_team(name: str) -> dict:
        with db.session_scope() as s:
            team = s.scalar(select(Team).where(Team.name == name))
            if team is None:
                raise HTTPException(status_code=404, detail="no such team")
            rows = s.execute(
                select(Challenge.slug, Submission.points, Submission.submitted_at)
                .join(Submission, Submission.challenge_id == Challenge.id)
                .where(Submission.team_id == team.id, Submission.correct.is_(True))
                .order_by(Submission.submitted_at)
            ).all()
            attempts = s.scalar(
                select(func.count())
                .select_from(Submission)
                .where(Submission.team_id == team.id)
            )
            return {
                "team": team.name,
                "country": team.country,
                "points": sum(r[1] for r in rows),
                "attempts": attempts or 0,
                "solves": [
                    {"challenge": r[0], "points": r[1], "at": r[2].isoformat()}
                    for r in rows
                ],
            }

    @app.post(
        "/submit",
        response_model=SubmissionOut,
        tags=["competition"],
        dependencies=[ready],
    )
    def submit(payload: SubmissionIn) -> SubmissionOut:
        submitted = normalise_flag(payload.flag)
        with db.session_scope() as s:
            team = s.scalar(select(Team).where(Team.name == payload.team.strip()))
            if team is None:
                raise HTTPException(status_code=404, detail="no such team")
            chal = s.scalar(
                select(Challenge).where(Challenge.slug == payload.challenge.strip())
            )
            if chal is None:
                raise HTTPException(status_code=404, detail="no such challenge")

            already = s.scalar(
                select(Submission).where(
                    Submission.team_id == team.id,
                    Submission.challenge_id == chal.id,
                    Submission.correct.is_(True),
                )
            )
            if already is not None:
                raise HTTPException(status_code=409, detail="already solved")

            correct = hmac.compare_digest(
                challenge_loader.flag_hash(submitted), chal.flag_hash
            )

            if not correct:
                s.add(
                    Submission(
                        team_id=team.id, challenge_id=chal.id, correct=False, points=0
                    )
                )
                metrics.SUBMISSIONS.labels(
                    category=chal.category, outcome="incorrect"
                ).inc()
                log.info(
                    "submission rejected",
                    extra={"team": team.name, "challenge": chal.slug},
                )
                return SubmissionOut(correct=False, points=0, message="incorrect flag")

            prior = (
                s.scalar(
                    select(func.count())
                    .select_from(Submission)
                    .where(
                        Submission.challenge_id == chal.id,
                        Submission.correct.is_(True),
                    )
                )
                or 0
            )
            nth = prior + 1
            if settings.scoring_mode == "static":
                value = static_points_for(_spec(chal), nth)
            else:
                value = points_for(_spec(chal), nth)

            s.add(
                Submission(
                    team_id=team.id,
                    challenge_id=chal.id,
                    correct=True,
                    points=value,
                )
            )
            metrics.SUBMISSIONS.labels(category=chal.category, outcome="correct").inc()
            first_blood = nth == 1
            team_name, chal_title = team.name, chal.title

        log.info(
            "solve",
            extra={
                "team": team_name,
                "challenge": payload.challenge,
                "points": value,
                "first_blood": first_blood,
            },
        )
        if first_blood:
            _notify(settings, f"First blood on {chal_title} by {team_name}")

        return SubmissionOut(
            correct=True,
            points=value,
            message="first blood" if first_blood else "correct",
            first_blood=first_blood,
        )

    @app.get("/scoreboard", tags=["competition"], dependencies=[ready])
    def scoreboard(request: Request) -> dict:
        # Two deliberately injectable faults, both off by default. They exist
        # so that lab sheet 5 has an error budget to spend (Part C) and a canary
        # analysis has something to reject. See .env.example.
        if settings.slow_scoreboard_ms > 0:
            time.sleep(settings.slow_scoreboard_ms / 1000.0)
        if settings.error_rate > 0 and random.random() < settings.error_rate:
            log.error("injected failure", extra={"error_rate": settings.error_rate})
            raise HTTPException(status_code=500, detail="scoreboard unavailable")

        with db.session_scope() as s:
            rows = s.execute(
                select(Team.name, Submission.points, Submission.submitted_at)
                .join(Submission, Submission.team_id == Team.id, isouter=True)
                .where((Submission.correct.is_(True)) | (Submission.id.is_(None)))
            ).all()
            names = s.scalars(select(Team.name)).all()

        per_team: dict[str, list[SolveRecord]] = {n: [] for n in names}
        for name, points, at in rows:
            if points is None or at is None:
                continue
            per_team[name].append(
                SolveRecord(team=name, challenge="", points=points, at=at)
            )

        standings = rank_teams(per_team)
        return {
            "standings": [
                {
                    "rank": st.rank,
                    "team": st.team,
                    "points": st.points,
                    "solves": st.solves,
                    "last_solve": st.last_solve.isoformat() if st.last_solve else None,
                }
                for st in standings
            ],
            "teams": len(standings),
        }

    @app.post("/admin/reset", tags=["admin"], dependencies=[admin, ready])
    def admin_reset() -> dict:
        with db.session_scope() as s:
            s.execute(delete(Submission))
            s.execute(delete(Team))
        metrics.TEAMS.set(0)
        log.warning("competition reset")
        return {"reset": True}

    @app.post("/admin/teams/import", tags=["admin"], dependencies=[admin, ready])
    async def admin_import(file: UploadFile = FileParam(...)) -> dict:
        """Bulk registration from a CSV with columns name,country."""
        raw = (await file.read()).decode("utf-8", errors="replace")
        reader = csv.DictReader(io.StringIO(raw))
        added, skipped = 0, 0
        with db.session_scope() as s:
            for record in reader:
                name = (record.get("name") or "").strip()
                if not name or s.scalar(select(Team).where(Team.name == name)):
                    skipped += 1
                    continue
                s.add(Team(name=name, country=(record.get("country") or "").strip()))
                added += 1
        with db.session_scope() as s:
            metrics.TEAMS.set(s.scalar(select(func.count()).select_from(Team)) or 0)
        log.info("bulk import", extra={"added": added, "skipped": skipped})
        return {"added": added, "skipped": skipped}


app = None  # populated by __main__ / the ASGI entry point below


def get_app() -> FastAPI:
    """ASGI factory. Used by `uvicorn scoreboard.app:get_app --factory`."""
    return create_app()
