"""Run the service: `python -m scoreboard`.

In a container you would normally run uvicorn directly:

    uvicorn --factory scoreboard.app:get_app --host 0.0.0.0 --port 8000

Both forms install uvicorn's SIGTERM handler, so either one, started in
*exec form* (CMD ["...", "..."]), is PID 1 and stops cleanly in under a
second. What does NOT stop cleanly is a shell sitting in front of it as PID 1,
for example CMD ["sh", "-c", "python -m scoreboard; echo done"]: the shell
ignores SIGTERM, Docker waits the full grace period (10 s) and then kills it.
That is the comparison lab sheet 3 (Part C) asks you to measure.
"""

from __future__ import annotations

import uvicorn

from .config import Settings


def main() -> None:
    settings = Settings.from_env()
    uvicorn.run(
        "scoreboard.app:get_app",
        factory=True,
        host=settings.host,
        port=settings.port,
        log_config=None,  # we configure logging ourselves
    )


if __name__ == "__main__":
    main()
