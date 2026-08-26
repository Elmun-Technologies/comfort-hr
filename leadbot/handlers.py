"""Suhbat oqimi: savol-javob, tekshiruv, guruhga yuborish."""

from __future__ import annotations

import logging
import re
from datetime import UTC, datetime

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from leadbot import texts
from leadbot.config import LeadBotSettings, get_leadbot_settings
from leadbot.keyboards import CONTACT_KB, REMOVE_KB, YES_NO_KB
from leadbot.qualify import Answers, Verdict, qualify
from leadbot.states import Application
from leadbot.storage import add_application, build_report

logger = logging.getLogger(__name__)

router = Router(name="leadbot")

PHONE_RE = re.compile(r"^\+?\d{9,13}$")


def _normalize_phone(raw: str) -> str | None:
    digits = re.sub(r"[^\d+]", "", raw)
    if not PHONE_RE.match(digits):
        return None
    if not digits.startswith("+"):
        digits = f"+{digits}" if len(digits) > 9 else f"+998{digits}"
    return digits


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    settings = get_leadbot_settings()
    if not settings.is_configured:
        await message.answer(texts.NOT_CONFIGURED)
        return

    await state.clear()
    await message.answer(texts.WELCOME, reply_markup=REMOVE_KB)
    await message.answer(texts.ASK_FULL_NAME)
    await state.set_state(Application.full_name)


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(texts.CANCELLED, reply_markup=REMOVE_KB)


@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    """Analitika hisoboti — faqat guruh chatida ishlaydi."""
    settings = get_leadbot_settings()
    if message.chat.id != settings.lead_group_chat_id:
        await message.answer(texts.STATS_GROUP_ONLY)
        return
    try:
        report = build_report(settings.lead_db_path, settings.timezone)
    except Exception:  # noqa: BLE001
        logger.exception("Analitika hisobotini tuzishda xato")
        await message.answer(texts.STATS_ERROR)
        return
    await message.answer(report, parse_mode="HTML")


@router.message(Application.full_name, F.text)
async def on_full_name(message: Message, state: FSMContext) -> None:
    full_name = message.text.strip()
    if len(full_name) < 3:
        await message.answer(texts.ASK_FULL_NAME)
        return
    await state.update_data(full_name=full_name)
    await message.answer(texts.ASK_AGE)
    await state.set_state(Application.age)


@router.message(Application.age, F.text)
async def on_age(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    if not text.isdigit() or not (10 <= int(text) <= 80):
        await message.answer(texts.ASK_AGE_INVALID)
        return
    await state.update_data(age=int(text))
    await message.answer(texts.ASK_CITY, reply_markup=YES_NO_KB)
    await state.set_state(Application.city)


@router.callback_query(Application.city, F.data.in_({"yes", "no"}))
async def on_city(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(lives_in_city=callback.data == "yes")
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(texts.ASK_PHONE, reply_markup=CONTACT_KB)
    await state.set_state(Application.phone)
    await callback.answer()


@router.message(Application.phone, F.contact)
async def on_phone_contact(message: Message, state: FSMContext) -> None:
    phone = _normalize_phone(message.contact.phone_number)
    if phone is None:
        await message.answer(texts.ASK_PHONE_INVALID, reply_markup=CONTACT_KB)
        return
    await state.update_data(phone=phone)
    await message.answer(texts.ASK_SCHEDULE, reply_markup=YES_NO_KB)
    await state.set_state(Application.schedule)


@router.message(Application.phone, F.text)
async def on_phone_text(message: Message, state: FSMContext) -> None:
    phone = _normalize_phone(message.text)
    if phone is None:
        await message.answer(texts.ASK_PHONE_INVALID, reply_markup=CONTACT_KB)
        return
    await state.update_data(phone=phone)
    await message.answer(texts.ASK_SCHEDULE, reply_markup=YES_NO_KB)
    await state.set_state(Application.schedule)


@router.callback_query(Application.schedule, F.data.in_({"yes", "no"}))
async def on_schedule(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(accepts_schedule=callback.data == "yes")
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer()

    data = await state.get_data()
    settings = get_leadbot_settings()
    answers = Answers(
        full_name=data["full_name"],
        age=data["age"],
        lives_in_city=data["lives_in_city"],
        phone=data["phone"],
        accepts_schedule=data["accepts_schedule"],
    )
    verdict = qualify(
        answers,
        min_age=settings.lead_min_age,
        max_age=settings.lead_max_age,
        required_city=settings.lead_required_city,
    )

    if verdict.is_qualified:
        await callback.message.answer(
            texts.RESULT_QUALIFIED.format(name=answers.full_name), reply_markup=REMOVE_KB
        )
    else:
        reasons = "\n".join(f"• {reason}" for reason in verdict.reasons)
        await callback.message.answer(
            texts.RESULT_NOT_QUALIFIED.format(name=answers.full_name, reasons=reasons),
            reply_markup=REMOVE_KB,
        )

    # Arizani analitika bazasiga saqlash
    try:
        add_application(settings.lead_db_path, answers, verdict)
    except Exception:  # noqa: BLE001
        logger.exception("Arizani bazaga saqlashda xato")

    await _notify_group(callback, answers, verdict, settings)
    await state.clear()


async def _notify_group(
    callback: CallbackQuery, answers: Answers, verdict: Verdict, settings: LeadBotSettings
) -> None:
    if not settings.lead_group_chat_id:
        return

    user = callback.from_user
    username = f"@{user.username}" if user.username else "—"
    header = texts.GROUP_HEADER_QUALIFIED if verdict.is_qualified else texts.GROUP_HEADER_NOT_QUALIFIED
    now = datetime.now(UTC).strftime("%d.%m.%Y %H:%M UTC")
    lives_label = "Ha" if answers.lives_in_city else "Yo'q"
    schedule_label = "Ha" if answers.accepts_schedule else "Yo'q"

    lines = [
        header,
        "",
        f"👤 Ism: {answers.full_name}",
        f"🎂 Yosh: {answers.age}",
        f"🏙 Toshkentda yashaydi: {lives_label}",
        f"📞 Telefon: {answers.phone}",
        f"⏰ Grafikga rozi: {schedule_label}",
        f"💬 Telegram: {username} (id: <code>{user.id}</code>)",
        f"🕓 Vaqt: {now}",
    ]
    if verdict.reasons:
        lines.append("")
        lines.append("Sabab(lar):")
        lines.extend(f"• {reason}" for reason in verdict.reasons)

    try:
        await callback.bot.send_message(
            settings.lead_group_chat_id, "\n".join(lines), parse_mode="HTML"
        )
    except Exception:  # noqa: BLE001
        logger.exception("Guruhga xabar yuborib bo'lmadi (chat_id=%s)", settings.lead_group_chat_id)
