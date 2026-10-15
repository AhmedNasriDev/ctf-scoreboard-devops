#!/usr/bin/env python3
"""Print a team-import CSV larger than 1 MB.

    python3 tools/big_csv.py > big-teams.csv      (or: make big-csv)

Why it exists. The service writes nothing to disk except its database --
with one exception: a multipart upload larger than 1 MB is spooled to a
temporary file. So with a read-only root filesystem and no writable /tmp,
every ordinary request still works and only this one fails (HTTP 400).

Use it to see what a missing writable /tmp breaks (an optional experiment
after lab sheet 3, Part B: run without --tmpfs /tmp):

    curl -s -o /dev/null -w '%{http_code}\\n' -H "x-admin-token: $ADMIN_TOKEN" \\
         -F file=@big-teams.csv localhost:8000/admin/teams/import

Expect 200 with /tmp mounted and 400 without it. The CSV registers 1 200
teams named big-00000 ... big-01199; reset the competition afterwards.
"""

from __future__ import annotations

ROWS = 1200
PADDING = "x" * 1000  # an ignored third column, to pass 1 MB with few rows


def main() -> None:
    print("name,country,notes")
    for i in range(ROWS):
        print(f"big-{i:05d},DZ,{PADDING}")


if __name__ == "__main__":
    main()
