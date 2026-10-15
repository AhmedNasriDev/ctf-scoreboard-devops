"""Loading the competition definition from YAML.

The challenges are data, not code, so they live in data/challenges.yaml and
are loaded at startup. In a cluster the file can be mounted from a ConfigMap,
and the point of this module becomes obvious: the same image serves a
different competition depending on what is mounted at CHALLENGES_FILE.

Note yaml.safe_load, never yaml.load or yaml.full_load. The unsafe loaders
construct arbitrary Python objects from the document, which means anyone who
can edit the file can run code in this process. Remember this when a
dependency scanner reports a PyYAML advisory at you in lab sheet 2.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import yaml


class ChallengeFileError(ValueError):
    """The challenge file is missing, unreadable or malformed."""


@dataclass(frozen=True)
class ChallengeDef:
    slug: str
    title: str
    category: str
    base_points: int
    min_points: int
    decay_solves: int
    flag_hash: str


def flag_hash(flag: str) -> str:
    """SHA-256 of a flag, lowercase hex.

    Flags are never stored, logged or returned. Only this hash is, so a dump
    of the database does not hand over the competition.
    """
    return hashlib.sha256(flag.strip().encode("utf-8")).hexdigest()


def _require(raw: dict, key: str, slug: str) -> object:
    if key not in raw:
        raise ChallengeFileError(f"challenge {slug!r}: missing required key {key!r}")
    return raw[key]


def parse(document: str) -> list[ChallengeDef]:
    """Parse the YAML text into challenge definitions.

    A challenge may carry either ``flag`` (hashed here) or ``flag_sha256``
    (already hashed, which is what you use when the file is in version
    control, as it is from lab sheet 1 onwards).
    """
    try:
        data = yaml.safe_load(document)
    except yaml.YAMLError as exc:
        raise ChallengeFileError(f"not valid YAML: {exc}") from exc

    if data is None:
        return []
    if not isinstance(data, dict) or "challenges" not in data:
        raise ChallengeFileError("top level must be a mapping with a 'challenges' key")

    entries = data["challenges"]
    if not isinstance(entries, list):
        raise ChallengeFileError("'challenges' must be a list")

    out: list[ChallengeDef] = []
    seen: set[str] = set()
    for raw in entries:
        if not isinstance(raw, dict):
            raise ChallengeFileError("each challenge must be a mapping")
        slug = str(_require(raw, "slug", "<unnamed>"))
        if slug in seen:
            raise ChallengeFileError(f"duplicate challenge slug {slug!r}")
        seen.add(slug)

        if "flag_sha256" in raw:
            digest = str(raw["flag_sha256"]).strip().lower()
            if len(digest) != 64:
                raise ChallengeFileError(
                    f"challenge {slug!r}: flag_sha256 must be 64 hex characters"
                )
        elif "flag" in raw:
            digest = flag_hash(str(raw["flag"]))
        else:
            raise ChallengeFileError(
                f"challenge {slug!r}: needs either 'flag' or 'flag_sha256'"
            )

        base = int(_require(raw, "points", slug))
        out.append(
            ChallengeDef(
                slug=slug,
                title=str(_require(raw, "title", slug)),
                category=str(raw.get("category", "misc")),
                base_points=base,
                min_points=int(raw.get("min_points", min(50, base))),
                decay_solves=int(raw.get("decay_solves", 10)),
                flag_hash=digest,
            )
        )
    return out


def load(path: str | Path) -> list[ChallengeDef]:
    p = Path(path)
    if not p.is_file():
        raise ChallengeFileError(f"challenge file not found: {p}")
    return parse(p.read_text(encoding="utf-8"))
