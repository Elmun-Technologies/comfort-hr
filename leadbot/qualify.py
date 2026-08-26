"""Nomzodning talablarga mosligini tekshiruvchi sof mantiq (UI'dan mustaqil)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Answers:
    full_name: str
    age: int
    lives_in_city: bool
    phone: str
    accepts_schedule: bool


@dataclass(frozen=True)
class Verdict:
    is_qualified: bool
    reasons: list[str]
    reject_codes: tuple[str, ...] = ()


def qualify(answers: Answers, *, min_age: int, max_age: int, required_city: str) -> Verdict:
    """Javoblarni vakansiya talablari bilan solishtiradi."""
    reasons: list[str] = []
    codes: list[str] = []

    if not (min_age <= answers.age <= max_age):
        reasons.append(f"Yosh chegarasi: {min_age}-{max_age} (siz: {answers.age})")
        codes.append("age")

    if not answers.lives_in_city:
        reasons.append(f"Doimiy {required_city}da istiqomat qilish talab etiladi (yotoqxona yo'q)")
        codes.append("city")

    if not answers.accepts_schedule:
        reasons.append("Belgilangan ish grafigiga rozilik talab etiladi")
        codes.append("schedule")

    return Verdict(is_qualified=not reasons, reasons=reasons, reject_codes=tuple(codes))
