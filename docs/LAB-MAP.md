# What each lab sheet uses

Read the line of your lab sheet before you start it. Each lab sheet takes
about one hour and has five exercises. The application does not change between
lab sheets. What changes is what you build around it.

Are you new to Linux or to the command line? `docs/STUDENT-GUIDE.md` explains
every step of every lab sheet.

| Lab sheet | Title | Course chapters |
|---|---|---|
| 1 | Source control management | 1 |
| 2 | Continuous integration | 2 |
| 3 | Containers | 3 |
| 4 | Kubernetes | 4 (5 at home) |
| 5 | GitOps, error budgets and a canary | 6, 7 |
| 6 | Supply chain and measurement | 8, 9, 10 |

---

## Lab sheet 1: Source control

**Uses:** the repository itself, `.gitignore`, `src/scoreboard/scoring.py`,
`data/challenges.yaml`.

- The folder has exactly two files whose names start with a dot:
  `.gitignore` and `.env.example`. To copy both, use
  `cp -r .../ctf-scoreboard/. .`.
- `.gitignore` already excludes `.env`, `*.pem`, `*.key`, `data/*.db`, the
  virtual environment and the caches. It also excludes `gitleaks-report.json`.
  Why? A scan report contains the secrets that it found, in clear text.
- `scoring.py` uses only the Python standard library. So a one-line Python
  check can be the test for `git bisect`, with nothing installed.
- `data/challenges.yaml` gives the conflict exercise one line to change:
  `the-long-game`, `points: 500`.
- In Part D, you commit the secret on a branch. You delete this branch before
  you push. So the secret never reaches GitHub.

## Lab sheet 2: Continuous integration

**Uses:** `tests/`, `requirements*.txt`, `pyproject.toml`, `tools/seed.py`.

- 73 tests, about 3 seconds, coverage about 86 %. So the gate of 70 % passes.
- The tests import the *installed* package. There is no
  `pythonpath = ["src"]` in `pyproject.toml`. Without `pip install -e .`, the
  pipeline fails with `ModuleNotFoundError` (Part C).
- The pipeline runs on pull requests and on pushes to `main`. A push to
  another branch runs nothing, until you open a pull request.
- `make lint` prints nothing when the code is clean.
- `tools/seed.py --team <name> --commit` adds four defects. It chooses one of
  six versions. The four defects are: two failing tests, one fake credential,
  one dependency with a known vulnerability. The gates have
  `if: ${{ !cancelled() }}`, so one run shows all four. The script makes its
  commits with `--no-verify`.
- `pip-audit` prints identifiers like `PYSEC-…`. With `--aliases`, it also
  prints `GHSA-…` and `CVE-…`. `pip show <name>` (the line `Required-by`)
  helps you see if a dependency is direct or transitive.

## Lab sheet 3: Containers

**Uses:** `pyproject.toml`, `requirements.txt`, `data/`, `HOST`, `PORT`,
`BUILD_SHA`, `/version`, `tools/smoke.sh`.

- The runtime image does not need pytest, ruff or pip-audit. This is why there
  are two requirements files.
- The service listens on `0.0.0.0`. It writes only to its database folder. It
  never needs root. The data folder must belong to UID 10001
  (`COPY --chown=10001:10001`). In `docker run`, it is a named volume.
- The layer cache of Docker uses the *content* of the files. So change one
  byte, not only the date of the file.
- `uvicorn` in exec form stops in less than one second. With a shell in front
  of it (`sh -c '...; echo exited'`), it takes the full grace period of
  10 seconds.
- `BUILD_SHA` is set during the build. `/version` shows it as `commit`.
- Optional: `make big-csv` creates the only request that needs `/tmp`.

## Lab sheet 4: Kubernetes

**Uses:** `/healthz`, `/readyz`, `ADMIN_TOKEN`, `DATABASE_URL`,
`tools/smoke.sh`.

- `/healthz` is for the liveness probe. It checks nothing outside the process.
  `/readyz` is for the readiness probe. It checks the database.
- With a `DATABASE_URL` that cannot work, the pod stays `Running` with
  `READY 0/1` and `RESTARTS 0`. It logs `database not reachable`. It never
  joins the Service. During a rolling update, the old pod keeps working. When
  the liveness probe reads `/readyz`, the restarts start.
- The admin token comes from a Secret that you create with `kubectl`. No
  secret value is in a committed file.
- `cluster/kind.yaml` is outside `k8s/`. The folder `k8s/` contains only what
  runs in the cluster. Lab sheet 5 needs this.

## Lab sheet 5: GitOps, error budgets and a canary

**Uses:** `ERROR_RATE`, `SCORING_MODE`, `/metrics`, `/version`.

- Argo CD follows the `deploy` branch, folder `k8s/`. `main` stays protected.
- With `ERROR_RATE=0.2`, about one `/scoreboard` request in five returns 500.
  `/metrics` counts them in `scoreboard_http_requests_total`
  (`status="5xx"`). It counts for each pod separately. With several replicas,
  one `curl` sees one pod only.
- With `SCORING_MODE=static`, the canary gives different answers. `/version`
  shows `scoring_mode`, so you know which version answered.

## Lab sheet 6: Supply chain and measurement

**Uses:** `requirements.txt`, the image of lab sheet 3, the history of `main`
and `deploy`.

- Seven direct dependencies. Each one needs several other packages. Count the
  direct ones with `grep -cvE '^\s*(#|$)' requirements.txt`. (`wc -l` also
  counts the comments.)
- `BUILD_SHA` links a running instance to a commit. The attestation links the
  image to the workflow run that built it.
- The DORA numbers come from two places: the `deploy:` commits and the reverts
  on the `deploy` branch, and the pipeline runs on `main`.

---

## Tools for each lab sheet

All tools are free. The install commands are in `docs/STUDENT-GUIDE.md`.
Versions are those of October 2026.

| Lab | Tool | Note |
|---|---|---|
| 1 | git, Python 3.12 with `venv`, make, curl, unzip | Ubuntu packages |
| 1 | gitleaks 8.30 | program downloaded from GitHub |
| 1 | GitHub account, GitHub CLI `gh` 2.50+ | the repository must be **public**; `gh` also manages your login for `git push` |
| 2 | GitHub Actions | free for public repositories |
| 3 | Docker Engine with buildx | your user must be in the `docker` group |
| 3 | Trivy 0.75 | runs as a container image, nothing to install; a fixed version, never `latest` |
| 4 | kind 0.33, kubectl | programs downloaded from GitHub; about 4 GB of free memory |
| 4 (at home) | Terraform 1.16 or OpenTofu | optional part |
| 5 | Argo CD | installed in the cluster with `kubectl` |
| 6 | syft 1.54, grype 0.120, jq | programs downloaded from GitHub; grype downloads its database the first time |
