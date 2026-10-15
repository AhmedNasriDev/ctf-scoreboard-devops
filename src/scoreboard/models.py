"""Database tables.

Three of them. A team registers, a challenge is loaded from YAML, and a
submission records one attempt -- correct or not. Keeping the incorrect
attempts is deliberate: it is what the submissions metric and the
`attempts` field report, and it is what a real scoreboard does.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator


def utcnow() -> datetime:
    """Timezone-aware UTC now.

    Never use datetime.utcnow(): it returns a naive object that claims to be
    local time, and the comparison bugs it causes surface only when the
    container runs in a different timezone from the laptop. Which, from lab sheet 3
    onwards, it does.
    """
    return datetime.now(UTC)


class UTCDateTime(TypeDecorator):
    """A timestamp that is in UTC on the way in and on the way out.

    SQLite has no timestamp type and silently drops the timezone, so the same
    code returns an aware datetime on Postgres and a naive one on SQLite.
    That is the worst kind of difference between environments: it does not
    fail, it just produces a wrong answer somewhere downstream, and only in
    one of them. This decorator removes the difference rather than asking
    everyone to remember it.
    """

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):  # noqa: ANN001, ANN201
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    def process_result_value(self, value, dialect):  # noqa: ANN001, ANN201
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)


class Base(DeclarativeBase):
    pass


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    country: Mapped[str] = mapped_column(String(64), default="")
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(timezone=True), default=utcnow
    )

    submissions: Mapped[list[Submission]] = relationship(
        back_populates="team", cascade="all, delete-orphan"
    )


class Challenge(Base):
    __tablename__ = "challenges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(128))
    category: Mapped[str] = mapped_column(String(32), index=True)
    base_points: Mapped[int] = mapped_column(Integer)
    min_points: Mapped[int] = mapped_column(Integer, default=50)
    decay_solves: Mapped[int] = mapped_column(Integer, default=10)
    # SHA-256 of the flag. The flag itself is never stored, so a dump of this
    # table does not give away the competition.
    flag_hash: Mapped[str] = mapped_column(String(64))

    submissions: Mapped[list[Submission]] = relationship(back_populates="challenge")


class Submission(Base):
    __tablename__ = "submissions"
    __table_args__ = (
        # A team may attempt a challenge as often as it likes but may only
        # *solve* it once, so the uniqueness is partial: it applies to the
        # correct rows only. Enforced in the database rather than in
        # application code, because two concurrent requests will otherwise
        # both pass an application-level check and both insert.
        Index(
            "uq_one_solve",
            "team_id",
            "challenge_id",
            unique=True,
            sqlite_where=text("correct = 1"),
            postgresql_where=text("correct"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), index=True)
    challenge_id: Mapped[int] = mapped_column(ForeignKey("challenges.id"), index=True)
    correct: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    points: Mapped[int] = mapped_column(Integer, default=0)
    submitted_at: Mapped[datetime] = mapped_column(
        UTCDateTime(timezone=True), default=utcnow, index=True
    )

    team: Mapped[Team] = relationship(back_populates="submissions")
    challenge: Mapped[Challenge] = relationship(back_populates="submissions")
