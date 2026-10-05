# 📖 الشرح التفصيلي لكل جزء من الكود

> كل التعليقات داخل الملفات الإنجليزية ذاتية الشرح؛ هذه الوثيقة هي الشرح العربي الموسّع،
> مع مسار رسالة تيليجرام كاملاً من اللحظة التي يضغط فيها المستخدم «إرسال».

---

## 1) `telegram_bot.py` — نقطة التشغيل

### ماذا يفعل؟
يبني الكيانات (Agent/Team/Workflow) ثم يغلّفها بواجهة تيليجرام الرسمية ثم يخدّمها بـ AgentOS، ويوفّر أوامر CLI لإدارة الـ webhook عبر **واجهة تيليجرام العامة مباشرة**.

### الجزء تلو الآخر

| الكود | الوظيفة |
|---|---|
| `START_MESSAGE / HELP_MESSAGE / ERROR_MESSAGE / NEW_MESSAGE` | نصوص الرد على `/start` `/help` وعند الأخطاء وعلى `/new`. تمر لواجهة `Telegram(...)` لأن التوثيق يجعلها معاملات قابلة للتخصيص؛كتبناها ثنائية اللغة (عربي/إنجليزي). |
| `BOT_COMMANDS` | قائمة أوامر تُسجَّل تلقائياً في قائمة أوامر البوت (`setMyCommands`) عبر `register_commands=True`، فنراها في واجهة تيليجرام. |
| `build_agent_os()` | يحاكي نمط التوثيق حرفياً: `AgentOS(agents=[agent], interfaces=[Telegram(...)])` ثم `agent_os.get_app()`. الـ kwargs `{kind: entity}` تسمح بنفس البنية لأوضاع team/workflow. |
| معاملات `Telegram(...)` | كلها من جدول Parameters الرسمي: `streaming` (تعديل حي للرسالة)، `show_reasoning` (رسالة منفصلة للتفكير، تعمل مع non-streaming)، `reply_to_mentions_only=True` + `reply_to_bot_messages=True` (**سياسة المجموعات المطلوبة**)، `quoted_responses`، `prefix`، `commands`، `register_commands`، `token`. |
| `cmd_serve` | يعرض ملخص التشغيل ثم `agent_os.serve(...)`. لاحظ `host="0.0.0.0"` وتمرير كائن `app` مباشرة (وليس نص الاستيراد) لأن `RELOAD=0` افتراضياً؛ مع `RELOAD=1` نمرر نص `"telegram_bot:app"` لأن uvicorn يحتاج استيراد الوحدة من جديد لكل عملية عاملة. |
| `cmd_set_webhook / cmd_delete_webhook / cmd_find_chat_id / cmd_*_check` | أدوات تشغيل على واجهة تيليجرام العامة: تسجيل الرابط مع `secret_token`، حذفه (للتحويل لوضع polling واكتشاف chat_id)، وفحص المفاتيح — كلها بدون أي مكتبة تجريد. |
| السطر الأخير `else: app = _agent_os.get_app()` | يسمح لنمط التوثيق `serve(app="telegram_bot:app", reload=True) بأن يستورد الملف من جديد ويحصل على `app` جاهزة داخل عملية العمل. |

## 2) `bee/config.py` — التكوين المركزي

- **قارئ `.env` مدمج** (20 سطراً) بلا تبعيات إضافية: ملف `.env` اختياري، وكل متغير بيئة يتجاوزه مباشرة.
- كل إعداد يملك **قيمة افتراضية تعمل فوراً**: مفاتيح التجربة موضوعة كـ defaults (مع تحذير أمني صريح في أول الملف).
- أعلام الميزات (`ENABLE_WEB_SEARCH`, `ENABLE_IMAGE_GENERATION`, `ENABLE_USER_MEMORY`, ...) تفصل «البنية» عن «السلوك»: يمكنك إطفاء أي ميزة من `.env` دون لمس الكود.
- `validate()` يفشل **مبكراً وبرسالة عربية/إنجليزية واضحة** قبل رفع السيرفر إذا نقص سرّ في غير وضع التطوير أو ضبط `BOT_MODE` خطأ — وهذا يوفّر عليك نصف مشاكل استكشاف الأخطاء.
- `TMP_DIR.mkdir(...)` يهيّئ مجلد `tmp/` الذي يوصي به التوثيق لملفات SQLite.

## 3) `bee/prompts.py` — تعليمات الوكيل

قائمة `AGENT_INSTRUCTIONS` مبنية على مثال basic الرسمي («helpful assistant on Telegram», «concise») **مع إضافة شرط سياسة المجموعات داخل البرومبت نفسه** كطبقة ثانية من الانضباط، إضافة إلى الفلترة البرمجية في الواجهة:

- «أنت مُخاطَب عبر mention أو reply؛ أجب من خاطبك وحدَه» → لا يقحم نفسه في نقاشات الآخرين.
- «لا تلخّص ولا تكرّر محادثات مستخدمين آخرين» → يحمي الخصوصية في المجموعات.
- «استخدم لغة المستخدم» → يفيد لأن نموذج OpenAI متعدد اللغات بامتياز.
- `add_datetime_to_context=True` (من التوثيق) يجعله يعرف التاريخ الحالي في كل تشغيل.

## 4) `bee/agent.py` — بناء الكيانات

### `build_model()`
يختار فئة النموذج حسب `OPENAI_API_KIND`:
- `chat` → `OpenAIChat` = نقطة نهاية **Chat Completions** `POST /v1/chat/completions` من واجهة OpenAI العامة.
- `responses` → `OpenAIResponses` = نقطة نهاية **Responses** `POST /v1/responses` (الأحدث، تدعم أدوات المدمجة).
- `OPENAI_MODEL` و`OPENAI_REASONING_EFFORT` يمرّان كما هما لمستودعات OpenAI (minimal|low|medium|high لعائلة GPT-5) — هذه «مرونة الخيارات» التي طلبتها من دراسة platform.openai.com/api-reference.

### `_build_db()`
`SqliteDb(db_file="tmp/bee_telegram.db", session_table="telegram_sessions")` — نفس نمط التوثيق؛ دونه لا يعمل `/new` ولا تُحفظ الجلسة بعد إعادة التشغيل.

### `_build_tools()` — أدوات مجمّعة من كل صفحات التوثيق:
| الأداة | ماذا تعطي | التفعيل |
|---|---|---|
| `WebSearchTools` | بحث DuckDuckGo للأخبار/الأسعار الحية (ddgs) | `ENABLE_WEB_SEARCH=1` (افتراضي؛ إن غابت ddgs تُطبع ملاحظة ويُكمل البوت بدونها) |
| `ReasoningTools(add_instructions=True)` | «مفكرة تفكير» منظمة للأسئلة المعقدة — من مثال reasoning-agent | `ENABLE_REASONING_TOOLS=1` |
| `OpenAITools(image_model="gpt-image-2", ...)` | توليد صور + نسخ صوتي (Whisper) + (اختياري TTS) **عبر واجهة OpenAI العامة مباشرة** — التوصية الحالية بدل DalleTools المهجورة كما تنص صفحة agent-with-media | `ENABLE_IMAGE_GENERATION=1`, `ENABLE_TTS=0` |
| `TelegramTools(all=True)` | 13 أداة صادرة (إرسال/تعديل/حذف/تفاعل/تثبيت...) عبر Bot API العام | تلقائياً مع `TELEGRAM_CHAT_ID` أو `ENABLE_TELEGRAM_TOOLS=1` |

> الصور المولّدة لا نرسلها يدوياً: واجهة تيليجرام تلتقط `RunOutput.images/audio/files` وتبعثها كرسائل وسائط أصلية (توثيق: Outbound Media).

### ذاكرة المستخدم
```python
MemoryManager(model=..., memory_capture_instructions=...) + enable_agentic_memory=True
```
مطابقة لمثال agent-with-user-memory: يلتقط الاسم/الاهتمامات/التفضيلات عبر الجلسات (يحتاج db — موجود).

### `build_team()` و`build_workflow()`
نسخة منقحة من مثالي team وworkflow الرسميين (باحث+كاتب؛ مسودة→تحرير) مع استبدال كل النماذج بـ OpenAI، وويُفعّلهما `BOT_MODE=team|workflow`.

## 5) `bee/telegram_api.py` — واجهة تيليجرام العامة مباشرة

كما طلبت: لا مكتبات تجريد — `httpx.post("https://api.telegram.org/bot<token>/<method>")` فقط. التوابع مطابقة لصفحات core.telegram.org/bots/api:

| الدالة | Method الرسمي | فائدته هنا |
|---|---|---|
| `get_me()` | getMe | فحص التوكن (`telegram-check`) |
| `set_webhook(url, secret_token, allowed_updates=["message","edited_message"])` | setWebhook | تسجيل الرابط + السر + تقليص الضجيج لنوعي الأحداث اللذين تعالجهما الواجهة فعلاً (المصدر: router.py يقرأ `message`/`edited_message` فقط) |
| `get_webhook_info()` | getWebhookInfo | يريك `pending_error_count` و`last_error_message` — أول مكان تنظر إليه عند صمت البوت |
| `delete_webhook(drop_pending_updates=True)` | deleteWebhook | للتبديل لوضع polling (واكتشاف chat_id) |
| `set_my_commands(...)` | setMyCommands | قائمة الأوامر في واجهة تيليجرام |
| `send_message(chat_id, text)` | sendMessage | إشعارات إدارية/اختبارات يدوية؛ مع قصّ تلقائي عند 4096 |
| `get_updates()` | getUpdates | استخراج `chat_id` للمجموعات والأشخاص |
| `describe()` | getMe+getWebhookInfo | تقرير حالة من سطرين |

## 6) `bee/openai_api.py` — واجهة OpenAI العامة مباشرة

- `list_models()` → `GET /v1/models`: ما الذي يستطيع حسابك فعلاً استخدامه؟
- `check_model_available()` يطابق `OPENAI_MODEL` مع قائمة حسابك وويعرض النماذج الصالحة للوكيل ونماذج الصور — يريحك من تخمين المعرّفات.
- `ping()` إرسال real-completion قصير عبر نفس نقطة النهاية الذي سيستخدمه الوكيل (رسالة OK + Usage) — اختبار دخان كامل السلسلة قبل ربط تيليجرام.

## 7) 🔴 المسار الكامل لرسالة واردة (الأهم — كيف يتعامل الوكيل مع رسائل تيليجرام)

```
المستخدم يضغط إرسال
   │ HTTPS POST (سر X-Telegram-Bot-Api-Secret-Token في الهيدر)
   ▼
POST /telegram/webhook   (FastAPI — ثبّتته Telegram interface)
   1) فحص السر: hmac.compare_digest مع TELEGRAM_WEBHOOK_SECRET_TOKEN
      • لا يطابق → 403 | • APP_ENV=development → تجاوز مع تحذير
   2) إزالة التكرار: كاش update_id لمدة 60 ثانية → {"status":"duplicate"}
   3) ليس رسالة؟ (callback_query مثلاً) → {"status":"ignored"}
   4) يعاد فوراً {"status":"processing"} — والمعالجة تستمر في BackgroundTask:
      │
      ├─ مرشّحات _process_message (من المصدر router.py):
      │   • مرسل = بوت آخر → تجاهل (يمنع حلقات البوتات)
      │   • مجموعة + reply_to_mentions_only → لا mention ولا reply للبوت → تجاهل  ← قاعدة «فقط عند المنشن/الرد»
      │   • أمر مثل /start@botname مع اسم بوت آخر → تجاهل
      │   • /start /help /new → ردود نصية جاهزة (+ /new يستبدل الجلسة في الـDB)
      │   • إرسال sendChatAction("typing") → مؤشر «يكتب…»
      │
      ├─ استخلاص المحتوى (helpers.extract_message_payload):
      │   • نص + caption؛ الصور/الملصقات→Image، الصوت/الرسالة الصوتية→Audio،
      │     الفيديو/GIF/VideoNote→Video، المستندات→File (حتى 20MB، تنزّل من تيليجرام)
      │
      ├─ جلسة: session_id = tg:{entity_id}:{chat_id}[:{message_thread_id}]
      │   (كل محادثة/ثريد معزول؛ user_id منفصل للذاكرة)
      │
      ├─ entity.arun(text, images=..., audio=..., user_id, session_id, stream=True)
      │   → Agent يستدعي OpenAI API (chat.completions أو responses)
      │   → قد ينادي أدوات: بحث ويب / reasoning / توليد صورة / …
      │
      ├─ البث (streaming=True):
      │   • رسالة رد واحدة تُعدَّل مباشرة ~كل 1 ثانية (throttling)
      │   • أحداث حالة: "Reasoning…", "WebSearchTools…", أخطاء الأدوات تظهر
      │   • عند 429 من تيليجرام → احترام retry_after وتعليق التعديلات
      │   • Markdown من النموذج → HTML تيليجرام (bold/code/blockquote/…)
      │   • أكثر من 4096 حرفاً → تُقسَّم رسائل متتابعة
      │
      └─ وسائط الرد (send_response_media): الصور/الصوت/الملفات التي أنتجتها الأدوات
          تُرسَل ksendMessage/sendPhoto/sendAudio/sendDocument أصلية.
```

### لماذا هذا التصميم موثوق؟
1. **200 فوري قبل المعالجة الثقيلة**: لو عاد 5xx لتيليجرام أعاد تسليم التحديثات بشكل متكرر وفوضوي؛ الإرجاع السريع + BackgroundTask يفك الازدواجية.
2. **الدروع الثلاث**: فحص السر (أمان) ← كاش التكرار (موثوقية) ← مرشّحات المجموعات (سياسة).
3. **الفشل لا يُسكِت البوت**: أي استثناء في الخلفية يُترجم لرسالة `error_message` للمستخدم بدل صمت غامض.

## 8) كيف تُفعَّل الميزات من `.env` (خلطة سريعة)

```bash
# أعلى جودة إجابة (مع تأخير+تكلفة):
OPENAI_MODEL=gpt-5.4
OPENAI_REASONING_EFFORT=high

# فريق بحث كامل بدل وكيل مفرد:
BOT_MODE=team

# صوت منطوق في الردود (TTS):
ENABLE_TTS=1

# خاصية الاقتباس في الخاص أيضاً:
TG_QUOTED_RESPONSES=1

# إطفاء البث (رسالة كاملة مرة واحدة + رسالة Reasoning منفصلة):
TELEGRAM_STREAMING=0
TELEGRAM_SHOW_REASONING=1
```
