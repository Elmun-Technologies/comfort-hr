"""Arizalarni SQLite bazaga saqlash va analitika hisobotlarini tuzish.

Baza fayli `LEAD_DB_PATH` (default: ./data/leadbot.db) da joylashadi. Yozuvlar
har bir ariza topshirilganda `add_application` orqali qo'shiladi, `/stats`
buyrug'i esa `build_report` orqali guruhga umumiy statistika chiqaradi.
"""

from __future__ import annotations

import os
import sqlite3
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from leadbot.qualify import Answers, Verdict

REJECT_LABELS: dict[str, str] = {
    "age": "Yosh chegarasidan tashqari",
    "city": "Toshkentda yashamaydi",
}


def _connect(db_path: str) -> sqlite3.Connection:
    directory = os.path.dirname(os.path.abspath(db_path))
    os.makedirs(directory, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_new_columns(conn: sqlite3.Connection) -> None:
    """Mavjud bazaga yangi ustunlarni qo'shadi (migration)."""
    cur = conn.execute("PRAGMA table_info(applications)")
    existing = {row["name"] for row in cur.fetchall()}
    if "gender" not in existing:
        conn.execute("ALTER TABLE applications ADD COLUMN gender TEXT NOT NULL DEFAULT ''")
    if "experience" not in existing:
        conn.execute("ALTER TABLE applications ADD COLUMN experience TEXT NOT NULL DEFAULT ''")
    if "resume_info" not in existing:
        conn.execute("ALTER TABLE applications ADD COLUMN resume_info TEXT NOT NULL DEFAULT ''")


def init_db(db_path: str) -> None:
    """Agar baza bo'lmasa, jadvalni yaratadi."""
    conn = _connect(db_path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                gender TEXT NOT NULL DEFAULT '',
                age INTEGER NOT NULL,
                lives_in_city INTEGER NOT NULL,
                phone TEXT NOT NULL,
                experience TEXT NOT NULL DEFAULT '',
                resume_info TEXT NOT NULL DEFAULT '',
                is_qualified INTEGER NOT NULL,
                reject_codes TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        _ensure_new_columns(conn)
        conn.commit()
    finally:
        conn.close()


def add_application(
    db_path: str,
    answers: Answers,
    verdict: Verdict,
    *,
    created_at: datetime | None = None,
) -> None:
    """Bitta arizani bazaga yozadi (yangi nomzod har safar kelganda chaqiriladi)."""
    if created_at is None:
        created_at = datetime.now(UTC)
    codes = ",".join(verdict.reject_codes)
    conn = _connect(db_path)
    try:
        conn.execute(
            """
            INSERT INTO applications (
                full_name, gender, age, lives_in_city, phone,
                experience, resume_info,
                is_qualified, reject_codes, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                answers.full_name,
                answers.gender,
                answers.age,
                int(answers.lives_in_city),
                answers.phone,
                answers.experience,
                answers.resume_info,
                int(verdict.is_qualified),
                codes,
                created_at.isoformat(),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def count_applications(db_path: str) -> int:
    conn = _connect(db_path)
    try:
        cur = conn.execute("SELECT COUNT(*) FROM applications")
        return int(cur.fetchone()[0])
    finally:
        conn.close()


def _fetch_all(db_path: str) -> list[sqlite3.Row]:
    conn = _connect(db_path)
    try:
        cur = conn.execute("SELECT * FROM applications ORDER BY id DESC")
        return cur.fetchall()
    finally:
        conn.close()


def _parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


def build_report(db_path: str, tz: ZoneInfo) -> str:
    """Umumiy analitika hisobotini (matn) qaytaradi."""
    rows = _fetch_all(db_path)
    total = len(rows)
    if total == 0:
        return "📊 <b>Analitika</b>\n\nHali hech qanday ariza topshirilmagan."

    qualified = sum(1 for r in rows if r["is_qualified"])
    rejected = total - qualified
    now = datetime.now(tz)

    # Reject sabablari bo'yicha taqsimot
    reject_counts: dict[str, int] = {}
    for r in rows:
        codes = [c for c in (r["reject_codes"] or "").split(",") if c]
        for code in codes:
            reject_counts[code] = reject_counts.get(code, 0) + 1

    today = sum(
        1 for r in rows if _parse_dt(r["created_at"]).astimezone(tz).date() == now.date()
    )

    # Oxirgi 10 ta ariza (eng yangi birinchi)
    from leadbot.texts import GENDER_LABELS

    recent_lines = []
    for r in rows[:10]:
        mark = "🟢" if r["is_qualified"] else "🔴"
        gender = r["gender"] if "gender" in r.keys() else ""
        gender_label = GENDER_LABELS.get(gender, "")
        gender_str = f" ({gender_label})" if gender_label else ""
        recent_lines.append(f"{mark} {r['full_name']}{gender_str} — {r['age']} yosh")

    lines = [
        "📊 <b>ANALITIKA</b>\n",
        f"👥 <b>Jami arizalar:</b> {total}",
        f"✅ <b>Mos kelgan:</b> {qualified}",
        f"❌ <b>Mos kelmagan:</b> {rejected}",
        f"📅 <b>Bugun:</b> {today}",
        "",
    ]

    if reject_counts:
        lines.append("🚫 <b>Rad etish sabablari:</b>")
        for code, cnt in sorted(reject_counts.items(), key=lambda x: -x[1]):
            label = REJECT_LABELS.get(code, code)
            lines.append(f"• {label}: {cnt}")
        lines.append("")

    if recent_lines:
        lines.append("🕘 <b>Oxirgi 10 nomzod:</b>")
        lines.extend(recent_lines)

    return "\n".join(lines)
