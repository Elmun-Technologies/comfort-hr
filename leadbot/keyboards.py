"""Reply/inline klaviaturalar."""

from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

from leadbot.texts import BTN_NO, BTN_SHARE_CONTACT, BTN_YES

YES_NO_KB = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text=BTN_YES, callback_data="yes"),
            InlineKeyboardButton(text=BTN_NO, callback_data="no"),
        ]
    ]
)

CONTACT_KB = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text=BTN_SHARE_CONTACT, request_contact=True)]],
    resize_keyboard=True,
    one_time_keyboard=True,
)

REMOVE_KB = ReplyKeyboardRemove()
