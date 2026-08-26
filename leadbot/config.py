"""Lead-bot uchun mustaqil sozlamalar (.env orqali).

Bu bot asosiy HR nazorat botidan (app/) butunlay mustaqil ishlaydi — o'z tokeni,
o'z guruhi va o'z talab mezonlariga ega. amoCRM bilan bog'liq emas.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LeadBotSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # --- Telegram ---
    leadbot_token: str = Field(default="", alias="LEADBOT_TOKEN")
    # Natijalar yuboriladigan HR/sotuv guruhi. Guruh ID manfiy bo'ladi: -1001234567890
    lead_group_chat_id: int = Field(default=0, alias="LEAD_GROUP_CHAT_ID")

    # --- Talab mezonlari (Comfort tekstil: Sotuvchi/Dastavka yigitlar) ---
    lead_min_age: int = Field(default=18, alias="LEAD_MIN_AGE")
    lead_max_age: int = Field(default=25, alias="LEAD_MAX_AGE")
    lead_required_city: str = Field(default="Toshkent", alias="LEAD_REQUIRED_CITY")

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    @field_validator("lead_group_chat_id", mode="before")
    @classmethod
    def _parse_chat_id(cls, value: object) -> int:
        if value is None or value == "":
            return 0
        return int(value)

    @property
    def is_configured(self) -> bool:
        return bool(self.leadbot_token) and self.lead_group_chat_id != 0


@lru_cache
def get_leadbot_settings() -> LeadBotSettings:
    return LeadBotSettings()
