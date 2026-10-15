"""Prometheus instrumentation.

Five metrics. Three cover rate, errors and duration (lab sheet 5 reads the
request counter by hand); one counts flag submissions (a business signal);
one gauge is a property of the competition; one carries the build identity.

Note what is *not* here. There is no metric per team and none per challenge
slug: a label whose value comes from user input is how a metrics endpoint
turns into an out-of-memory incident. Challenge *category* is bounded and
small, so it is safe to use as a label; a team name is not.
"""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from starlette.requests import Request
from starlette.responses import Response

REGISTRY = CollectorRegistry()

REQUESTS = Counter(
    "scoreboard_http_requests_total",
    "HTTP requests handled, by route template, method and status class.",
    ["route", "method", "status"],
    registry=REGISTRY,
)

LATENCY = Histogram(
    "scoreboard_http_request_duration_seconds",
    "Wall-clock time to produce a response, by route template.",
    ["route"],
    # Buckets chosen around the latency objective this service is given in
    # chapter 7 (95 % of /scoreboard under 300 ms). Default buckets would put the
    # objective between two of them and make the quantile unusable.
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.2, 0.3, 0.5, 1.0, 2.5, 5.0),
    registry=REGISTRY,
)

SUBMISSIONS = Counter(
    "scoreboard_submissions_total",
    "Flag submissions, by challenge category and outcome.",
    ["category", "outcome"],
    registry=REGISTRY,
)

TEAMS = Gauge(
    "scoreboard_teams_registered",
    "Teams currently registered.",
    registry=REGISTRY,
)

BUILD = Gauge(
    "scoreboard_build_info",
    "Always 1. The build is carried in the labels.",
    ["version", "commit", "environment"],
    registry=REGISTRY,
)


def route_template(request: Request) -> str:
    """The route *pattern*, not the path.

    /teams/41 and /teams/42 must share a label value, otherwise every request
    creates a new time series. This is the single most common way a service
    takes down its own monitoring.
    """
    route = request.scope.get("route")
    path = getattr(route, "path", None)
    if path:
        return str(path)
    return "unmatched"


def status_class(code: int) -> str:
    return f"{code // 100}xx"


async def metrics_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        elapsed = time.perf_counter() - started
        template = route_template(request)
        LATENCY.labels(route=template).observe(elapsed)
        REQUESTS.labels(route=template, method=request.method, status="5xx").inc()
        raise

    elapsed = time.perf_counter() - started
    template = route_template(request)
    LATENCY.labels(route=template).observe(elapsed)
    REQUESTS.labels(
        route=template,
        method=request.method,
        status=status_class(response.status_code),
    ).inc()
    response.headers["x-response-time-ms"] = f"{elapsed * 1000:.1f}"
    return response


def render() -> Response:
    return Response(generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)
