# 🐝 Bee-Agent-Ai — وكيل ذكاء اصطناعي متصل بتيليجرام

وكيل AI كامل يعمل عبر **Agno (AgentOS)** + **واجهة OpenAI العامة** + **واجهة تيليجرام العامة للبوتات (Bot API)**، مبنيّ حرفياً على البنية الموصى بها في التوثيق الرسمي:
`https://docs.agno.com/agent-os/interfaces/telegram/introduction`

> ⚠️ **أمني**: مفاتيح التجربة مضمّنة في `bee/config.py` لكي يعمل المشروع فوراً بدون أي تعديل. قبل نشر المستودع على الإنترنت: احذف المفاتيح من الكود، أنشئ مفتاحاً جديداً من platform.openai.com، وأرسل `/revoke` لـ @BotFather لتغيير توكن البوت.

---

## ✅ الميزات الجاهزة الآن

| الميزة | الحالة | مصدرها في التوثيق |
|---|---|---|
| بكسل-باي-بكسل ستريمينغ مع تعديل مباشر للرسالة | ✅ افتراضياً | introduction → Streaming |
| **سلوك المجموعات**: رد فقط عند @mention أو الرد على رسالة البوت | ✅ افتراضياً | introduction → Group Chat Support |
| تجاهل رسائل البوتات الأخرى (منع حلقات المحادثة) | ✅ تلقائياً | reference → Message Processing |
| وسائط واردة: صور، ملصقات، رسائل صوتية، فيديو، مستندات، GIFs | ✅ | introduction → Media Support |
| وسائط صادرة: صور مولدة بـ OpenAI (GPT Image) تصل كرسائل تيليجرام أصلية | ✅ (قابلة للإيقاف) | Media Support + OpenAITools |
| أوامر `/start` `/help` `/new` مع تسجيل تلقائي في قائمة البوت | ✅ | reference → Command handling |
| جلسات محفوظة في SQLite + إعادة تعيين بمعرفة `/new` | ✅ | introduction → Session Management |
| تحقق أمني من `X-Telegram-Bot-Api-Secret-Token` | ✅ | setup → Production Deployment |
| تقسيم الرسائل الطويلة تلقائياً (حد 4096) + احترام حد المعدل 429 | ✅ | reference |
| بحث ويب مباشر + أدوات تفكير ReasoningTools + ذاكرة مستخدم دائمة | ✅ (أعلام تفعيل) | أمثلة reasoning / user-memory |
| `TelegramTools` لإرسال ردود استباقية (13 أداة) | ✅ اختياري | introduction → TelegramTools |
| أوضاع Team و Workflow متعددة الخطوات | ✅ عبر `BOT_MODE` | أمثلة team / workflow |

---

## 🚀 التشغيل السريع (3 أوامر)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python telegram_bot.py
```

ثم سجّل الـ webhook (من نافذة ngrok مثلاً):

```bash
python telegram_bot.py set-webhook --url https://xxxx.ngrok-free.app/telegram/webhook
```

افتح البوت على تيليجرام وأرسل `/start` — هذا كل شيء.
**التعليمات الكاملة خطوة بخطوة بالعربية: [docs/SETUP.md](docs/SETUP.md)**

---

## 🗂️ بنية المشروع (حسب توصيات docs.agno.com)

التوثيق الرسمي يعتمد ملف تشغيل واحداً باسم `telegram_bot.py` + قاعدة SQLite في مجلد `tmp/`؛ حافظنا على هذا القلب تماماً وغلّفناه بحزم صغيرة:

```
Bee-Agent-Ai/
├── telegram_bot.py            # 🎯 نقطة التشغيل + CLI لإدارة الـ webhook
├── bee/                       # الحزمة الداخلية
│   ├── config.py              # كل التكوين (مفاتيح، نماذج، أعلام الميزات) مع قيم جاهزة
│   ├── agent.py               # بناء الـ Agent / Team / Workflow والأدوات
│   ├── prompts.py             # تعليمات الوكيل (instructions)
│   ├── telegram_api.py        # اتصال مباشر بواجهة تيليجرام العامة (httpx بدون مكتبات تجريد)
│   └── openai_api.py          # فحص مباشر لواجهة OpenAI العامة (models.list / ping)
├── examples/                  # # أمثلة التوثيق الرسمي كاملةً (مُحوّلة إلى OpenAI)
│   ├── 01_basic_agent.py      #   basic
│   ├── 02_streaming.py        #   streaming
│   ├── 03_team.py             #   team (باحث + كاتب)
│   ├── 04_workflow.py         #   workflow (مسودة + تحرير)
│   ├── 05_streaming_workflow.py #  workflow مع عرض تقدم الخطوات
│   ├── 06_reasoning_agent.py  #   ReasoningTools + بحث ويب
│   ├── 07_agent_with_user_memory.py # MemoryManager (ذاكرة المستخدم)
│   ├── 08_agent_with_media.py #   توليد صور GPT Image + تحويل صوت/نص
│   └── 09_multiple_instances.py # بوتان على نفس السيرفر (prefix مختلف لكل token)
├── scripts/
│   ├── set_webhook.sh         # تسجيل webhook عبر curl (نفس أمر التوثيق حرفياً)
│   └── clear_webhook.sh       # حذف webhook + التحديثات المعلقة
├── tests/test_smoke.py        # 10 اختبارات بدون إنترنت تتحقق من كل الأسلاك
├── docs/
│   ├── SETUP.md               # 📖 خطوات الإعداد الكاملة بالعربية
│   ├── CODE_GUIDE.md          # 📖 شرح تفصيلي لكل سطر/قسم بالعربية
│   ├── ADVANCED_FEATURES.md   # 📖 كل الميزات المتقدمة وكيفية تفعيلها
│   └── TROUBLESHOOTING.md     # 📖 استكشاف الأخطاء بالعربية
├── requirements.txt
├── .env.example               # كل المتغيرات القابلة للتعديل (اختياري)
└── tmp/                       # قواعد SQLite (يُنشأ تلقائياً)
```

## 🧪 تحقّق محلي بدون تيليجرام

```bash
python tests/test_smoke.py          # 10/10 OK
python telegram_bot.py openai-check # يتصل بواجهة OpenAI العامة ويعرض النماذج المتاحة
python telegram_bot.py telegram-check # getMe + getWebhookInfo من تيليجرام مباشرة
```

## 📌 سلوك الوكيل في المجموعات (كما طُلب تماماً)

منطق الفلترة في واجهة Agno الرسمية (`router.py`) — وتتحقق منه هذه الأعلام في `telegram_bot.py`:

- `reply_to_mentions_only=True` → في المجموعات يرد **فقط** عند ذكر `@username_bot` أو الرد على رسالته.
- `reply_to_bot_messages=True` → الرد يشمل أيضاً من **يرد على رسالة سابقة للوكيل**.
- الرسائل من `is_bot=True` تُتجاهَل (لا رسائل عشوائية، لا حلقات بين البوتات).
- في الخاص (DMs) يرد على كل رسالة — والوسم `@bot` يُزال من النص قبل إرساله للنموذج.
