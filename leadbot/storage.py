"""Arizalarni SQLite bazaga saqlash va analitika hisobotlarini tuzish.

Baza fayli `LEAD_DB_PATH` (default: ./data/leadbot.db) da joylashadi. Yozuvlar
har bir ariza topshirilganda `add_application` orqali qo'shiladi, `/stats`
buyrug'i esa `build_report` orqali guruhga umumiy statistika chiqaradi.
"""

from __future__ import annotations

import os
import sqlite3
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from leadbot.qualify import Answers, Verdict

REJECT_LABELS: dict[str, str] = {
    "age": "Yosh chegarasidan tashqari",
    "city": "Toshkentda yashamaydi",
    "schedule": "Grafikka rozi emas",
}


def _connect(db_path: str) -> sqlite3.Connection:
    directory = os.path.dirname(os.path.abspath(db_path))
    os.makedirs(directory, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str) -> None:
    """Agar baza bo'lmasa, jadvalni yaratadi."""
    conn = _connect(db_path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                age INTEGER NOT NULL,
                lives_in_city INTEGER NOT NULL,
                phone TEXT NOT NULL,
                accepts_schedule INTEGER NOT NULL,
                is_qualified INTEGER NOT NULL,
                reject_codes TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
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
                full_name, age, lives_in_city, phone, accepts_schedule,
                is_qualified, reject_codes, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                answers.full_name,
                answers.age,
                int(answers.lives_in_city),
                answers.phone,
                int(answers.accepts_schedule),
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


# /stats hisobotida ko'rsatiladigan so'nggi arizalar soni
RECENT_LIMIT = 10
# Har bir nomni shu uzunlikdan uzun bo'lsa qisqartiramiz (Telegram xabar limitidan
# himoya — o'nlab uzun ismlar ham hisobotni 4096 belgidan oshirib yubormasligi uchun)
MAX_DISPLAY_NAME_LENGTH = 40


def _truncate(name: str, limit: int = MAX_DISPLAY_NAME_LENGTH) -> str:
    return name if len(name) <= limit else name[: limit - 1] + "…"


def build_report(db_path: str, tz: ZoneInfo) -> str:
    """Umumiy analitika hisobotini (matn) qaytaradi.

    Butun jadvalni Python'ga yuklamaslik uchun jamlanmalar SQL orqali
    hisoblanadi, so'nggi arizalar esa `LIMIT`li so'rov bilan olinadi.
    """
    conn = _connect(db_path)
    try:
        total = int(conn.execute("SELECT COUNT(*) FROM applications").fetchone()[0])
        if total == 0:
            return "📊 <b>Analitika</b>\n\nHali hech qanday ariza topshirilmagan."

        qualified = int(
            conn.execute(
                "SELECT COUNT(*) FROM applications WHERE is_qualified = 1"
            ).fetchone()[0]
        )
        rejected = total - qualified

        # Bugungi kunni mahalliy vaqt mintaqasida hisoblab, UTC chegaralarga
        # o'tkazamiz — created_at ustuni doim UTC ISO satr sifatida saqlanadi,
        # shu format lug'aviy taqqoslashda ham xronologik tartibga mos keladi.
        now_local = datetime.now(tz)
        start_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
        end_local = start_local + timedelta(days=1)
        today = int(
            conn.execute(
                "SELECT COUNT(*) FROM applications WHERE created_at >= ? AND created_at < ?",
                (start_local.astimezone(UTC).isoformat(), end_local.astimezone(UTC).isoformat()),
            ).fetchone()[0]
        )

        # Reject sabablari bo'yicha taqsimot — bog'langan qiymatlar bilan
        # chegaralangan (LIKE) so'rovlar, to'liq jadval o'qilmaydi
        reject_counts: dict[str, int] = {}
        for code in REJECT_LABELS:
            cnt = int(
                conn.execute(
                    "SELECT COUNT(*) FROM applications "
                    "WHERE (',' || reject_codes || ',') LIKE ('%,' || ? || ',%')",
                    (code,),
                ).fetchone()[0]
            )
            if cnt:
                reject_counts[code] = cnt

        recent_rows = conn.execute(
            "SELECT full_name, age, is_qualified FROM applications "
            "ORDER BY id DESC LIMIT ?",
            (RECENT_LIMIT,),
        ).fetchall()
    finally:
        conn.close()

    recent_lines = [
        f"{'🟢' if r['is_qualified'] else '🔴'} {_truncate(r['full_name'])} — {r['age']} yosh"
        for r in recent_rows
    ]

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
