"""Bot matnlari (o'zbek tilida)."""

from __future__ import annotations

WELCOME = (
    "Assalomu alaykum! 👋\n\n"
    "<b>Comfort</b> — Sotuvchi/Dastavka yigit vakansiyasiga murojaat qilganingiz uchun rahmat.\n\n"
    "🧑🏻‍💼 Lavozim: Sotuvchi/Dastavka yigit\n"
    "💵 Oylik: 10 000 000 – 15 000 000 so'm\n"
    "⏰ Ish grafigi: 08:00–19:00, oyiga 1 kun dam\n"
    "📌 Manzil: Toshkent, O'rikzor bozori atrofida\n\n"
    "Talablarga mos kelasizmi — buni bilish uchun bir nechta savol beraman. "
    "Javoblaringiz to'g'ridan-to'g'ri HR bo'limiga yuboriladi."
)

ASK_FULL_NAME = "1️⃣ Ism va familiyangizni to'liq kiriting:"
ASK_FULL_NAME_INVALID = (
    "Ism va familiya 3 dan 80 belgigacha bo'lishi kerak. Iltimos, qaytadan kiriting:"
)
ASK_AGE = "2️⃣ Necha yoshdasiz? (faqat raqamda, masalan: 22)"
ASK_AGE_INVALID = "Iltimos, yoshingizni faqat raqamda kiriting (masalan: 22)."
ASK_CITY = "3️⃣ Doimiy Toshkent shahrida istiqomat qilasizmi? (Yotoqxona berilmaydi)"
ASK_PHONE = (
    "4️⃣ Telefon raqamingizni yuboring — pastdagi tugma orqali yoki qo'lda kiriting "
    "(masalan: +998901234567):"
)
ASK_PHONE_INVALID = "Telefon raqami noto'g'ri formatda. Masalan: +998901234567"
ASK_SCHEDULE = "5️⃣ Ish grafigi 08:00–19:00, oyiga 1 kun dam — shu grafikka rozimisiz?"

BTN_YES = "✅ Ha"
BTN_NO = "❌ Yo'q"
BTN_SHARE_CONTACT = "📱 Raqamni yuborish"

RESULT_QUALIFIED = (
    "✅ Rahmat, {name}!\n\n"
    "Siz vakansiya talablariga javob berasiz. Tez orada HR mutaxassisi siz bilan "
    "bog'lanadi.\n\n"
    "Kuting va telefoningizni yoningizda tuting 📞"
)

RESULT_NOT_QUALIFIED = (
    "Rahmat, {name}, ariza uchun!\n\n"
    "Afsuski, hozircha quyidagi sabab(lar)ga ko'ra ushbu vakansiya talablariga "
    "to'liq mos kelmaysiz:\n{reasons}\n\n"
    "Boshqa mos vakansiyalar bo'lsa, albatta siz bilan bog'lanamiz. E'tiboringiz uchun rahmat!"
)

CANCELLED = "Ariza bekor qilindi. Qaytadan boshlash uchun /start ni bosing."
ALREADY_SUBMITTED = (
    "Siz allaqachon ariza topshirgansiz. Qayta topshirish uchun /start ni bosing."
)
NOT_CONFIGURED = (
    "Bot hozircha sozlanmagan (LEADBOT_TOKEN / LEAD_GROUP_CHAT_ID). Administratorga murojaat qiling."
)

GROUP_HEADER_QUALIFIED = "🟢 <b>YANGI NOMZOD — MOS KELADI</b>"
GROUP_HEADER_NOT_QUALIFIED = "🔴 <b>YANGI NOMZOD — MOS KELMAYDI</b>"

STATS_GROUP_ONLY = (
    "📊 Analitikani faqat guruh chatida ko'rish mumkin. "
    "Guruhga /stats deb yozing."
)
STATS_ERROR = "Kechirasiz, analitika hisobotini tuzishda xato yuz berdi. Iltimos, keyinroq qayta urinib ko'ring."
