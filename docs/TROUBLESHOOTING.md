# 🔧 استكشاف الأخطاء وإصلاحها

مرتّبة حسب الأثر: ابدأ من القسم الأول «البوت صامت» ثم انتقل لما بعده. الأقسام 1–5 من جدول Troubleshooting الرسمي في توثيق Agno، والباقي توسيع عملي.

---

## 1) البوت لا يرد إطلاقاً (في الخاص)
**الأسباب بالترتيب المرجّح + الفحص السريع:**

```bash
# أ) السيرفر يعمل؟
curl http://localhost:7777/telegram/status        # توقّع {"status":"available"}

# ب) الـ webhook مسجّل ويشير لنفقتك؟
python telegram_bot.py webhook-info
#   أو: curl "https://api.telegram.org/bot$TELEGRAM_TOKEN/getWebhookInfo"
```
- `url` فارغ/قديم → أعد: `python telegram_bot.py set-webhook --url https://<الرابط-الحالي>/telegram/webhook`
- رابط ngrok تغيّر بعد إعادة تشغيله (الرابط المجاني يتبدل!) → **أشهر سبب**; أعد التسجيل بالرابط الجديد أو اشترك برابط ثابت أو انشر على نطاقك.
- نفق مغلق → افتح الرابط في متصفحك؛ إن ظهر خطأ ngrok فالتطبيق خلفه ميت أو على منفذ آخر (تأكد `PORT=7777` ومنفذ ngrok نفسه).
- `last_error_message` فيه `connection refused/timeout` → السيرفر لا يستجيب (انظر 6).

## 2) أخطاء 403 على الـ webhook
**السبب (رسمي):** تشغيل بوضع production بدون/بسـر غير مطابق.
- `TELEGRAM_WEBHOOK_SECRET_TOKEN` عند السيرفر ≠ السـر المسجَّل مع setWebhook. الحل: صدّر نفس القيمة للطرفين أو استخدم `python telegram_bot.py set-webhook` (يقرأ نفس الإعداد تلقائياً).
- للتحربة المحلية المعزولة فقط: `APP_ENV=development python telegram_bot.py` (يعطّل الفحص — لا تستخدمه مع نفق عام).
- تحقق: `curl -i -X POST https://.../telegram/webhook -H "X-Telegram-Bot-Api-Secret-Token: <السر>" -d '{}'` يجب أن يرجع 200 وليس 403.

## 3) البوت يتجاهل الرسائل في المجموعة
**السبب الرسمي الأول: privacy mode.** افتراضياً لا يرى البوت إلا أوامره/تنبيهاته:
- @BotFather ← `/setprivacy` ← اختر البوت ← **Disable** ← أخرج البوت من المجموعة وأعد إضافته (إعادة الإضافة تلزم لتحديث الوضع).
- ثم تحقق من سلوكنا المقصود: لن يرد إلا إذا **ذكرته `@bee_agent_bot`** أو **رددت رسالته** — هذا مطلوب المشروع وليس عطلاً.
- إن استخدمت `TG_REPLY_TO_MENTIONS_ONLY=0` وتريد الرد على كل رسالة: وضع privacy mode يجب أن يكون Disable وإلا لن تصلك الرسائل أصلاً.
- رسائل البوتات الأخرى تُتجاهل عمداً (منع حلقات): كل مستخدم يجب أن يخاطبه بنفسه.

## 4) `/new` لا يغيّر شيئاً
**رسمي:** بدون قاعدة بيانات لا توجد جلسة محفوظة لتستبدل. تحقق أن `DB_FILE` (افتراضياً `tmp/bee_telegram.db`) قابل للكتابة وأن `bee/agent.py::build_agent` يمرر `db=` — عدّلته؟ أعد `SqliteDb`. تفقد وجود الملف بعد أول محادثة.

## 5) خطأ بدء: `TELEGRAM_TOKEN environment variable is not set`
- صدّر المتغير أو ضع `.env` في جذر المشروع (يقرأه `bee/config.py` تلقائياً) — أو اترك `TELEGRAM_TOKEN` في إعدادات المشروع كما هو معد مسبقاً.
- انتبه: تصدير متغير فارغ (`export TELEGRAM_TOKEN=`) يُحسب «غير مضبوط» لأن الافتراضي يُستخدم فقط عند غياب القيمة — أعِد تعيينه بقيمة صحيحة.

## 6) بدء يفشل: `Address already in use` (7777)
منشغل سابق قيد التشغيل:
```bash
lsof -ti:7777 | xargs kill -9      # ويندوز: netstat -ano | findstr 7777 ثم taskkill /PID
```
أو شغّل على `PORT=7788 python telegram_bot.py` وحدّث نفقك/الأمر accordingly.

## 7) `Invalid HTTP request received` في اللوجات
غالباً محاولة وصل HTTP عادي لمنفذ mTLS/نفق، أو port scan. تجاهله إن كان نادراً؛ تكرّره بلا سبب = هناك من يخبط على نفقك العام — لا خطر على المنطق لأنه يفشل عند فحص الـ secret.

## 8) بطء/انقطاع الردود الطويلة
- البوت يقسّم عند 4096 حرفاً ويطبّق throttling على التعديلات — طبيعي.
- 429 من OpenAI: قلّل `NUM_HISTORY_RUNS`، أو انتقل لنموذج أرخص (`OPENAI_MODEL=gpt-4o-mini`).
- بطء ngrok المجاني شائع للإنتاج → انشر على نطاق ثابت (SETUP §8).

## 9) الصوت/الصورة لا تصل من الوكيل
- تأكد أن النموذج المختار متعدد الوسائط للاستقبال: الصور مدعومة في gpt-5.x؛ للملفات الصوتية الضخمة يعتمد النسخ على أداة `whisper-1` — إن ظهرت «unsupported» صدّر `ENABLE_IMAGE_GENERATION=1` (مفعّل افتراضياً) وتحقق أن مخرج الأدوات لا يرمي استثناءات: شغّل `TELEGRAM_SHOW_REASONING=1` مع `TELEGRAM_STREAMING=0` لترى رسائل الأداة كاملة.
- ملف أكبر من 20MB (حد التنزيل الرسمي للواجهة) → يُتجاهَل الوسائط ويبقى النص.
- حدود OpenAI لحسابك على `gpt-image-2`؟ جرّب: `python telegram_bot.py openai-check` ثم اطلب رسمة واحدة.

## 10) أخطاء مفاتيح OpenAI
- `401/429/insufficient_quota`: افحص `python telegram_bot.py openai-check` — يعرض قائمة النماذج المتاحة لحسابك ومقارنة `OPENAI_MODEL` بها.
- نموذج غير موجود عندك (`gpt-5.4-mini` مثلاً) → غيّر `OPENAI_MODEL` لقيمة تظهرها أداة الفحص.
- مفتاح معرّض في git عام؟ افتح حسابك وألغِه فوراً وأنشئ جديداً وحدّث `.env`.

## 11) تحديثات تتكرر / ردود مزدوجة
- كاش التكرار محلي 60 ثانية فقط: لا تُشغّل نسختين على نفس التوكن لنفس الـ prefix، ومع تعدد النسخ ضع replica واحدة على الأقل للـ webhook أو قسّم البوتات (multiple instances).
- أعد تشغيل السيرفر كثيراً؟ قد تعيد تيليجرام دفع تحديثات قديمة مكدسة — نظّف: `python telegram_bot.py delete-webhook` ثم أعد التسجيل.

## 12) فحص نهائي سريع (شبكة الأمان)
```bash
python tests/test_smoke.py             # اختبار منطق التوصيل (بدون شبكة)
python telegram_bot.py telegram-check  # التوكن + حالة الـ webhook
python telegram_bot.py openai-check    # المفتاح + النماذج
curl -sS "https://api.telegram.org/bot$TELEGRAM_TOKEN/getWebhookInfo" | python3 -m json.tool
```
