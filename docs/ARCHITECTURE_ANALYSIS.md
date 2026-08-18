# 🏗 گزارش تحلیل معماری کامل LearnQuest
### قبل از اجرای سیستم اقتصاد/فروشگاه — گام ۱
> وضعیت: **فقط تحلیل — هنوز هیچ کدی تغییر نکرده.** پیاده‌سازی پس از تأیید شما.

---

## ۱) نقشهٔ معماری فعلی

### اپ‌های نصب‌شده (`INSTALLED_APPS`)

| اپ | نقش | مدل‌های کلیدی | وضعیت |
|---|---|---|---|
| `user` | احراز هویت، پروفایل، OTP | `CustomUser` (xp/level/points/coins/streak), `PasswordResetOTP`, `UserActivity` | فعال |
| `Home` | صفحات لندینگ، هب بازی‌ها، پروفایل | — (بدون مدل) | فعال |
| `Game` | ۱۰ بازی + آمار + دستاورد | `UserGameStats`, `UserAchievement` | فعال |
| `language` | بازی‌های واژگانی (Drag&Drop، حدس، جورچین، شکار کلمه) | `Word` (۵۵۹ کلمه لود شده) | فعال |
| `language_academy` | قلب آموزشی: نقشه جهان/فصل/درس/کوئیز/امتحان/Marking CMS | ۲۷+ مدل (World…DailyGoal) | فعال |
| `blog` | مقالات + نظرات (با گارد ML) | `Category`, `Article`, `Comment` | فعال |
| `Messenger` | چت رمزنگاری‌شده (Encryption از SECRET_KEY مشتق) + WebSocket | `Conversation`, `Message` | فعال |
| `programapp_module` | ابزارهای ریاضی (ماشین‌حساب و…) | بدون مدل | فعال (غیرمرتبط با گیمیفیکیشن) |
| `ContactUs` | فرم تماس | `ContactModel` | فعال |
| `moderation_ml` | گارد محتوای ML روی چت/کامنت (PHICAD v2) | بدون مدل | فعال |
| — | `educational_platform` | — | **کد مرده** (در INSTALLED_APPS نیست) |

### جریان‌های اصلی
1. **ثبت‌نام/ورود** → فرم‌های Django کلاسیک + کد تأیید ۶رقمی (از طریق Console Email فقط چاپ می‌شود).
2. **آکادمی** → World ← Chapter ← Lesson ← (LessonContent, Quiz 1-1, Vocab) و Exam در سطح Chapter/World؛ پیشرفت با `UserLessonProgress/Chapter/World`؛ پاداش XP/coins در `submit_quiz` / `submit_quiz_auto` / `submit_exam*`.
3. **بازی‌ها** → قالب JS سمت کلاینت رکورد می‌سازد → `POST save_*_score` → `UserGameStats` + XP + `UserActivity` + `UserAchievement`.
4. **پروفایل** → نمایش xp/level/coins/points (coins و points عملاً بدون مصرف‌کننده‌اند).
5. **گارد محتوا** → `check_text()` قبل از ذخیرهٔ پیام/کامنت (دو نما + ضددورزدن) — این بخش دست‌نخورده می‌ماند.

---

## ۲) سیستم گیمیفیکیشن فعلی (موجودی‌ها)

| قابلیت | وضعیت فعلی | مشکل |
|---|---|---|
| XP | فیلد `CustomUser.xp` + `add_xp()` | بدون دفتر حسابداری/لاگ، بدون قانون قابل‌تنظیم |
| Level | هر ۲۰۰ XP یک سطح، سقف ۲۰ | `profile_view` با **۱۰۰** حساب می‌کند (ناهماهنگی ⇒ درصد اشتباه) |
| Coins | فیلد `coins`؛ فقط از کوئیز/امتحان | **هیچ مصرفی ندارد** |
| Points | فیلد `points` | **کاملاً بلااستفاده** |
| Streak | فیلد `streak` | **هیچ‌جا آپدیت نمی‌شود** |
| دستاوردها | `UserAchievement` (بازی‌ها) + `Badge/UserBadge` (آکادمی) | دو سیستم موازی ناسازگار |
| هدف روزانه | `DailyGoal` (پر می‌شود در کوئیز) | بدون پاداش تکمیل، بدون ریست خودکار |
| Leaderboard | — | **وجود ندارد** (حتی ویو/قالب) |
| فروشگاه/موجودی از قبیل کیف پول | — | وجود ندارد |

---

## ۳) ضعف‌ها و باگ‌های پیدا شده (غیرامنیتی)

1. **ناسازگاری فرمول لِوِل**: مدل ۲۰۰XP/سطح، پروفایل ۱۰۰ فرض می‌کند → نوار پیشرفت غلط.
2. **کد تأیید ثبت‌نام هیچ‌وقت چک نمی‌شود** (`is_verified` همیشه False می‌ماند) → جریان تأیید ایمیل ناتمام.
3. `add_xp()` ابتدا `save()` می‌کند و بعد سطح را آپدیت می‌کند؛ در بعضی مسیرها `save()` دوم نیامده و لِوِل ممکن است عقب بیفتد (ناسازگاری داده‌ای).
4. **کد مرده**: اپ `educational_platform`، فایل یتیم `articles.db`، سطر کامنت‌شده‌ی `UserActivity` در `login_view`.
5. `bare except` در `profile_view` و `edit_profile` → خطاها خاموش می‌شوند.
6. قالب `games.html` به URL وجودندارد `games` لینک می‌دهد در برخی مسیرها بدون namespace ثابت (امکان شکست در prefix تغییر) — ناچیز.
7. گزارش‌دهی یکتای رکوردها: برخی بازی‌های language ساختار ذخیرهٔ متفاوتی نسبت به Game دارند (تکرار منطق در ۱۰ نقطه).

---

## ۴) مسائل امنیتی (بحرانی‌ترین‌ها اول)

### 🔴 بحرانی
1. **فارم نامحدود XP از API بازی‌ها** — `POST /games/save-*-score/` مقدار `score` را از کلاینت می‌گیرد و بدون اعتبارسنجی، برای هر بازیٔ completed تا ~۶۰XP پاداش می‌دهد. با اسکریپت ساده می‌توان **در هر ثانیه چند صد XP** گرفت؛ `games_completed` هم بالا می‌رود و دستاوردها خودکار باز می‌شوند. راه‌حل: سقف سرورساید پاداش/روز + محدودیت تعداد ثبت رکورد معتبر + اعتبارسنجی حداقلی نمره (شکست‌نماید‌شدنی نبودن امتیاز).
2. **پاداش کوئیز/امتحان در هر تلاشِ پاس‌شده تکرار می‌شود** — `submit_quiz` و `submit_quiz_auto` فقط روی `xp_earned==0` برای *درس* چک دارند ولی **XP/skk کوئیز در همهٔ تلاش‌ها مجدد واریز می‌شود** (با max_attempts=۳ سه‌برابر). راه‌حل: پادش فقط «اولین پاس» + محدودیت یکتا روی (user, quiz, reward_type).
3. **17 نقطهٔ `@csrf_exempt`** در endpointهای امتیاز (`Game/views.py` ۱۱تا + `language/views.py` ۶تا) → حذف CSRF برای راحتی fetch. راه‌حل: حذف csrf_exempt + ارسال توکن از قالب (meta + header `X-CSRFToken`).
4. **Race Condition در واریز** — همه‌جا الگوی `user.xp += n; user.save()` است. دو درخواست همزمان ⇒ از دست رفتن یک واریز / خرید دوباره. راه‌حل: `F()` expressions + `select_for_update` در تراکنش.
5. **کیف پول موجود نیست** → هرگونه مغایرت/واریز اشتباه قابل ردیابی نیست (بدون دفتر حسابداری).

### 🟠 مهم
6. `SECRET_KEY` پیش‌فرض Django در `settings.py` هاردکد (و در گیت) — کلید رمزنگاری پیام‌ها هم از آن مشتق می‌شود ⇒ درز SECRET_KEY = خوانایی تمام چت‌ها.
7. `DEBUG=True` + `ALLOWED_HOSTS=[]` در تنظیمات اصلی (production-ready نیست؛ صفحات خطا داده لو می‌دهند).
8. **Rate limiting وجود ندارد** در هیچ endpoint حساسی (OTP، لاگین، ثبت‌نام، امتیازها) → Bot farming/Brute force ممکن. LocMemCache هم تک‌پروسه است (برای آیندهٔ چندکارگزاری نامناسب).
9. OTP بازنشانی فقط ۱۰ دقیقه است ولی **بدون محدودیت تلاش**؛ کد تأیید ایمیل ۲۴ ساعت عمر دارد و هیچ‌کجا اجبار/مصرف نمی‌شود.
10. برخی endpointهای JSON اطلاعات کاربر را بدون بررسی مالکیت آبجکت می‌گیرند (مثلاً الگوی `conversation_id` الان اوکی است ولی باید برای آیتم‌های جدید اصل IDOR صراحتاً رعایت شود — خرید/equip/consume فقط روی آبجکت خودِ کاربر).
11. افزایش `views`/`likes` مقاله بدون throttle (آمار ساده‌اند؛ کم‌خطر ولی قابل پمپ).
12. قالب‌ها کلی `|safe` ندارند ولی برای فروشگاه باید تصویر/توضیح محصول sanitize/render استاندارد بماند (خطای رایج آینده).

### جزئی
13. لاگ‌گذاری اقتصادی وجود ندارد (برای audit خرید/refund باید جدول رویداد ثابت شود).
14. InMemory Channel Layer برای چت — تک‌نودی (مقیاس‌پذیری آینده).

---

## ۵) مشکلات عملکرد و دیتابیس

1. **ایندکس‌ها**: برای Leaderboard فیلدهای `xp`/`coins` هیچ ایندکسی ندارند؛ `UserGameStats(user,game)` یکتاست ولی بدون ایندکس جداگانه؛ `UserActivity.created_at` مرتب‌سازی بدون ایندکس ترکیبی.
2. **N+1** در بخش‌هایی مثل لیست مقالات/نظرات و داشبورد آکادمی (بعضی جاها select_related کم است؛ نمایندهٔ آن `blog_home` و لیست کامنت‌هاست).
3. کوئری محاسبات چپتر/جهان (`update_progress`) سنگین و تکراری است → بعداً با سیگنال/کَش.
4. پیجینیشن در لیست‌ها (مقالات، واژگان، بازی‌ها) وجود ندارد — بعد از رشد داده مشکل می‌شود.
5. SQLite + WAL فعلی برای هم‌زمانی بالای خرید شکننده است؛ باید `atomic` + `select_for_update` و الگوی تراکنش‌محور لحاظ شود (و مسیر مهاجرت به Postgres باز بماند — همه‌چیز ORM-سازگار نگه‌داشته می‌شود).

---

## ۶) معماری هدف پیشنهادی (بدون شکستن ساختار فعلی)

سه اپ جدید + چند افزونهٔ کوچک به اپ‌های موجود. **هیچ مدل/فیلد فعلی حذف نمی‌شود**؛ فیلدهای `xp/coins/level/points` به‌عنوان «نمایش‌دهندهِ کش» از کیف پول/لجر جدید همگام نگه‌داشته می‌شوند (backfill یک‌باره + سینک سرویس‌لِیر).

### اپ `economy` (بهمنِ اقتصاد — منبع واحد حقیقت)
- `Wallet` (1-1 با کاربر): `coins_balance`, `gems(اختیاری, فاز بعد)`, `created/updated`. ← **فقط Ledger می‌نویسد**.
- `Transaction` (تغییرناپذیر/Immutable): کاربر، نوع (`earn|spend|reward|refund|admin_adjust|consume`), ارز (`coin|xp`), مقدار (+/−), موجودی‌بعدازتراکنش، `idempotency_key` (یکتا، ضد replay/double-submit), منبع (`quiz/game/mission/shop/admin/...`), `source_id`, متادیتا JSON، زمان.
- `XPRule` / `CoinRule` (پیکربندی‌پذیر در ادمین): کد فعالیت (`lesson_complete`, `quiz_perfect`, `game:snake`, `daily_login`…), مقدار، سقف/روز، فعال/غیرفعال.
- `AuditLog`: هر رویداد حساس (خرید، refund، تغییر دستی ادمین، مصرف آیتم، بلاک/مجازات) با actor و IP/user agent.
- `RewardGrant` (سند صدور پاداش — ایندکس یکتا روی (user, rule, period/source) برای «یک‌بار در روز/در کوئیز») — ضد duplicate reward.
- `LeaderboardEntry` کش‌محور (weekly/seasonal/global با snapshot دوره‌ای) — برای رتبه‌بندی بدون کوئری سنگین.
- `StatisticsDaily` (تجمیع روزانهٔ تعداد فعالیت‌ها برای نمودارهای پروفایل).
- سرویس‌لِیر (`services.py`): `grant_xp/grant_coins/spend/refund` همه `atomic + select_for_update(Wallet)` + ثبت Transaction + اعمال booster (ضریب XP/سکه از آیتم‌های مصرفی فعال) + بررسی سقف روزانه از XPRule.

### اپ `shop` (کاتالوگ + خرید + موجودی)
- `Category` (سلسله‌مراتب، آیکون، ترتیب).
- `Product`: نوع (`cosmetic|consumable|booster|unlock|bundle|currency_pack(فازبعد)`), **effect_type** (رجیستری رفتاری — مهم‌ترین فیلد؛ مثل `frame`, `theme`, `username_color`, `xp_booster`, `hint_ticket`, `unlock_lesson`, `pet`…), `effect_payload` JSON (id درس/حداقل ضریب/مدت booster/رنگ…), قیمت، تخفیف (٪ + بازه‌ی زمانی), موجودی/محدود(global stock + per_user_limit)، بازهٔ زمانه‌فروختن ( featured/limited/seasonal )، تصویر، توضیح، preview JSON، bundle (M2M به خود).
- `Purchase`: کاربر، محصول، قیمت‌لحظه‌خرید، وضعیت (`completed|refunded|failed`)، `idempotency_key` یکتا (ضد دابل‌کلیک/ریفرش)، تراکنش مرتبط، زمان، سند bundle.
- `InventoryItem`: کاربر↔محصول، `quantity` (consumable‌ها)، `equipped` (آرایشی‌ها — **یک unique constraint به‌ازای (user, slot)** تا فقط یک فریم/تم/رنگ فعال باشد)، `acquired_at`, `used_at`.
- `Wishlist`, `RecentlyViewed` (شِما سبک با تابع پاک‌سازی).
- رجیستری `effects/` (Strategy Pattern): هر `effect_type` یک handler: `can_use/equip/unequip/consume/apply_bonus/render_badge_data` → اتصال تمیز محصول به بقیهٔ سایت.

### اپ `missions` (فعالیت‌محوری)
- `Mission` (daily/weekly/seasonal/event): شرط JSON (کد رویداد + تعداد هدف)، پاداش XP/skk، بازه، `is_active`.
- `MissionProgress` (user, mission, period_key): شمارندهٔ پیشرفت، وضعیت (`active|claimable|claimed|expired`) → جلوگیری از claim تکراری با unique (user, mission, period).
- `Season/Event` + `SeasonPass` (DM: ردیف مرتبط محصول «Season Pass»؛ سطح پِس و پاداش‌های هر پله).
- `DailyRewardSchedule` (۷-۱۴ روزه با streak) + `LoginStreakLog`.
- هوک: `EventBus.dispatch(code, user, amount)` که از درس/کوئیز/بازی/لاگین/خرید صدا زده می‌شود و پیشروی مأموریت‌ها را آپدیت می‌کند (یک نقطهٔ اتصال واحد — همهٔ جایزه‌دهنده‌ها به آن وصل می‌شوند).

### افزونه‌ها به اپ‌های موجود (backward-compatible)
- `user`: فیلدهای نمایشی پروفایل (`active_frame`, `active_theme`, `username_color`, `active_badge_set`, `active_pet`) → از `InventoryItem.equipped` پر می‌شوند (فقط خواندنی در ادمین کاربر، تغییر فقط از طریق endpoint «تنظیمات ظاهری» با چک مالکیت).
- `language_academy`: تزریق درگاه «unlock» در `lesson_detail/world_map` (درس Exclusive با قفل)، `retry_ticket` به بازپخش‌کردن کوئیز بعد از اتمام تلاش‌ها، `hint_ticket` در UI کوئیز، `extra_time` تغییر تایمر (فیلد ارثی روی QuizSession).
- `Game`: پاداش‌ها از مسیر `economy.services.grant_xp` با XPRule + سقف روزانه + sanity-score پلن می‌شود (حد حداکثر امتیاز باورپذیر هر بازی تعریف ‌shode).
- `Home`/قالب‌ها: context processor که `wallet + equipped cosmetics + unread missions count` را به همهٔ قالب‌ها می‌دهد (فریم/رنگ نام/تم در navbar و پروفایل اعمال می‌شود).

---

## ۷) سازوکار صحت اقتصاد (ECONOMY INTEGRITY)

1. **Ledger-only** — موجودی هرگز مستقیم UPDATE نمی‌شود؛ تابع جرای که در تراکنش `Wallet` را `select_for_update()` می‌گیرد، میزان را اعمال، **موجودی قفل‌شده را روی خود تراکنش ثبت**، و بعد ذخیره ⇒ خواندن موجودیت همیشه consistent (و قابل بازسازی از دفتر).
2. **Idempotency** — کلید یکتای سمت سرور (از session_user+action+nonce یا UUID کلاینت + unique constraint) برای خرید/consum/claim. دابل‌کلیک‌ها `IntegrityError` می‌خورند و یک پاسخ امن برمی‌گردد.
3. **عدم منفی** — چک `balance >= price` داخل همان تراکنش؛ constraint دیتابیسی `CHECK(balance>=0)` در کوئریِ مهاجرت.
4. **قفل موجودی فروشگاهی** — محصول‌های limited: شمارندهٔ `sold_count` با `F('sold_count')+1` در تراکنش + چک `sold_count < stock_limit` (ضد oversell).
5. **Atomic bundling** — خرید باندِل: کسر سکه + صدور N آیتم در **یک** `atomic()`؛ هر خطا → rollback کامل.
6. **رویداد واریز یک‌بار** — `RewardGrant` با UniqueConstraint روی `(user, rule_code, period_key)` ⇒ تکرار claim/تلاش همزمان = خطای یکتا → «قبلاً گرفته شده».
7. **ممیز** — همهٔ تغییر دستی ادمین (adjust/refund) الزاماً `AuditLog` با دلیل و actor.
8. **Anti-farming** — سقف روزانهٔ هر XPRule (پیش‌فرض بازی‌ها: ۳ بازی معتبر/روز + یک سقف جمع XP بازی/روز)، بررسی امتیاز حداکثر منطقی، معدل‌سازی زمان بازی، شناسایی الگوی ربات (نمایه‌شدن‌گر simple در audit).
9. **سرورساید همیشه** — قیمت فقط از DB خوانده می‌شود؛ کلاینت هرگز `price`/`quantity` اثرگذار نمی‌فرستد.

---

## ۸) نگاشتِ «قابل استفاده شدن محصول در کل سایت»

| نوع محصول (effect_type) | رفتار پس از خرید | محل استفاده |
|---|---|---|
| `frame` / `frame_animated` | Inventory + قابل Equip | پروفایل، لیدربرد، نظرات بلاگ، چت (آواتار کاربر با فریم CSS/SVG) |
| `avatar_premium` | آیتم آواتار → انتخاب در تنظیمات | همان‌جاها |
| `avatar_decoration` | Equip (تا ۲ اسلات) | پروفایل/لیدربرد |
| `username_color` | Equip | نمایش نام در navbar، لیدربرد، کامنت‌ها |
| `profile_background` / `profile_card` / `profile_effect` | Equip | صفحهٔ پروفایل (بک‌گراند/افکت‌حرکت) |
| `theme` / `theme_dark_variant` | فعال‌سازی تم | تمام سایت (کلاس body + CSS variableها — `base.html` و `base_academy.html`) |
| `badge` / `title` | انتخاب نمایش | پروفایل/کامنت/لیدربرد (کنار نام) |
| `emoji_pack` / `sticker_pack` | فعال در پنل ایموجی | کامنت بلاگ + پیام‌رسان |
| `music_pack` / `wallpaper_pack` | Unlock لیست دانلود/پخش | صفحهٔ Library کاربر |
| `language_pack` / `grammar_pack` / `vocab_pack` / `listening` / `speaking` / `writing` / `pronunciation_pack` | Unlock محتوا | در آکادمی (World/Chapter نمایش داده، دررس/تمرین ویژه باز می‌شود) |
| `exclusive_lesson` / `course` / `minigame` / `practice_pack` | Unlock موجودیت هدف در `effect_payload` | نقشه/بازی‌ها — همان صفحه، قفل باز |
| `pet` / `pet_skin` / `pet_accessory` | انتخاب/Equip | پروفایل + نمایش کوچک در داشبورد؛ (لواجیک تغذیه/سطح در فاز بعد) |
| `xp_booster` / `coin_booster` | Consumable → `ActiveBoost(expires_at, multiplier)` | سرویس grant در واریز اعمال می‌کند (همهٔ منابع) |
| `hint_ticket` | مصرف داخل کوئیز: حذف ۲ گزینهٔ غلط | `quiz_take` (دکمه، با چک موجودی سرور) |
| `retry_ticket` | +۱ تلاش جدید برای کوئیز/امتحان | submit error page/ take_quiz |
| `extra_hearts`(بازی‌های آتی)/`time_ext` | مصرف در بازی/کوئیز | همان صفحه |
| `mystery_box` | Consumable → جدول جایزهٔ وزن‌دار سرور (با Transaction جداگانه) | Inventory صفحهٔ «باز کردن» |
| `lucky_spin` | مصرف → چرخ سرور (همان الگو) | صفحهٔ گردونه |
| `certificate_special` | صدور Certificate ویژه | صفحهٔ گواهینامه‌ها |
| `season_pass` | فعال‌سازی پِس | اپ missions |
| `event_reward`/limited cosmetics | عادی مثل بالا | — |
| (آینده) محصولی جدید | فقط یک handler جدید در رجیستری + effect_type در ادمین — **بدون تغییر کد اصلی** |

---

## ۹) نقشهٔ راه پیاده‌سازی (فازبندی پیشنهادی)

| فاز | محتوا | خروجی ملموس |
|---|---|---|
| **0 — آماده‌سازی** | پاک‌سازی اشکال جزئی (فرمول لول در پروفایل)، مهاجرت SECRET_KEY به env، فعال‌سازی CSRF روی ۱۷ endpoint (تزریق توکن در قالب‌ها) | سبد security hygiene (۰ ریسک رفتاری) |
| **1 — Core Economy** | اپ `economy`: Wallet/Transaction/Rules/RewardGrant/Audit + Service layer + بک‌فیل از `user.coins/xp` + سینک فیلدها + انتقال واریزهای موجود (quiz/game/language) به services با سقف روزانه + پاداش «اولین‌بار» برای کوئیز | XP/سکه شفاف، ضد‌دابل، ضد‌فارم؛ همهٔ پاداش‌ها از یک کانال |
| **2 — Shop پایه** | اپ `shop`: مدل‌ها، ادمین، صفحات (خانهٔ فروشگاه با فیلتر/جستجو/سورت)، خرید امن، Inventory + equip/unequip، Purchase history، صفحهٔ محصول با preview، wishlist | فروشگاه کامل برای محصول‌های آرایشی اصلی (فریم/آواتار/رنگ/تم/بج) |
| **3 — Consumables/Unlock** | رجیستری effects + booster (cxp/ccoin)، hint/retry/time، mystery box (جدول وزن‌دار)، lucky spin، unlock محتوا در آکادمی | آیتم‌های قابل مصرف و بازکردن واقعی در جای خودشان |
| **4 — Missions/Rewards** | اپ `missions`: DailyReward+streak واقعی، Daily&Weekly missions + claim، سیستم EventBus اتصال از همهٔ فعالیت‌ها | انگیزهٔ روزانه پایدار |
| **5 — Leaderboard/Stats/Season** | لیدربرد هفتگی/فصلی کش‌شده، صفحهٔ آمار پیشرفتهٔ کاربر، Season & Season pass فعال | فصل اول + نمایش رتبه در navbar/پروفایل |
| **6 — پت‌ها + زبان/رسانه پک‌ها + پولیش** | پت مجازی پایه (سطح/تغذیهٔ ساده)، music/wallpaper packs، صفحهٔ Library، تست e2e امنیتی (تلاش تقلب‌ها) | کامل شدن کاتالوگ |

> اندازهٔ هر فاز ~ یک تحویل مستقل و قابل تست (بدون شکستن ورژن فعلی؛ هر فاز migration و seed جدا).

---

## ۱۰) تصمیماتی که قبل از شروع لازم است (تأیید شما)

1. **دامنهٔ این تحویل**: همهٔ فازهای ۱ تا ۶ یک‌جا؟ یا فاز ۱–۳ (اقتصاد+فروشگاه+مصرفی‌ها) به‌عنوان نسخهٔ اول؟
2. **ارزها**: فقط سکه + XP؟ (Gem/الماس به‌عنوان ارز پولی آینده — فعلاً فیلد رزرو بگذارم؟)
3. **اقتصاد پاداش اولیه**: یک نرخ‌نامهٔ پیش‌فرض می‌سازم (درس=۳۰XP، کوئیز=۳۰XP/۱۵🪙، بازی روزانه سقف ۳ بار، ورود روزانه پلکانی +۵..+۵۰🪙…) — اوکی؟
4. **مجلهٔ اولیهٔ فروشگاه**: دیتا سید کنم برای ~۴۰ محصول از دسته‌بندی‌های لیست شما؟ (با تصاویر placeholder تولیدشده + قیمت نمونه)
5. **پت مجازی**: اولویت دارد (فاز اوّل) یا آخر؟
6. **سیزن‌پس/ایونت**: الان اسکلت یا کامل؟
7. Backend پرداخت واقعی (واوچر/کد) — آیا می‌خواهید خرید با پول واقعی هم لحاظ شود یا فعلاً سکهٔ درون‌برنامه کافی است؟

---
*تهیه‌شده پس از خواندن کامل ۹۴ قالب، ۲۷+ مدل academy و تمام ویوها/مدل‌های ۱۱ اپ.*
