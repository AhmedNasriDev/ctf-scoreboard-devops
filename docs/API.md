# API reference

A running instance has interactive documentation at `/docs`. The code
generates it. This file gives the same information, and you can read it
without starting anything.

All request and response bodies are JSON, except when this file says
otherwise. Every response has an `x-request-id` header. If you send your own
`x-request-id`, the response returns the same value. So one identifier can
follow a request through several services.

---

## Meta

### `GET /`
```json
{"service":"ctf-scoreboard","version":"1.0.0","docs":"/docs","scoreboard":"/scoreboard"}
```

### `GET /healthz`: liveness
Always `200 {"status":"ok"}` while the process can answer. This is true even
when the database is down, or was never reachable. It checks nothing outside
the process, **on purpose**. If it fails, the process is broken, and a restart
is the correct action.

### `GET /readyz`: readiness
`200 {"status":"ready","database":true}`. Or `503` with
`{"status":"degraded","database":false}` when the database is not reachable.

A restart of the container does not repair the database. So do not use this
endpoint for the liveness probe. When the readiness probe fails, Kubernetes
removes the instance from the load balancer, but lets it run. When the probe
succeeds again, the instance comes back automatically.

Imagine that the database was not reachable at start-up. Then each call to
`/readyz` tries to connect again. When it succeeds, it creates the tables and
loads the competition. So the instance becomes ready without a restart. Until
then, every data endpoint answers `503 {"detail":"database unavailable"}`.

### `GET /version`
```json
{"version":"1.0.0","commit":"a1b2c3d","built":"2026-10-11T09:14:02Z",
 "environment":"production","scoring_mode":"decay"}
```
`commit` comes from `BUILD_SHA`. The image build sets it to the commit that it
builds (lab sheet 3, Part E). Before that, its value is `dev`. During a
canary, it shows which version answered.

### `GET /metrics`
Metrics in the text format of Prometheus. There are five metrics:

| Metric | Type | Labels |
|---|---|---|
| `scoreboard_http_requests_total` | counter | `route`, `method`, `status` |
| `scoreboard_http_request_duration_seconds` | histogram | `route` |
| `scoreboard_submissions_total` | counter | `category`, `outcome` |
| `scoreboard_teams_registered` | gauge | — |
| `scoreboard_build_info` | gauge (always 1) | `version`, `commit`, `environment` |

`route` is the route *template* (`/teams/{name}`), never the real path.
`status` is the status *class*: `2xx`, `4xx` or `5xx`. The histogram buckets
are around 300 ms, because chapter 7 uses a latency objective of 300 ms. The
default buckets do not fit this value, so the quantile would be useless.

---

## The competition

### `GET /challenges`
```json
{"scoring_mode":"decay",
 "challenges":[
   {"slug":"the-long-game","title":"Patience is a side channel",
    "category":"crypto","base_points":500,"current_value":430,"solves":1}]}
```
`current_value` is the value for the *next* team that solves the challenge.
Flags and flag hashes never appear in this response. A test checks this.

### `POST /teams`
```json
{"name":"my-team","country":"DZ"}
```
`201` if it works. `409` if the name already exists. `422` if the name has
fewer than two characters.

### `GET /teams/{name}`
```json
{"team":"my-team","country":"DZ","points":600,"attempts":4,
 "solves":[{"challenge":"warmup-banner","points":100,
            "at":"2026-10-11T09:20:11+00:00"}]}
```
`attempts` counts every submission, correct or not. `404` if the team does not
exist. Times are always in UTC, with SQLite and with Postgres.

### `POST /submit`
```json
{"team":"my-team","challenge":"warmup-banner","flag":"UEM9{read_the_banner}"}
```

| Result | Status | Body |
|---|---|---|
| correct, first team | `200` | `{"correct":true,"points":500,"message":"first blood","first_blood":true}` |
| correct | `200` | `{"correct":true,"points":430,"message":"correct","first_blood":false}` |
| wrong | `200` | `{"correct":false,"points":0,"message":"incorrect flag","first_blood":false}` |
| already solved | `409` | `{"detail":"already solved"}` |
| team or challenge does not exist | `404` | `{"detail":"no such team"}` |

A wrong flag is **not** an error. The request is correct, and the result is
normal: `200` with `correct: false`. With `400` here, the error ratio of lab
sheet 5 would count normal play as failures.

Spaces at the start and at the end of the flag are removed. Upper and lower
case are not changed.

### `GET /scoreboard`
```json
{"teams":3,
 "standings":[{"rank":1,"team":"alpha","points":600,"solves":2,
               "last_solve":"2026-10-11T09:20:11+00:00"}]}
```
The ranking uses the points. When two teams have the same points, the team
that got there first is ranked higher. Then the name decides, so the order
does not change when you reload the page. Registered teams appear with zero
points before their first solve. An empty competition returns
`{"standings":[],"teams":0}`, not an error.

`ERROR_RATE` and `SLOW_SCOREBOARD_MS` act on this endpoint.

---

## Administration

Both endpoints need the header `x-admin-token`. If `ADMIN_TOKEN` is not set,
the endpoints return `503` for everybody, even with a correct token. A service
with no configured administrator has no administrator. The comparison of the
token takes the same time for every value. So an attacker cannot find the
token one character at a time by measuring the response time.

### `POST /admin/reset`
Deletes every team and every submission. `200 {"reset":true}`.

### `POST /admin/teams/import`
`multipart/form-data` with a field `file`: a CSV file with the columns
`name,country`. Other columns are ignored.

```bash
curl -X POST localhost:8000/admin/teams/import \
     -H "x-admin-token: $ADMIN_TOKEN" -F 'file=@teams.csv'
```
`200 {"added":12,"skipped":1}`. Names that already exist are skipped, not
replaced.

An upload larger than 1 MB goes to a temporary file. So this is the only
request that needs a writable `/tmp`. Without it, the answer is `400`.
`make big-csv` creates such a file, for an optional test after lab sheet 3,
Part B.
