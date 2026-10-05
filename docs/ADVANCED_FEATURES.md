# 🚀 الميزات المتقدمة — كاملة من توثيق Agno الرسمي وكيفية تفعيلها

المصدر: `docs.agno.com/agent-os/interfaces/telegram/introduction` + `…/setup` + `…/reference` + كل أمثلة `agent-os/usage/interfaces/telegram/*` + `tools/toolkits/social/telegram`. كل ميزة موثّقة هنا مع موضع تفعيلها في هذا المشروع.

---

## 1) البث الحي (Streaming) — تعديل الرسائل لحظياً
**من التوثيق:** عند `streaming=True` يعدّل البوت رسالة الرد في الوقت الحقيقي مع قدوم الرموز، مقنّناً بحوالي تعديل واحد كل ثانية لاحترام حدود تيليجرام، وعند بلوغ حد المعدل (429) يوقف التعديلات ويحترم `retry_after`. في الـ Workflows تُعرض أيضاً خطوات التقدم (اسم الخطوة الجارية، التكرارات، التنفيذ المتوازي بمسافات بادئة).

**في المشروع:** `TELEGRAM_STREAMING=1` (افتراضياً) ← يمر إلى `Telegram(streaming=...)`.
**أحداث الحالة المعروضة أثناء الانتظار:** `Reasoning...` / `{Tool}...` / `{Tool}` (تُزال النقطة عند الاكتمال) / `{Tool} failed` / `Updating memory...`.

## 2) عرض سلسلة التفكير (show_reasoning)
**من التوثيق:** يرسل تفكير النموذج كرسالة منفصلة قبل الرد — **وضع non-streaming فقط** (في البث يظهر التفكير ضمن رسائل الحالة).

**التفعيل:**
```bash
TELEGRAM_STREAMING=0
TELEGRAM_SHOW_REASONING=1
```
أو مع OpenAI: `OPENAI_MODEL=gpt-5.4` + `OPENAI_REASONING_EFFORT=high` لمنح النموذج مساحة تفكير أكبر (المعامل الرسمي في platform.openai.com).

## 3) سياسة المجموعات الدقيقة (مطلوب هذا المشروع)
**من التوثيق (Group Chat Support):**
- `reply_to_mentions_only=True` (افتراضي): في المجموعة يُعالَج فقط ما فيه **@mention للبوت** أو **رد على رسالة البوت**. في الخاص كل رسالة تُعالَج.
- `reply_to_bot_messages=True` (افتراضي): الرد يشمل الردود على رسائل البوت نفسه.
- رسائل أي بوت آخر تُتجاهَل دائماً (حماية من حلقات البوتات — مرجع: Bot filtering).
- لإلغاء التقييد كلياً (البوت يرد على كل شيء): `TG_REPLY_TO_MENTIONS_ONLY=0` **ويجب** تعطيل privacy mode من @BotFather (`/setprivacy` ← Disable) ليرى البوت كل الرسائل.
- يزيل الوكيل نص `@bee_agent_bot` من الرسالة قبل تمريرها للنموذج (Text cleanup) فيرد مباشرة دون تكرار المنشن.
- البرومبت نفسه (bee/prompts.py) يضيف انضباطاً: «أجب من خاطبك فقط، لا تتدخل في غير ذلك، لا رسائل عشوائية».

## 4) إدارة الجلسات و `/new` (Session Management)
- معرّف الجلسة: `tg:{entity_id}:{chat_id}` و`tg:{entity_id}:{chat_id}:{message_thread_id}` لمنتديات/ثريدات السوبرجروب — أي **لكل محادثة سياقها المعزول**.
- `/new` ينشئ جلسة جديدة فارغة — **يتطلب قاعدة بيانات** (وفّرناها: SqliteDb في `tmp/bee_telegram.db`)؛ بدون DB يرد البوت برسالة توضيحية.
- `add_history_to_context=True` + `NUM_HISTORY_RUNS=3`: آخر 3 تبادلات ضمن السياق (نفس مثال basic الرسمي).
- ⚠️ قيد معروف في المرجع الرسمي: البحث عن الجلسة المخزّنة يستخدم مقارنة بادئة بدون حدّ فاصل (`tg:a:12` قد يطابق `tg:a:123`)؛ الحل العملي الحالي: كيان واحد لكل بوت (وهو وضعنا) وجعل `entity_id` ثابتاً (`id="bee-telegram-agent"`).

## 5) الوسائط الواردة (Inbound Media)
يستقبل الوكيل تلقائياً (حد التنزيل 20MB): صور وملصقات ← `Image`؛ رسالة صوتية وصوت ← `Audio`؛ فيديو/GIF/VideoNote ← `Video`؛ مستندات ← `File`.
التحويل يتم في `helpers.extract_message_payload` من الحزمة الرسمية؛ النموذج متعدد الوسائط في OpenAI يحللها (نموذج gpt-5.x يقبل الصور؛ للصوت يعمل نسخ Whisper عبر `OpenAITools.transcribe_audio` المفعّل أساساً).

## 6) الوسائط الصادرة (Outbound Media)
أي صورة/صوت/ملف تنتجه أدوات الوكيل (مثل `OpenAITools(image_model="gpt-image-2")` أو ElevenLabsTools) يُرسل تلقائياً كرسالة وسائط أصلية مع النص (توثيق: Media Support). مفعّل في مشروعنا عبر `ENABLE_IMAGE_GENERATION=1` — جرّب: «ارسم لي خلية نحل بأسلوب مائي».
> صفحة agent-with-media الرسمية تعدّ مثال DALL-E **مهملاً** وتوجّه إلى GPT Image عبر OpenAITools — ونحن التزمنا بالتوصية الأحدث حرفياً.

## 7) `TelegramTools` — أفعال صادرة كاملة (13 أداة)
**من التوثيق:** مجموعة أدوات مستقلة عن الواجهة؛ تمنح الوكيل القدرة على مبادَرة أفعال على Bot API العام:

| الطريقة | الوصف | علم التفعيل |
|---|---|---|
| `send_message` | نص لدردشة | `enable_send_message` (افتراضي مفعّل) |
| `send_photo / send_document / send_video / send_audio / send_animation / send_sticker` | وسائط صادرة بـ caption | `enable_send_*` |
| `edit_message` / `delete_message` | تعديل/حذف رسالة بـ message_id | `enable_edit_message` / `enable_delete_message` |
| `react_with_emoji` | تفاعلية إيموجي على رسالة | `enable_react_with_emoji` |
| `pin_message` | تثبيت رسالة (مع كتم الاختياري) | `enable_pin_message` |
| `get_chat` / `get_file` | بيانات الدردشة / تنزيل ملف (base64 أو حفظ محلي عبر `output_directory` + `save_downloads`) | `enable_get_chat` / `enable_get_file` |

النتائج JSON: `{"status":"success","message_id":…}` أو `{"status":"error","message":…}`.

**في المشروع:** `all=True` مفعول داخل `bee/agent.py` متى ضبطت `TELEGRAM_CHAT_ID` (أو `ENABLE_TELEGRAM_TOOLS=1`). احصل على الـ chat_id:
```bash
python telegram_bot.py delete-webhook && python telegram_bot.py find-chat-id
```
> استخدمها بحذر في المجموعات: هي «مسمار الأمان» الوحيد لإرسال الوكيل رسالة غير موجهة إليه مباشرة — لا نفعّلها إلا إن احتجت تنبيهات مجدولة فعلية.

## 8) الأوامر والقوائم (Commands)
- قائمة الأوامر الافتراضية (`/start`, `/help`, `/new`) استبدلناها في `telegram_bot.py` بوصف ثنائي اللغة، ومسجَّلة في واجهة تيليجرام آلياً عبر `register_commands=True` (تُنادى `setMyCommands` عند أول رسالة).
- الرسائل الأربع (start/help/error/new) كلها قابلة للتخصيص — نفّذناها في `telegram_bot.py`.
- أي أمر غير معروف (مثل `/mycommand`) يمر كنص للنموذج فيتصرف معه كأنه طلب عادي (سلوك واجهة Agno).

## 9) الاقتباس (quoted_responses)
`TG_QUOTED_RESPONSES=1` → في **الخاص** يرد البوت بالاقتاس على رسالة المستخدم (reply-to). في المجموعات الاقتباس always-on حسب المرجع الرسمي (السطر: `reply_to = incoming_message_id if (is_group or quoted_responses)`).

## 10) Prefix مخصص + تعدد البوتات (Multiple Instances)
`prefix="/telegram"` قابل للتغيير — والأساس: **webhook واحد لكل توكن**. لتشغيل وكيلين على سيرفر واحد استخدم توكنين عبر @BotFather ومسارين `/basic/webhook` و`/web-research/webhook` — جاهز حرفياً في `examples/09_multiple_instances.py`.

## 11) فرق عمل (Team) وسير عمل (Workflow)
- **Team:** قائد يفوّض لباحث وكاتب (مثال team الرسمي) — في المشروع `BOT_MODE=team` (يبنى في `bee/agent.py::build_team`) أو `examples/03_team.py`.
- **Workflow:** أنابيب مسودة→تحرير بخطوتين (`Steps` + `Step`) — `BOT_MODE=workflow` أو `examples/04_workflow.py`، ومع البث الحي تظهر حالة كل خطوة (`examples/05_streaming_workflow.py`). للسيرفر: تمرير `workflows=[...]` بدل `agents=[...]` — تم في `build_agent_os`.

## 12) ذاكرة المستخدم عبر الجلسات (Memory)
`MemoryManager(memory_capture_instructions=..., model=...)` + `enable_agentic_memory=True` ← يطبّق مثال agent-with-user-memory: يحفظ اسم المستخدم واهتماماته ويستحضرها لاحقاً. `ENABLE_USER_MEMORY=1` افتراضياً (يحتاج DB — مؤمن).

## 13) أدوات التفكير والبحث (Reasoning + Web Search)
مثال reasoning-agent الرسمي: `ReasoningTools(add_instructions=True)` + بحث ويب → في المشروع مفعّلان افتراضياً (`ENABLE_REASONING_TOOLS`, `ENABLE_WEB_SEARCH`). للتشخيص: `TELEGRAM_SHOW_REASONING=1`.

## 14) صوت داخل/خارج (Whisper + TTS)
`OpenAITools(enable_transcription=True, enable_speech_generation=...)`:
- إدخال: الميمو الصوتي يُنسخ تلقائياً (whisper-1) فيفهمه الوكيل.
- خروج: `ENABLE_TTS=1` يضيف أداة `generate_speech` → رد صوتي mp3 كرسالة تيليجرام صوتية.

## 15) أمان Webhook (Security)
- تيليجرام يعيد إرسال `secret_token` في هيدر `X-Telegram-Bot-Api-Secret-Token`؛ الواجهة تقارنه ثابتياً (constant-time) وترفض 403.
- المشروع ولّد `TELEGRAM_WEBHOOK_SECRET_TOKEN` بقيمة صالحة (حروف/أرقام/_/-) ويحقنها تلقائياً في `set-webhook`.
- `APP_ENV=development` يعطّل الفحص — **للاختبار المحلي المعزول فقط** (تحذير رسمي).
- كاش التكرار يحمي من إعادة تسليم Telegram؛ ملاحظة: ليس مشتركاً بين النسخ المتعددة.

## 16) التنسيق والتقسيم التلقائي (Text Formatting)
Markdown من النموذج ← HTML تيليجرام حسب جدول المرجع: `**b**→<b>`, `*i*→<i>`, `__u__→<u>`, `~~s~~→<s>`, كود داخل السطر وكتل `<pre>`, اقتباس `<blockquote>`, روابط `<a>`, القوائم `-` ← `•`. أي رد أطول من **4096** يُقسَّم تلقائياً (chunking في `helpers._chunk_text`).

## 17) إضافات AgentOS نفسها (من agno.com/agentos + docs/agent-os)
- `GET /docs` — واجهة OpenAPI/Swagger لكل الـ 80+ endpoint (تشغيل/جلسات/آثار).
- `tracing=1` (`AGENTOS_TRACING=1`): OpenTelemetry traces إلى نفس قاعدة SQLite — تتبع كامل لقرارات الوكيل.
- `mcp=1` (`AGENTOS_MCP=1`, تتطلب `fastmcp`): كشف الوكيل كـ MCP server على `/mcp` لعملاء MCP.
- لوحة os.agno.com تتصل بسيرفرك مباشرة (لا تمر بياناتك عبر Agno).
- عند الحاجة: `authorization=True` + JWT/RBAC (مرجع: Security & Auth في AgentOS).

## 18) خيارات واجهة OpenAI العامة المستخدمة
من platform.openai.com/docs/api-reference ما التزم به المشروع:
- `model` قابل للتبديل بالكامل (`OPENAI_MODEL`) + أداة `openai-check` تعرض المتاح لحسابك فعلياً.
- `reasoning_effort` (minimal/low/medium/high) ← `OPENAI_REASONING_EFFORT`.
- نقطتا النهاية (endpoints): `chat/completions` أو `responses` ← `OPENAI_API_KIND`.
- `images.generate` model `gpt-image-2` لتوليد الصور (الأداة), و`audio.transcriptions` + `audio.speech` للصوت — كلها عبر الـ SDK الرسمي نفسه الذي تستخدمه Agno.

## 19) النشر (Deploy)
للنشر الدائم: لا تعتمد على ngrok (للتطوير فقط)؛ استخدم قالباً من `docs.agno.com/deploy/introduction` أو VPS + Nginx + HTTPS + systemd (مثال في docs/SETUP.md §8) مع إبقاء فحص السر مفعلاً.

## 20) الاختبارات الآلية
`tests/test_smoke.py` — 10 اختبارات offline تغطي: تحميل الإعدادات، بناء الكيانات الثلاثة، تركيب المسارات `/telegram/status|webhook`، استجابات `processing/ignored/duplicate`، منطق mention/reply، فحص السر، قص الرسائل 4096.
