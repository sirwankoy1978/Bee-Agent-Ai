# 📖 خطوات الإعداد الكاملة — Bee-Agent-Ai

> هذه الوثيقة مطابقة بالترتيب للتوثيق الرسمي
> `docs.agno.com/agent-os/interfaces/telegram/setup` مع تحديثات تجعل التشغيل فورياً في هذا المستودع.

---

## 0) المتطلبات المسبقة

| المتطلب | التفاصيل |
|---|---|
| Python | **3.9 أو أحدث** (agno الرسمي: `>=3.9,<4`) — يُفضَّل 3.12 |
| حساب تيليجرام | لإنشاء البوت وللاختبار |
| مفتاح OpenAI API | `OPENAI_API_KEY` من platform.openai.com — **موجود مسبقاً داخل `bee/config.py` في هذا المشروع** |
| توكن البوت | من @BotFather — **موجود مسبقاً داخل `bee/config.py`** |
| نفق HTTPS للتطوير المحلي | ngrok (أو cloudflared) لأن تيليجرام يرسل الأحداث إلى رابط عام فقط |

## 1) إنشاء البوت من @BotFather

1. افتح تيليجرام وأرسل رسالة إلى [@BotFather](https://t.me/BotFather).
2. أرسل `/newbot` ثم اختر الاسم الظاهر واسم المستخدم (يجب أن ينتهي بـ `bot`، مثال: `bee_agent_bot`).
3. انسخ التوكن (صيغته `123456:ABC-DEF...`). في هذا المشروع التوكن مُهيّأ مسبقاً فلا تحتاج شيئاً.

### ⚙️ إعدادان مهمان من @BotFather (للسلوك الصحيح في المجموعات)

| الأمر | القيمة | لماذا |
|---|---|---|
| `/setprivacy` ← اختر البوت ← **Disable** | مطلوب فقط إذا أردت أن يرى البوت كل رسائل المجموعة ليعرف من يسنده/يرد عليه بدقة أعلى | افتراضياً تستقبل البوتات رسائل المجموعة التي تذكرها فقط؛ مع `reply_to_mentions_only=True` الوضع الافتراضي كافٍ عملياً للـ mentions، أما الردود على رسالة البوت فتحتاج أن تصل التحديثات (الرسالة المقتبسة تصل عادة، لكن تعطيل privacy mode يجعل قاعدة «الرد على البوت» مضمونة 100%) |
| `/setjoingroups` ← Enable | لكي تستطيع إضافة البوت للمجموعات | — |

> ملاحظة: privacy mode يخص **استقبال** الرسائل؛ منطق الرد عند الـ mention/الرد ينفذه الوكيل نفسه كما هو موضح في docs CODE_GUIDE.

## 2) تثبيت البيئة

```bash
# من جذر المشروع
python3 -m venv .venv
source .venv/bin/activate          # ويندوز: .venv\Scripts\activate

# الطريقة الرسمية في توثيق Agno (باستخدام uv) هي:
#   uv pip install -U "agno[os,telegram]" openai ddgs
# وهنا عبر pip العادي بنفس الحزم بالضبط:
pip install -U "agno[os,telegram]" openai ddgs
# أو: pip install -r requirements.txt
```

ما الذي يُثبَّت ولماذا:

| الحزمة | الدور |
|---|---|
| `agno[os]` | AgentOS: خادم FastAPI + إدارة الجلسات + الـ interfaces (تيليجرام أحدها) |
| `agno[telegram]` | يضيف `pyTelegramBotAPI` التي تستخدمها الواجهة داخلياً للاستجابة |
| `openai` | SDK واجهة OpenAI العامة (تستخدمها نماذج `OpenAIChat/OpenAIResponses` وأيضاً `bee/openai_api.py` للفحص المباشر) |
| `httpx` | عميل HTTP الخام المستخدم في `bee/telegram_api.py` للنداء المباشر على واجهة تيليجرام العامة |
| `ddgs` | محرك البحث الذي تستخدمه `WebSearchTools` |

## 3) (اختياري) ضبط متغيرات البيئة

كل القيم لها افتراضات عاملة داخل `bee/config.py`. لتجاوزها أنشئ ملف `.env` من القالب:

```bash
cp .env.example .env      # ثم عدّل ما تشاء؛ أو صدّر المتغيرات يدوياً:
export TELEGRAM_WEBHOOK_SECRET_TOKEN="$(openssl rand -hex 16)"
```

> **مهم**: `TELEGRAM_WEBHOOK_SECRET_TOKEN` يجب أن يكون **نفس القيمة** عند تشغيل السيرفر وعند تسجيل الـ webhook. الصيغة المسموحة: حروف/أرقام/`_`/`-` بطول 1–256.
> لا تشغّل أبداً `APP_ENV=development` على رابط عام — إنه يعطّل فحص السر للاختبار المحلي المعزول فقط.

## 4) تشغيل الوكيل

```bash
python telegram_bot.py
```

سترى لوحة AgentOS والسيرفر على `http://0.0.0.0:7777`. تحقق من الحالة:

```bash
curl http://localhost:7777/telegram/status   # → {"status":"available"}
```

نقاط النهاية المثبّتة آلياً (حسب prefix الافتراضي `/telegram`):

- `POST /telegram/webhook` — يستقبل تحديثات تيليجرام (رسائل جديدة/محررة)
- `GET /telegram/status` — فحص صحة الواجهة
- بقية واجهة AgentOS: `/agents`, `/sessions`, `/health`, الوثائق التفاعلية على `/docs`، ولوحة التحكم os.agno.com تتصل بخادمك مباشرة.

## 5) فتح نفق HTTPS (للتطوير المحلي)

```bash
ngrok http 7777
# انسخ الرابط https://xxxx.ngrok-free.app
```

## 6) تسجيل الـ webhook

**الطريقة المدمجة (تستخدم واجهة تيليجرام العامة مباشرة وترسل السر نفسه):**

```bash
python telegram_bot.py set-webhook --url https://xxxx.ngrok-free.app/telegram/webhook
```

**أو الأمر الحرفي من التوثيق الرسمي:**

```bash
curl -X POST "https://api.telegram.org/bot$TELEGRAM_TOKEN/setWebhook" \
     --data-urlencode "url=https://xxxx.ngrok-free.app/telegram/webhook" \
     --data-urlencode "secret_token=$TELEGRAM_WEBHOOK_SECRET_TOKEN"
```

**أو السكربت الجاهز:** `NGROK_URL=https://xxxx.ngrok-free.app ./scripts/set_webhook.sh`

الاستجابة المتوقعة: `{"ok":true,"result":true,"description":"Webhook was set"}`

تحقق في أي وقت:

```bash
python telegram_bot.py webhook-info
# أو: curl "https://api.telegram.org/bot$TELEGRAM_TOKEN/getWebhookInfo"
```

## 7) جرّب البوت

1. خاص: أرسل `/start` ثم أي سؤال بالعربية أو الإنجليزية.
2. أرفق صورة أو رسالة صوتية — سيحللها الوكيل (صور/صوت GPT عبر أدوات Whisper مفعّلة).
3. اطلب: «ارسم رسمة خلايا نحل» — سيولّد صورة بها OpenAI ويرسلها كرسالة تيليجرام أصلية.
4. في مجموعة: أضف البوت، اذكره `@bee_agent_bot مرحباً` → يرد. أرسل رسالة عادية بدون ذكر → **لا يرد** (هذا هو المطلوب).
5. ردّ (Reply) على رسالة سابقة للبوت في المجموعة → يرد، رغم غياب الـ mention.
6. `python telegram_bot.py find-chat-id` (بعد `delete-webhook` مؤقتاً) للحصول على `chat_id` الخاص بك لتفعيل `TelegramTools` الاستباقية.

للعودة للـ webhook: أعد الخطوة 6.

## 8) النشر الدائم (إنتاج)

- استخدم رابط HTTPS ثابتاً (نطاقك + reverse proxy أو استضف قالب deploy من التوثيق `docs.agno.com/deploy/introduction`).
- بيئتك يجب أن تكون **بدون** `APP_ENV=development` حتى يبقى فحص السر مفعلاً (403 لكل طلب بدون الهيدر الصحيح).
- شغّل خلف مدير عمليات، مثال systemd:

```ini
[Service]
WorkingDirectory=/opt/Bee-Agent-Ai
EnvironmentFile=/opt/Bee-Agent-Ai/.env
ExecStart=/opt/Bee-Agent-Ai/.venv/bin/python /opt/Bee-Agent-Ai/telegram_bot.py
Restart=always
```

- عند تعدد النسخ (replicas) لاحظ أن كاش تكرار `update_id` محلي داخل العملية فقط (60 ثانية) حسب المرجع الرسمي — مصمم للسينغل-إينستانس.
