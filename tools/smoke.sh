#!/usr/bin/env bash
# Exercise a running instance end to end.
#
#   ./tools/smoke.sh                      # localhost:8000
#   ./tools/smoke.sh scoreboard.local     # anywhere else
#   ADMIN_TOKEN=... ./tools/smoke.sh      # also tests the admin endpoints
#                                         # (and RESETS the competition)
#
# From lab sheet 3 onwards this is how you check that a deployment actually works,
# rather than that a pod reached the Running state. The two are not the same
# thing, and the difference is the subject of the readiness probe.
#
# Exits non-zero on the first failure, so it can be a pipeline gate.
set -euo pipefail

HOSTP="${1:-localhost:8000}"
BASE="http://${HOSTP}"
TEAM="smoke-$$"
FLAG='UEM9{read_the_banner}'
ADMIN_TOKEN="${ADMIN_TOKEN:-}"

pass() { printf '  \033[32mok\033[0m    %s\n' "$1"; }
die()  { printf '  \033[31mFAIL\033[0m  %s\n' "$1"; exit 1; }

req() { # req METHOD PATH [JSON]
  local m=$1 p=$2 body=${3:-}
  if [ -n "$body" ]; then
    curl -fsS -X "$m" "$BASE$p" -H 'content-type: application/json' -d "$body"
  else
    curl -fsS -X "$m" "$BASE$p"
  fi
}

code() { curl -s -o /dev/null -w '%{http_code}' "$@"; }

echo "smoke test against $BASE"

[ "$(code "$BASE/healthz")" = 200 ] || die "liveness"
pass "liveness"

[ "$(code "$BASE/readyz")" = 200 ] || die "readiness (is the database reachable?)"
pass "readiness"

VERSION=$(req GET /version)
echo "$VERSION" | grep -q '"commit"' || die "version"
pass "version   $(echo "$VERSION" | tr ',' '\n' | grep commit | cut -d'"' -f4)"

# Responses are captured before grep reads them. Piping curl straight into
# `grep -q` under `set -o pipefail` fails at random: grep exits at the first
# match, curl gets SIGPIPE writing the rest, and the pipeline reports an error.
METRICS=$(req GET /metrics) || die "metrics"
grep -q scoreboard_http_requests_total <<<"$METRICS" || die "metrics"
pass "metrics"

CHALLENGES=$(req GET /challenges) || die "challenge list"
grep -q warmup-banner <<<"$CHALLENGES" || die "challenge list"
grep -qi 'flag' <<<"$CHALLENGES" && die "challenge list leaks a flag"
pass "challenge list"

req POST /teams "{\"name\":\"$TEAM\"}" >/dev/null || die "register"
pass "register  $TEAM"

[ "$(code -X POST "$BASE/teams" -H 'content-type: application/json' \
      -d "{\"name\":\"$TEAM\"}")" = 409 ] || die "duplicate rejected"
pass "duplicate rejected"

OUT=$(req POST /submit \
  "{\"team\":\"$TEAM\",\"challenge\":\"warmup-banner\",\"flag\":\"$FLAG\"}")
echo "$OUT" | grep -q '"correct":true' || die "correct flag accepted"
pass "correct flag accepted"

OUT=$(req POST /submit \
  "{\"team\":\"$TEAM\",\"challenge\":\"carved-out\",\"flag\":\"UEM9{nope}\"}")
echo "$OUT" | grep -q '"correct":false' || die "wrong flag rejected"
pass "wrong flag rejected"

DETAIL=$(req GET "/teams/$TEAM") || die "team detail"
grep -q '"points"' <<<"$DETAIL" || die "team detail"
pass "team detail"

BOARD=$(req GET /scoreboard) || die "scoreboard (is ERROR_RATE set?)"
grep -q "$TEAM" <<<"$BOARD" || die "scoreboard"
pass "scoreboard"

[ "$(code -X POST "$BASE/admin/reset")" = 401 ] \
  || [ "$(code -X POST "$BASE/admin/reset")" = 503 ] \
  || die "admin refuses an unauthenticated request"
pass "admin refuses an unauthenticated request"

if [ -n "$ADMIN_TOKEN" ]; then
  [ "$(code -X POST "$BASE/admin/reset" -H "x-admin-token: $ADMIN_TOKEN")" = 200 ] \
    || die "admin reset with a token"
  pass "admin reset with a token"
fi

echo "all good"
