# CTF Scoreboard

A small scoreboard for a capture-the-flag (CTF) competition. Teams register and
submit flags. The scoreboard ranks the teams. A challenge is worth fewer points
when more teams solve it.

**You use this application in every lab session of the DevOps module.** You
put it in Git and give it a pipeline. You put it in a container and deploy it
to a cluster. You deliver it with GitOps, measure its errors and protect its
supply chain. The code is small on purpose: the lab work is about DevOps, not
about the code.

Read this file once, at the start of lab sheet 1. Each lab sheet takes about
one hour. **Are you new to Linux or to the command line?** Start with
`docs/STUDENT-GUIDE.md`. It explains every step of every lab sheet, from the
download of this folder to the end.

---

## Before lab sheet 1

You need these tools on your own computer:

| Tool | Version | How to check |
|---|---|---|
| Git | 2.30 or later | `git --version` |
| Python | **3.11 or later** (3.12 is best: the pipeline and the container use it) | `python3.12 --version` |
| `venv` support | Debian and Ubuntu install it separately: `sudo apt install python3.12-venv` | `python3.12 -m venv /tmp/t` |
| make, curl, unzip | any | `make --version` |
| gitleaks | 8.30 or later | `gitleaks version` |
| GitHub CLI `gh` | 2.50 or later | `gh --version` |

Each later lab sheet lists its own tools in the part *Before you start*. The
table at the end of `docs/LAB-MAP.md` lists all of them.
`docs/STUDENT-GUIDE.md` gives the exact commands to install them.

> **Use a public GitHub repository.** On a free GitHub account, three features
> work only on public repositories: branch protection (lab sheet 1), image
> downloads from `ghcr.io` without a password (lab sheets 3–4), and build
> attestations (lab sheet 6). Nothing in this repository is secret. The flags
> in `docs/FLAGS.md` are public on purpose.

---

## Quick start

```bash
make install                           # .venv with the pinned dependencies,
                                       # plus `pip install -e .` (see below)
make test                              # 73 tests, about 3 seconds
make lint                              # silent when clean
ADMIN_TOKEN=local-dev-token make run   # http://localhost:8000/docs
```

`make install` uses the first Python 3.11 or later that it finds. It prefers
3.12. To choose the version yourself, run `make install PY=python3.12`. You can
also do the same steps by hand:

```bash
python3.12 -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
pip install -e .                       # puts scoreboard/ on the path -- the
                                       # tests cannot import it without this
```

Then, in a second terminal:

```bash
curl -s localhost:8000/healthz
curl -s -X POST localhost:8000/teams \
     -H 'content-type: application/json' -d '{"name":"my-team"}'
curl -s -X POST localhost:8000/submit -H 'content-type: application/json' \
     -d '{"team":"my-team","challenge":"warmup-banner","flag":"UEM9{read_the_banner}"}'
curl -s localhost:8000/scoreboard
```

The flags of the demonstration competition are in `docs/FLAGS.md`.

`tools/smoke.sh` runs all these requests against any host and port, for
example `./tools/smoke.sh localhost:8080`. You use it from lab sheet 3. It
checks that a container or a deployment really *works*. A process that
*runs* does not always work. Be careful: if `ADMIN_TOKEN` is exported in your
shell, the smoke test also calls `/admin/reset`. This deletes the whole
competition.

---

## What is missing on purpose

There is **no `Dockerfile`, no `.dockerignore`, no `.github/workflows/`, no
Kubernetes manifest and no Argo CD application**. You write them. Each lab
sheet adds some of them to this same repository:

| Lab sheet | Course chapters | What you add |
|---|---|---|
| 1 | 1 | the public repository, with a merge, a bisect and a revert in its history; branch protection on `main` |
| 2 | 2 | `.github/workflows/ci.yml` (lint, tests with coverage, secret scan, dependency audit), as a required check; `docs/TP2_diagnosis.md` |
| 3 | 3 | `Dockerfile` (multi-stage, not root), `.dockerignore`, and an `image` job that pushes to `ghcr.io` |
| 4 | 4 (5 at home) | `cluster/kind.yaml`; `k8s/`: namespace, Deployment with three probes, limits and a strict security context, Service |
| 5 | 6, 7 | `cluster/argocd-app.yaml`, a `deploy` branch that Argo CD follows, an error-budget test and a canary, all as commits |
| 6 | 8, 9, 10 | an SBOM, a scan of the SBOM, a build attestation in the `image` job, the image deployed by digest, your DORA numbers |

Every lab sheet also asks for a file `docs/TP<n>_answers.md` with your
answers.

At the end, you have one repository. It goes from a commit to a running
service that you can observe and whose origin you can prove. You show this in
the oral exam.

---

## The design, and the reasons for it

Each decision below is on purpose. A lab sheet depends on each one. You must be
able to explain most of them.

**The configuration comes only from the environment.**
`src/scoreboard/config.py` reads every setting from an environment variable.
It keeps the settings in a frozen dataclass (an object that cannot change).
There is no file of local settings and no secret in the code. So the same image
runs on your laptop, in a cluster and in a canary.

**`/healthz` and `/readyz` are two different endpoints.**

- Liveness (`/healthz`) checks nothing outside the process. If it fails, the
  process is broken, and a restart helps.
- Readiness (`/readyz`) checks the database. If it fails, a restart does *not*
  help. The correct action is: remove the instance from the Service and let it
  run.

Many people use one endpoint for both. This is the most common Kubernetes
mistake. In lab sheet 4 (Part C), you make this mistake on purpose.

**The process does not stop when the database is not reachable.** At start-up,
the database may not be reachable. For example: Postgres is not ready yet, the
`DATABASE_URL` is wrong, or the container cannot write to the path. In that
case, the service still starts. `/healthz` answers 200. `/readyz` and all data
endpoints answer 503. The log says why. Each readiness probe tries again. When
the database becomes reachable, the service becomes ready alone, without a
restart. A `CHALLENGES_FILE` with errors is different: it is a configuration
error, and the process stops immediately.

**`/version` gives the commit of the build.** The image build writes it into
the image with `BUILD_SHA` (lab sheet 3, Part E). During a canary, this is how
you know which version answered you.

**The labels of `/metrics` use the route template, not the path.**
`/teams/alice` and `/teams/bob` have the same label: `/teams/{name}`. If a
label value comes from user input, each request creates a new time series.
This can break the monitoring system. For the same reason, there is no metric
for each team.

**Each log line is one JSON object, on stdout, with a request id.** A container
must not manage log files itself. To read the logs more easily, set
`LOG_FORMAT=text`.

**The scoring logic is pure.** `src/scoreboard/scoring.py` takes values and
returns values. It uses no database, no clock and no network. So it has the
most tests, and they run in milliseconds. So lab sheet 1 can also use it as a
test for `git bisect`, with nothing installed.

**Times are in UTC with both databases.** SQLite loses the time zone without
any warning. `models.UTCDateTime` adds it back. The same code must work the
same way on SQLite and on Postgres. A difference that appears in one
environment only is the most difficult kind of bug.

**The application writes to disk in one place only:** the SQLite database (by
default `./data/scoreboard.db`). There is one exception: a multipart upload
larger than 1 MB goes to a temporary file. So a read-only root filesystem works
with one writable mount for the database. Without `/tmp`, only a large
`/admin/teams/import` fails. (`make big-csv` creates such a file, for an
optional test after lab sheet 3.)

**You can switch on two faults.** `ERROR_RATE` makes `/scoreboard` fail for a
part of the requests. `SLOW_SCOREBOARD_MS` makes it slow. Both are off by
default. Lab sheet 5 (Part C) uses `ERROR_RATE` to spend an error budget on
purpose. `SLOW_SCOREBOARD_MS` is for a latency objective, if you want to try
one.

**`SCORING_MODE` changes the result, not only the speed.** A canary in mode
`static` really gives different scores from a stable version in mode `decay`.
So the canary of lab sheet 5 is a real test, not just a formality.

---

## Configuration

Each variable, its default value, and the first lab sheet that needs it. See
also `.env.example`.

| Variable | Default | First used in |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./data/scoreboard.db` | 4 (`sqlite:////data/scoreboard.db`, then a broken path in Part C) |
| `CHALLENGES_FILE` | `data/challenges.yaml` | optional (a ConfigMap can replace the file) |
| `ADMIN_TOKEN` | *not set*: admin endpoints return 503 | 3 (`-e ADMIN_TOKEN`), 4 (Secret) |
| `BUILD_SHA` | `dev` | 3 (written by the image build, read on `/version`) |
| `BUILD_TIME` | `unknown` | optional |
| `ENVIRONMENT` | `local` | optional; appears in `/version` and `scoreboard_build_info` |
| `SCORING_MODE` | `decay` (or `static`) | 5 (canary) |
| `ERROR_RATE` | `0.0` | 5 (error budget) |
| `SLOW_SCOREBOARD_MS` | `0` | optional (latency objective) |
| `WEBHOOK_URL` | empty: nothing is sent | optional |
| `HOST` / `PORT` | `0.0.0.0` / `8000` | 3 |
| `LOG_LEVEL` / `LOG_FORMAT` | `INFO` / `json` | any |

Without `ADMIN_TOKEN`, the admin endpoints are switched off. They are not open
to everybody. This is called *fail closed*: a service with no administrator is
safer than a service where anybody is the administrator.

The lab sheets use SQLite everywhere. The code also works with Postgres, but
the Postgres driver is not included. First add `psycopg[binary]` to
`requirements.txt`. If you do not, a `postgresql+psycopg` URL gives a service
that runs but is not ready, with `No module named 'psycopg'` in the log.

---

## The API

| | | |
|---|---|---|
| `GET` | `/` | service banner |
| `GET` | `/healthz` | liveness |
| `GET` | `/readyz` | readiness; 503 when the database is not reachable |
| `GET` | `/version` | version, commit, environment, scoring mode |
| `GET` | `/metrics` | metrics for Prometheus |
| `GET` | `/challenges` | the competition, with the current values. Never the flags |
| `POST` | `/teams` | register a team |
| `GET` | `/teams/{name}` | one team, its solves and its attempts |
| `POST` | `/submit` | submit a flag |
| `GET` | `/scoreboard` | the ranking |
| `POST` | `/admin/reset` | delete the whole competition (`x-admin-token`) |
| `POST` | `/admin/teams/import` | register many teams from a CSV file (`x-admin-token`) |

The interactive documentation is at `/docs`. The code generates it.
`docs/API.md` shows the exact requests and responses.

### Scoring

A challenge is worth `points` for the first team that solves it. In the
default mode, `decay`, its value then goes down in a straight line. It reaches
`min_points` after `decay_solves` solves, and stays there:

```
value(n) = base - (base - min) * (n - 1) // decay_solves     while decaying
value(n) = min                                               afterwards
```

`n` includes the team that solves now. So the first team always gets the full
value, and nobody gets less than the minimum. The ranking uses the total
points. When two teams have the same total, the team that reached it first is
ranked higher.

### The competition

The competition is in `data/challenges.yaml`. The flags are stored as SHA-256
hashes. So the file can be in Git without giving the answers. To add a
challenge, edit the file and restart. The loader updates what exists and adds
what is new. So loading the same file two times changes nothing.

---

## Development

```bash
make help          # every target
make test          # the suite
make cov           # with a coverage report (about 86 %)
make lint          # ruff check + format --check; silent when clean
make fmt           # fix what can be fixed
make audit         # pip-audit against requirements.txt
make run           # the service
make smoke         # curl every endpoint against a running instance
make big-csv       # a > 1 MB import file (optional /tmp experiment)
make clean
```

Before you open a pull request, `make lint test` must pass. From lab sheet 2,
your pipeline checks this for you.

### Files and folders

```
src/scoreboard/
  app.py             routes, request and response shapes, start-up
  scoring.py         pure scoring and ranking logic
  challenges.py      loading data/challenges.yaml
  models.py          the three tables
  db.py              engine, session, readiness ping, retry when unreachable
  metrics.py         Prometheus collectors and the middleware
  logging_setup.py   JSON logs and the request id
  config.py          the environment, read once
tests/               73 tests: scoring, loading, and the HTTP layer
data/challenges.yaml the competition
docs/                student guide, API reference, the flags, the lab map
tools/               smoke test, the lab sheet 2 seeding script, big_csv.py
.env.example         every setting, with its default
```

`docs/LAB-MAP.md` shows the files and endpoints that each lab sheet uses. It
also lists the tools for each lab sheet. Read the line of a lab sheet
*before* you start it.

### Problems and solutions

| What you see | Cause and solution |
|---|---|
| `make install`: *No Python 3.11+ found* | Install `python3.12`. On Ubuntu 22.04, it comes from the deadsnakes PPA. Or use the course virtual machine. |
| `ensurepip is not available` | Debian or Ubuntu: `sudo apt install python3.12-venv` |
| `pip install --user ...`: *externally-managed-environment* | Debian 12 and Ubuntu 23.04+ refuse pip for the whole system. Use `pipx install <tool>`, or install inside `.venv`. |
| `ModuleNotFoundError: No module named 'scoreboard'` in the tests | The package is not installed: `pip install -e .` (see lab sheet 2, Part C). |
| `permission denied ... docker.sock` | Your user is not in the `docker` group. Or you did not log out and in again after you were added. |
| `/readyz` answers 503, `/healthz` 200, the log says `unable to open database file` | The container user (UID 10001) cannot write to the database folder. Use `COPY --chown=10001:10001 data/ ./data/` in the runtime stage, and a named volume, not a bind mount of a host folder. |
| `/readyz` answers 503, `/healthz` 200, another reason | The database is not reachable. The log line `database not reachable` gives the reason. |

---

## About the fixed versions of dependencies

`requirements.txt` gives an exact version for each package (the versions are
*pinned*). `requirements-dev.txt` uses it and adds the development tools. Why
pin? A vulnerability scanner compares versions with its database. Without exact
versions, it has nothing to compare. It then reports "no problem" for packages
that nobody checked.

But pinned versions get old. New advisories appear for versions that were safe
when you chose them. So a file that passes the audit today can fail it next
year. `make audit` tells you. The solution is a newer pinned version, not
removing the pin. The versions in this repository passed the audit on
12 October 2026.

---

## Licence

MIT. See `LICENSE`. You may keep this repository and put it in your portfolio.
