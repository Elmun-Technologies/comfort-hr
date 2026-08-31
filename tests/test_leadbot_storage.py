"""leadbot.storage uchun testlar."""

from __future__ import annotations

import os
import tempfile
from zoneinfo import ZoneInfo

from leadbot.qualify import Answers, qualify
from leadbot.storage import add_application, build_report, count_applications, init_db


def _answers(**overrides: object) -> Answers:
    base = {
        "full_name": "Aliyev Vali",
        "age": 22,
        "lives_in_city": True,
        "phone": "+998901234567",
        "accepts_schedule": True,
    }
    base.update(overrides)
    return Answers(**base)


def _tmp_db() -> str:
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.remove(path)
    return path


def test_init_db_creates_table_and_counts_empty() -> None:
    path = _tmp_db()
    init_db(path)
    assert count_applications(path) == 0


def test_add_and_count_applications() -> None:
    path = _tmp_db()
    init_db(path)
    add_application(path, _answers(), qualify(_answers(), min_age=18, max_age=25, required_city="Toshkent"))
    add_application(path, _answers(age=30), qualify(_answers(age=30), min_age=18, max_age=25, required_city="Toshkent"))
    assert count_applications(path) == 2


def test_build_report_empty_db() -> None:
    path = _tmp_db()
    init_db(path)

    report = build_report(path, ZoneInfo("Asia/Tashkent"))
    assert "Hali hech qanday ariza topshirilmagan" in report


def test_build_report_shows_totals_and_reasons() -> None:
    path = _tmp_db()
    init_db(path)

    # Mos kelgan
    ok = qualify(_answers(), min_age=18, max_age=25, required_city="Toshkent")
    add_application(path, _answers(), ok)
    # Yosh + shahar sababi bilan rad
    bad = qualify(
        _answers(age=40, lives_in_city=False),
        min_age=18,
        max_age=25,
        required_city="Toshkent",
    )
    add_application(path, _answers(age=40, lives_in_city=False), bad)

    report = build_report(path, ZoneInfo("Asia/Tashkent"))
    plain = report.replace("<b>", "").replace("</b>", "")
    assert "Jami arizalar: 2" in plain
    assert "Mos kelgan: 1" in plain
    assert "Mos kelmagan: 1" in plain
    assert "Yosh chegarasidan tashqari" in report
    assert "Toshkentda yashamaydi" in report


def test_recent_list_is_limited_to_ten() -> None:
    path = _tmp_db()
    init_db(path)
    for i in range(15):
        answers = _answers(full_name=f"Nomzod {i}")
        add_application(path, answers, qualify(answers, min_age=18, max_age=25, required_city="Toshkent"))

    report = build_report(path, ZoneInfo("Asia/Tashkent"))
    assert "Jami arizalar: 15" in report.replace("<b>", "").replace("</b>", "")
    # Faqat oxirgi 10 tasi ro'yxatda, eng yangisi (Nomzod 14) birinchi bo'lishi kerak
    assert report.count("Nomzod") == 10
    assert "Nomzod 14" in report
    assert "Nomzod 0" not in report


def test_long_names_are_truncated_in_report() -> None:
    path = _tmp_db()
    init_db(path)
    long_name = "A" * 80
    answers = _answers(full_name=long_name)
    add_application(path, answers, qualify(answers, min_age=18, max_age=25, required_city="Toshkent"))

    report = build_report(path, ZoneInfo("Asia/Tashkent"))
    assert long_name not in report
    assert "A" * 39 + "…" in report
    # Hisobot Telegram sendMessage limitidan (4096) ancha past bo'lishi kerak
    assert len(report) < 2000
