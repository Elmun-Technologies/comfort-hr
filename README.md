# Comfort HR — amoCRM jarayon nazorati boti

Sotuvchilar uchun Telegram bot: amoCRM'dagi har bir sotuv jarayonini avtomatik
nazorat qiladi, qoidabuzarliklarni (SLA, muddati o'tgan vazifa, qotib qolgan
lid va h.k.) aniqlaydi va tegishli xodimga, kechiksa — rahbariyatga xabar
beradi. Shuningdek sotuvchilarga target (reja) belgilash va bajarilishini
kuzatish imkonini beradi.

## Qanday ishlaydi

```
amoCRM  <──(API v4 / OAuth2)──  Sinxronizatsiya (har N daqiqada + webhook)
                                        │
                                        ▼
                                  Lokal baza (SQLite/PostgreSQL)
                                        │
                                        ▼
                              Qoidalar dvigateli (app/services/rules.py)
                                        │
                         ┌──────────────┴───────────────┐
                         ▼                               ▼
                 Sotuvchiga Telegram xabar      2 soatdan kech javobsiz →
                 (o'z vaqtida)                  rahbariyatga eskalatsiya
```

### Nazorat qilinadigan qoidalar

| Qoida | Tavsif | Sozlash (`.env`) |
|---|---|---|
| Birinchi javob SLA | Yangi lidga belgilangan vaqt ichida hech qanday harakat bo'lmasa | `RULE_FIRST_RESPONSE_MINUTES` |
| Vazifasiz lid | Ochiq lidda keyingi qadam bo'yicha vazifa yo'q | `RULE_LEAD_WITHOUT_TASK_HOURS` |
| Muddati o'tgan vazifa | amoCRM vazifasi muddati o'tib, hali yopilmagan | — |
| Bosqichda qotib qolish | Lid bir bosqichda uzoq turib qolgan | `RULE_STATUS_STUCK_DAYS` (yoki bosqichga xos `max_days`) |
| Harakatsiz lid | Lidda umuman hech qanday yangilanish yo'q | `RULE_NO_ACTIVITY_DAYS` |
| Ortiqcha yuklama | Sotuvchida ochiq lidlar soni limitdan oshgan | `RULE_MAX_OPEN_LEADS` |
| Target sur'atidan orqada qolish | Reja bajarilishi kunlar sur'atiga nisbatan orqada | `RULE_TARGET_LAG_PERCENT` |

Yangi qoida qo'shish uchun `app/services/rules.py` faylidagi patternga
ergashib funksiya yozib, `ALL_RULES` ro'yxatiga qo'shish kifoya.

## Bot funksiyalari

**Sotuvchi uchun:**
- 📊 Shaxsiy natija (bugungi savdo, ochiq lidlar, targetlar progress-bar bilan)
- ⚠️ Shaxsiy ochiq ogohlantirishlar ro'yxati
- 🔔 Bildirishnomalarni yoqish/o'chirish
- ☀️/🌙 Kunlik tong va kechki avtomatik hisobot

**Rahbar / HR uchun:**
- 👥 Jamoa holati (barcha sotuvchilar bo'yicha umumiy ko'rinish)
- ➕ Yangi xodim uchun taklif (invite) yaratish
- 🎯 Target belgilash (savdo summasi / yopilgan bitimlar / yangi lidlar / konversiya — kunlik/haftalik/oylik)
- 🗓 Haftalik avtomatik hisobot

**Administrator uchun:**
- amoCRM ulanishini tekshirish (`/amosetup`)
- Qo'lda sinxronizatsiya (`/sync`)
- Xodimlarni amoCRM foydalanuvchilariga bog'lash (`/linkamo`)

## O'rnatish

1. **amoCRM tomonida integratsiya yarating**: amoCRM sozlamalari →
   Integratsiyalar → Yaratish. `Client ID`, `Client secret` va
   `Redirect URI` oling. Birinchi avtorizatsiyadan `authorization code`
   oling (yoki uzoq muddatli token yarating).

2. **`.env` faylini tayyorlang**:
   ```bash
   cp .env.example .env
   # BOT_TOKEN, ADMIN_TELEGRAM_IDS, AMO_* qiymatlarini to'ldiring
   ```

3. **Docker bilan ishga tushirish** (tavsiya etiladi):
   ```bash
   docker compose up -d --build
   ```

   **Yoki lokal Python bilan:**
   ```bash
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   python -m app.main
   ```

4. **Birinchi admin**: `ADMIN_TELEGRAM_IDS` ichidagi Telegram ID egasi botga
   `/start` yuborishi bilan avtomatik administrator bo'ladi. Keyin
   `/amosetup` bilan amoCRM ulanishini tekshiring, `/addemployee` bilan
   sotuvchilarni qo'shing va ularga chiqqan `/start <kod>` ni yuboring,
   so'ng `/linkamo` orqali har birini amoCRM akkountiga bog'lang.

5. **amoCRM webhook (ixtiyoriy, real vaqtga yaqinroq nazorat uchun)**:
   amoCRM sozlamalari → Webhooklar → qo'shish:
   `https://SIZNING_DOMEN/amocrm/webhook?secret=WEBHOOK_SECRET`
   (`.env` dagi `WEBHOOK_SECRET` bilan bir xil bo'lsin). Webhook bo'lmasa
   ham bot `SYNC_INTERVAL_MINUTES` bo'yicha muntazam o'zi sinxronlanadi —
   webhook faqat kutish vaqtini qisqartiradi.

## Loyiha tuzilishi

```
app/
  amocrm/       amoCRM OAuth, API mijozi, sinxronizatsiya
  bot/          Telegram bot: handlerlar, klaviaturalar, FSM
  services/     Biznes mantiq: qoidalar, targetlar, hisobotlar
  scheduler/    Davriy vazifalar (APScheduler)
  web/          amoCRM webhook qabul qiluvchi (FastAPI)
  db/           SQLAlchemy modellari va sessiya
tests/          pytest testlari
```

## Test va lint

```bash
pip install -r requirements-dev.txt
ruff check app tests
pytest
```
