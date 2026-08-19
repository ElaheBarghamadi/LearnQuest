# -*- coding: utf-8 -*-
"""
بانک محتوای آکادمی — نکات گرامری (الهام‌گرفته از English Grammar in Use — Raymond Murphy)
هر درس ۱ تا ۲ گرامر با توضیح کامل، فرمول، مثال دوزبانه، اشتباهات رایج و نکات کاربردی.
"""

GRAMMAR_BANK = {
    # ============================================================
    # WORLD 1 — AIRPORT ADVENTURES (A1)
    # ============================================================
    "present_simple_to_be": {
        "title": "Present Simple — Verb «To Be»",
        "title_fa": "حال ساده — فعل «بودن»",
        "level": "A1",
        "structure": "I am / You are / He-She-It is / We-They are  |  Am I? Are you? Is he?",
        "explanation": (
            "<p>حال سادهٔ فعل <b>to be</b> برای بیان وضعیت، شغل، مکان و معرفی خودمان به کار می‌رود. "
            "این اولین و مهم‌ترین گرامر برای شروع مکالمه است (Grammar in Use — Unit 1).</p>"
            "<p><b>مثبت:</b> I <strong>am</strong> a passenger. · You <strong>are</strong> at the airport. "
            "· He <strong>is</strong> in the terminal.</p>"
            "<p><b>منفی:</b> I <strong>am not</strong> late. · She <strong>is not</strong> at the gate.</p>"
            "<p><b>سوالی:</b> <strong>Am</strong> I at the right gate? · <strong>Are</strong> you ready to board? "
            "· <strong>Is</strong> this your flight?</p>"
        ),
        "examples": [
            {"en": "I am a passenger on flight 2025.", "fa": "من مسافر پرواز ۲۰۲۵ هستم."},
            {"en": "The gate is at the end of the terminal.", "fa": "گیت انتهای ترمینال است."},
            {"en": "We are waiting for the boarding announcement.", "fa": "ما منتظر اعلام سوار شدن هستیم."},
            {"en": "Are you traveling alone?", "fa": "آیا تنها سفر می‌کنی؟"},
            {"en": "The flight is not on time today.", "fa": "پرواز امروز به‌موقع نیست."},
        ],
        "common_mistakes": (
            "«I is» یا «You is» نگویید — با I همیشه am و با You همیشه are می‌آید. "
            "در سوال، فعل را اول جمله بیاورید: «Are you ready?» نه «You are ready?»"
        ),
        "usage_tips": (
            "برای معرفی: «I am a student.» · برای مکان: «The hotel is near the airport.» · "
            "برای سن: «I am twenty years old.» در مکالمهٔ روزمره، فرم کوتاه خیلی رایج است: I'm, You're, He's."
        ),
    },
    "present_simple_actions": {
        "title": "Present Simple — Actions & Routines",
        "title_fa": "حال ساده — کارهای روزمره",
        "level": "A1",
        "structure": "Subject + verb(+s/es)  |  He/She/It + verb+s  |  Do/Does + subject + verb?",
        "explanation": (
            "<p>حال ساده برای عادت‌ها، کارهای روزمره و حقایق عمومی استفاده می‌شود (Grammar in Use — Unit 2). "
            "برای سوم‌شخص مفرد (he/she/it) به فعل <b>s/es</b> اضافه می‌شود.</p>"
            "<p><b>مثبت:</b> I <strong>check in</strong> online. · She <strong>travels</strong> every month.</p>"
            "<p><b>منفی:</b> I <strong>don't</strong> like delays. · He <strong>doesn't</strong> smoke.</p>"
            "<p><b>سوالی:</b> <strong>Do</strong> you have a passport? · <strong>Does</strong> the flight leave at 9?</p>"
        ),
        "examples": [
            {"en": "I always arrive two hours before my flight.", "fa": "من همیشه دو ساعت قبل از پروازم می‌رسم."},
            {"en": "She travels to London every summer.", "fa": "او هر تابستان به لندن سفر می‌کند."},
            {"en": "The plane leaves at 10:30 AM.", "fa": "هواپیما ساعت ۱۰:۳۰ صبح حرکت می‌کند."},
            {"en": "Do you usually book your tickets online?", "fa": "آیا معمولاً بلیطت را آنلاین رزرو می‌کنی؟"},
            {"en": "He doesn't like window seats.", "fa": "او صندلی کنار پنجره را دوست ندارد."},
        ],
        "common_mistakes": (
            "فراموش نکنید برای he/she/it به فعل s اضافه کنید: «She travel<u>s</u>» نه «She travel». "
            "در سوال و منفی با does، فعل s نمی‌گیرد: «Does she travel?» نه «Does she travels?»"
        ),
        "usage_tips": (
            "برای عادت‌ها از قیدهای تکرار استفاده کنید: always, usually, often, sometimes, never — "
            "این قیدها قبل از فعل اصلی می‌آیند: «I always check my bags.»"
        ),
    },
    "present_continuous": {
        "title": "Present Continuous — Actions Now",
        "title_fa": "حال استمراری — کار در حال انجام",
        "level": "A1",
        "structure": "am/is/are + verb-ing",
        "explanation": (
            "<p>حال استمراری برای کاری که <b>همین حالا</b> در حال انجام است به کار می‌رود (Grammar in Use — Unit 3). "
            "همچنین برای برنامه‌های قطعی نزدیک (مثل پرواز) استفاده می‌شود.</p>"
            "<p><b>مثبت:</b> The plane <strong>is taking off</strong> now. · I <strong>am boarding</strong>.</p>"
            "<p><b>منفی:</b> They <strong>are not flying</strong> today.</p>"
            "<p><b>سوالی:</b> <strong>Is</strong> the flight <strong>delaying</strong>? · <strong>Are</strong> you <strong>waiting</strong>?</p>"
        ),
        "examples": [
            {"en": "The passengers are boarding now.", "fa": "مسافران همین حالا سوار می‌شوند."},
            {"en": "I am looking for my boarding pass.", "fa": "من دنبال کارت سوار شدنم می‌گردم."},
            {"en": "They are serving drinks on the plane.", "fa": "آن‌ها داخل هواپیما نوشیدنی سرو می‌کنند."},
            {"en": "Is the pilot speaking now?", "fa": "آیا خلبان الان صحبت می‌کند؟"},
            {"en": "We are not landing yet.", "fa": "ما هنوز فرود نمی‌آییم."},
        ],
        "common_mistakes": (
            "فراموش نکنید فعل to be را قبل از verb-ing بیاورید: «I am boarding» نه «I boarding». "
            "برای he/she/it از is و برای I از am استفاده کنید."
        ),
        "usage_tips": (
            "برای صحبت دربارهٔ پرواز و سفر عالی است: «We are landing in 20 minutes.» "
            "قیدهای now, right now, at the moment نشانهٔ این زمان هستند."
        ),
    },
    "past_simple": {
        "title": "Past Simple — Completed Actions",
        "title_fa": "گذشته ساده — کارهای تمام‌شده",
        "level": "A2",
        "structure": "Subject + verb-ed (یا بی‌قاعده)  |  Did + subject + verb?",
        "explanation": (
            "<p>گذشته ساده برای کارهایی که در زمان مشخصی در گذشته تمام شده‌اند (Grammar in Use — Unit 5). "
            "افعال منظم با ed- ساخته می‌شوند و افعال بی‌قاعده را باید حفظ کرد (go→went, fly→flew).</p>"
            "<p><b>مثبت:</b> We <strong>landed</strong> at 8 PM. · She <strong>went</strong> through security.</p>"
            "<p><b>منفی:</b> I <strong>didn't check</strong> my luggage.</p>"
            "<p><b>سوالی:</b> <strong>Did</strong> you <strong>enjoy</strong> the flight?</p>"
        ),
        "examples": [
            {"en": "The flight landed on time yesterday.", "fa": "پرواز دیروز به‌موقع فرود آمد."},
            {"en": "I flew to Tehran last week.", "fa": "من هفتهٔ پیش به تهران پرواز کردم."},
            {"en": "She lost her boarding pass at the airport.", "fa": "او کارت سوار شدنش را در فرودگاه گم کرد."},
            {"en": "Did you see the departure board?", "fa": "آیا تابلو پروازها را دیدی؟"},
            {"en": "They didn't wait at the gate.", "fa": "آن‌ها پشت گیت منتظر نماندند."},
        ],
        "common_mistakes": (
            "در منفی و سوال گذشته، فعل اصلی بدون تغییر می‌آید: «Did you go?» نه «Did you went?» "
            "افعال بی‌قاعده (went, flew, took, saw) را جداگانه تمرین کنید."
        ),
        "usage_tips": (
            "قیدهای yesterday, last week, two days ago نشانهٔ گذشته ساده‌اند. "
            "برای تعریف سفرهای گذشته این زمان را حتماً بلد باشید."
        ),
    },
    "past_continuous": {
        "title": "Past Continuous — Actions in Progress in the Past",
        "title_fa": "گذشته استمراری — کار در جریان در گذشته",
        "level": "A2",
        "structure": "was/were + verb-ing",
        "explanation": (
            "<p>گذشته استمراری برای کاری که در یک لحظهٔ خاص در گذشته در حال انجام بود (Grammar in Use — Unit 6). "
            "معمولاً با گذشته ساده هم‌آیی می‌شود: کار در جریان + اتفاقی که وسطش افتاد.</p>"
            "<p><b>مثال ترکیبی:</b> I <strong>was waiting</strong> at the gate <b>when</b> I <strong>heard</strong> the announcement.</p>"
            "<p>I <strong>was sleeping</strong> during the flight. · They <strong>were watching</strong> a movie when we landed.</p>"
        ),
        "examples": [
            {"en": "I was reading a book when the plane took off.", "fa": "داشتم کتاب می‌خواندم که هواپیما بلند شد."},
            {"en": "The passengers were sleeping during the night flight.", "fa": "مسافران در پرواز شبانه خواب بودند."},
            {"en": "She was talking to the flight attendant when I saw her.", "fa": "او با مهماندار صحبت می‌کرد که من او را دیدم."},
            {"en": "We weren't flying over the mountains at that time.", "fa": "ما در آن زمان روی کوه‌ها پرواز نمی‌کردیم."},
            {"en": "What were you doing when the announcement came?", "fa": "وقتی اعلام شد چه کار می‌کردی؟"},
        ],
        "common_mistakes": (
            "برای I/He/She/It از was و برای You/We/They از were استفاده کنید. "
            "فراموش نکنید که فعل اصلی ing می‌گیرد."
        ),
        "usage_tips": (
            "الگوی رایج: Past Continuous + when + Past Simple — «I was sleeping when you called.» "
            "این ساختار برای روایت داستان‌ها (Storytelling) خیلی مفید است."
        ),
    },
    "present_perfect": {
        "title": "Present Perfect — Life Experiences",
        "title_fa": "حال کامل — تجربه‌های زندگی",
        "level": "A2",
        "structure": "have/has + past participle (verb-ed / بی‌قاعده)",
        "explanation": (
            "<p>حال کامل برای تجربه‌هایی که زمان دقیقشان مهم نیست یا کاری که در گذشته شروع شده و هنوز ادامه دارد "
            "(Grammar in Use — Units 7-8). در سفر و مکالمه خیلی پرکاربرد است.</p>"
            "<p><b>تجربه:</b> I <strong>have flown</strong> to many countries.</p>"
            "<p><b>ادامه‌دار:</b> She <strong>has lived</strong> in this city for 5 years.</p>"
            "<p><b>منفی:</b> I <strong>have never been</strong> to Japan.</p>"
            "<p><b>سوالی:</b> <strong>Have</strong> you ever <strong>traveled</strong> alone?</p>"
        ),
        "examples": [
            {"en": "I have traveled to three continents.", "fa": "من به سه قاره سفر کرده‌ام."},
            {"en": "She has never missed a flight.", "fa": "او هیچ‌وقت پروازش را از دست نداده است."},
            {"en": "Have you ever flown first class?", "fa": "تا به حال کلاس اول پرواز کرده‌ای؟"},
            {"en": "We have already checked in online.", "fa": "ما همین الان آنلاین چک‌این کرده‌ایم."},
            {"en": "He has just landed from Paris.", "fa": "او همین الان از پاریس فرود آمده."},
        ],
        "common_mistakes": (
            "بعد از have/has باید قسمت سوم فعل (past participle) بیاید: «I have seen» نه «I have saw». "
            "با ever/never/just/already از حال کامل استفاده کنید نه گذشته ساده."
        ),
        "usage_tips": (
            "ever برای سوال تجربه: «Have you ever…?» · never برای منفی تجربه: «I have never…» · "
            "just برای اتفاق لحظه‌ای: «The plane has just landed.»"
        ),
    },
    "future_will_going": {
        "title": "Future — Will & Be Going To",
        "title_fa": "آینده — Will و Be Going To",
        "level": "A2",
        "structure": "will + verb  |  am/is/are going to + verb",
        "explanation": (
            "<p>برای آینده دو ساختار اصلی داریم (Grammar in Use — Units 19-20):</p>"
            "<p><b>will</b> برای تصمیم لحظه‌ای، پیش‌بینی و قول: «I <strong>will help</strong> you with your bags.»</p>"
            "<p><b>be going to</b> برای برنامهٔ از قبل‌تعیین‌شده: «We <strong>are going to visit</strong> the museum tomorrow.»</p>"
            "<p>فرم کوتاه will: I'll, She'll, They'll — منفی: won't.</p>"
        ),
        "examples": [
            {"en": "I will call you when I land.", "fa": "وقتی فرود بیایم بهت زنگ می‌زنم."},
            {"en": "The flight will be delayed because of the storm.", "fa": "پرواز به خاطر طوفان تأخیر خواهد داشت."},
            {"en": "We are going to rent a car at the airport.", "fa": "ما قصد داریم در فرودگاه ماشین کرایه کنیم."},
            {"en": "She is going to travel to Istanbul next month.", "fa": "او ماه آینده قصد سفر به استانبول را دارد."},
            {"en": "Don't worry, I won't be late.", "fa": "نگران نباش، دیر نمی‌کنم."},
        ],
        "common_mistakes": (
            "بعد از will و going to فعل بدون to می‌آید: «I will go» نه «I will to go». "
            "برای برنامهٔ قطعی از going to استفاده کنید، برای تصمیم لحظه‌ای will."
        ),
        "usage_tips": (
            "در فرودگاه زیاد می‌شنوید: «The flight will depart from gate 5.» · «We are going to begin boarding soon.» — "
            "این دو ساختار را برای برنامه‌ریزی سفر حتماً تمرین کنید."
        ),
    },
    "modals_can_must": {
        "title": "Modals — Can, Could, Must, Should",
        "title_fa": "افعال کمکی — Can، Could، Must، Should",
        "level": "A2",
        "structure": "can/could/must/should + verb (بدون to)",
        "explanation": (
            "<p>افعال کمکی برای توانایی، اجازه، الزام و توصیه (Grammar in Use — Units 26-32):</p>"
            "<p><b>can</b> = توانایی/اجازه: «You <strong>can</strong> take this seat.»</p>"
            "<p><b>could</b> = گذشتهٔ can / مودبانه: «<strong>Could</strong> I see your passport?»</p>"
            "<p><b>must</b> = الزام: «Passengers <strong>must</strong> fasten their seatbelts.»</p>"
            "<p><b>should</b> = توصیه: «You <strong>should</strong> arrive early.»</p>"
        ),
        "examples": [
            {"en": "You must show your passport at the counter.", "fa": "باید پاسپورتت را پشت میز نشان بدهی."},
            {"en": "Can I bring this bag on the plane?", "fa": "می‌توانم این کیف را داخل هواپیما بیاورم؟"},
            {"en": "Could you help me with my luggage, please?", "fa": "می‌شود لطفاً با چمدانم کمکم کنی؟"},
            {"en": "You should book your ticket in advance.", "fa": "بهتر است بلیطت را از قبل رزرو کنی."},
            {"en": "Passengers must turn off their phones.", "fa": "مسافران باید گوشی‌هایشان را خاموش کنند."},
        ],
        "common_mistakes": (
            "بعد از افعال کمکی فعل بدون to می‌آید: «You must show» نه «You must to show». "
            "سوم‌شخص s نمی‌گیرد: «She can go» نه «She cans go»."
        ),
        "usage_tips": (
            "در فرودگاه must را زیاد می‌شنوید (قوانین) و could برای درخواست مودبانه (گفتگو با مهماندار). "
            "این چهار فعل را با مثال‌های سفر حفظ کنید."
        ),
    },
    "comparatives": {
        "title": "Comparatives & Superlatives",
        "title_fa": "صفت‌های تفضیلی و عالی",
        "level": "A2",
        "structure": "adj+er than / more + adj than  |  the adj+est / the most + adj",
        "explanation": (
            "<p>برای مقایسهٔ دو چیز از تفضیلی (comparative) و برای برتری در یک گروه از عالی (superlative) استفاده می‌کنیم "
            "(Grammar in Use — Units 104-106).</p>"
            "<p><b>صفت کوتاه:</b> cheap → <strong>cheaper</strong> → the <strong>cheapest</strong></p>"
            "<p><b>صفت بلند:</b> expensive → <strong>more expensive</strong> → the <strong>most expensive</strong></p>"
            "<p><b>بی‌قاعده:</b> good → better → the best · bad → worse → the worst</p>"
        ),
        "examples": [
            {"en": "Economy class is cheaper than business class.", "fa": "اکونومی از بیزینس ارزان‌تر است."},
            {"en": "This airline is more reliable than the other one.", "fa": "این ایرلاین از آن یکی قابل‌اعتمادتر است."},
            {"en": "It's the fastest way to get to the city.", "fa": "این سریع‌ترین راه رسیدن به شهر است."},
            {"en": "My suitcase is heavier than yours.", "fa": "چمدان من از مال تو سنگین‌تر است."},
            {"en": "Dubai airport is one of the busiest airports in the world.", "fa": "فرودگاه دبی یکی از شلوغ‌ترین فرودگاه‌های جهان است."},
        ],
        "common_mistakes": (
            "برای صفت‌های کوتاه از more استفاده نکنید: «cheaper» نه «more cheap». "
            "فراموش نکنید بعد از comparative کلمهٔ than می‌آید."
        ),
        "usage_tips": (
            "در خرید بلیط و مقایسهٔ پروازها پرکاربرد است: «Which flight is cheaper?» · «The first flight is the most convenient.»"
        ),
    },
    # ============================================================
    # WORLD 2 — RESTAURANT & FOOD (A2)
    # ============================================================
    "some_any": {
        "title": "Some / Any / A / An — Countable & Uncountable",
        "title_fa": "Some و Any — اسم‌های شمارشی و ناشمارا",
        "level": "A2",
        "structure": "some + plural/uncountable (مثبت)  |  any + plural/uncountable (منفی/سوال)",
        "explanation": (
            "<p>برای مقدار نامشخص از some در جملات مثبت و any در منفی و سوال استفاده می‌کنیم "
            "(Grammar in Use — Units 76-77).</p>"
            "<p><b>شمارشی:</b> some apples · any oranges</p>"
            "<p><b>ناشمارا:</b> some water · any rice</p>"
            "<p><b>a/an</b> فقط برای مفرد شمارشی: a sandwich, an egg</p>"
            "<p>نکته: در سوال‌های پیشنهادی/درخواستی از some استفاده می‌شود: «Would you like some tea?»</p>"
        ),
        "examples": [
            {"en": "I'd like some water, please.", "fa": "یک کم آب می‌خواهم، لطفاً."},
            {"en": "Do you have any vegetarian dishes?", "fa": "آیا غذای گیاهی دارید؟"},
            {"en": "There isn't any sugar in my coffee.", "fa": "توی قهوه‌ام شکر نیست."},
            {"en": "We ordered some appetizers to share.", "fa": "ما چند پیش‌غذا برای تقسیم سفارش دادیم."},
            {"en": "Would you like some dessert?", "fa": "دسر میل دارید؟"},
        ],
        "common_mistakes": (
            "در جملات منفی از any استفاده کنید نه some: «There isn't any milk» نه «There isn't some milk». "
            "اسم‌های ناشمارا (water, rice, bread) جمع نمی‌گیرند: «some water» نه «some waters»."
        ),
        "usage_tips": (
            "در رستوران: «Can I have some bread?» · «Is there any salt on the table?» — "
            "این الگوها را تمرین کنید تا سفارش دادن راحت شود."
        ),
    },
    "countable_uncountable": {
        "title": "Countable vs Uncountable Nouns & Quantifiers",
        "title_fa": "اسم‌های شمارشی و ناشمارا + مقدارها",
        "level": "A2",
        "structure": "a few + countable  |  a little + uncountable  |  a lot of + هر دو",
        "explanation": (
            "<p>برای بیان مقدار از عبارت‌های کمی استفاده می‌کنیم (Grammar in Use — Units 78-79):</p>"
            "<p><b>a few</b> با اسم شمارشی (تعداد کم): a few cookies</p>"
            "<p><b>a little</b> با ناشمارا (مقدار کم): a little sugar</p>"
            "<p><b>much</b> با ناشمارا در منفی/سوال: How much milk?</p>"
            "<p><b>many</b> با شمارشی: How many eggs?</p>"
            "<p><b>a lot of / lots of</b> با هر دو: a lot of food</p>"
        ),
        "examples": [
            {"en": "How much does this meal cost?", "fa": "این غذا چقدر هزینه دارد؟"},
            {"en": "How many people are at the table?", "fa": "چند نفر سر میز هستند؟"},
            {"en": "There are a few empty tables by the window.", "fa": "چند میز خالی کنار پنجره هست."},
            {"en": "I'd like a little more rice, please.", "fa": "یک کم بیشتر برنج می‌خواهم."},
            {"en": "We have a lot of customers on weekends.", "fa": "ما آخر هفته‌ها مشتری زیاد داریم."},
        ],
        "common_mistakes": (
            "much با اسم شمارشی نمی‌آید: «How much apples?» ❌ → «How many apples?» ✅ "
            "a few با ناشمارا نمی‌آید: «a few water» ❌ → «a little water» ✅"
        ),
        "usage_tips": (
            "در رستوران برای سوال دربارهٔ مواد غذایی: «How much cheese is in this dish?» — "
            "تفاوت few/little را با مثال‌های غذایی یاد بگیرید."
        ),
    },
    "imperatives": {
        "title": "Imperatives — Giving Orders & Requests",
        "title_fa": "دستور و درخواست",
        "level": "A1",
        "structure": "Verb (بدون فاعل)  |  Don't + verb  |  Please + verb",
        "explanation": (
            "<p>برای دستور، پیشنهاد و درخواست از شکل سادهٔ فعل استفاده می‌کنیم (Grammar in Use — Unit 44). "
            "برای منفی از Don't استفاده می‌شود. «Please» آن را مودبانه می‌کند.</p>"
            "<p><b>دستور:</b> <strong>Bring</strong> the menu, please.</p>"
            "<p><b>منفی:</b> <strong>Don't</strong> eat too fast!</p>"
            "<p><b>پیشنهاد:</b> <strong>Try</strong> the grilled fish — it's delicious!</p>"
        ),
        "examples": [
            {"en": "Bring me the bill, please.", "fa": "صورتحساب را برایم بیاور."},
            {"en": "Don't forget to leave a tip.", "fa": "فراموش نکن انعام بگذاری."},
            {"en": "Try the traditional stew — it's amazing!", "fa": "خورش سنتی را امتحان کن — عالی است!"},
            {"en": "Please wait a moment.", "fa": "لطفاً یک لحظه صبر کنید."},
            {"en": "Enjoy your meal!", "fa": "نوش جان!"},
        ],
        "common_mistakes": (
            "برای منفی حتماً Don't بیاورید: «Don't be late» نه «No be late». "
            "فاعل در جملهٔ امری نمی‌آید: «Close the door» نه «You close the door» (در حالت عادی)."
        ),
        "usage_tips": (
            "در رستوران زیاد می‌شنوید: «Enjoy your meal», «Please sit anywhere you like» — "
            "و خودتان برای سفارش: «Give me the menu, please.»"
        ),
    },
    "would_like": {
        "title": "Would Like — Polite Offers & Orders",
        "title_fa": "Would Like — سفارش و پیشنهاد مودبانه",
        "level": "A1",
        "structure": "I would like (I'd like) + noun/to-verb  |  Would you like + noun?",
        "explanation": (
            "<p>«would like» به‌معنای «می‌خواهم» است ولی خیلی مودبانه‌تر از want است — مخصوصاً برای سفارش غذا "
            "(Grammar in Use — Unit 31).</p>"
            "<p><b>سفارش:</b> I <strong>'d like</strong> a chicken kebab, please.</p>"
            "<p><b>پیشنهاد:</b> <strong>Would you like</strong> something to drink?</p>"
            "<p><b>منفی:</b> I <strong>wouldn't like</strong> any dessert, thanks.</p>"
        ),
        "examples": [
            {"en": "I'd like to order a pizza, please.", "fa": "می‌خواهم پیتزا سفارش بدهم."},
            {"en": "Would you like anything to drink?", "fa": "چیزی برای نوشیدن میل دارید؟"},
            {"en": "She'd like the steak, well done.", "fa": "او استیک می‌خواهد، کاملاً پخته."},
            {"en": "We would like a table for two, please.", "fa": "یک میز دو نفره می‌خواهیم."},
            {"en": "Would you like to see the dessert menu?", "fa": "میل دارید منوی دسر را ببینید؟"},
        ],
        "common_mistakes": (
            "بعد از would like، فعل با to می‌آید: «I'd like to order» نه «I'd like order». "
            "فراموش نکنید would + like است نه will like."
        ),
        "usage_tips": (
            "این ساختار طلایی سفارش غذاست: «I'd like…» + «Would you like…?» — "
            "با این دو جمله می‌توانید کل یک وعده غذا را سفارش دهید."
        ),
    },
    "present_perfect_2": {
        "title": "Present Perfect with «Just / Already / Yet»",
        "title_fa": "حال کامل با Just، Already، Yet",
        "level": "A2",
        "structure": "have/has + past participle + just/already  |  haven't + yet (پایان جمله)",
        "explanation": (
            "<p>سه قید مهم با حال کامل (Grammar in Use — Unit 8):</p>"
            "<p><b>just</b> = همین الان: «The waiter has <strong>just</strong> brought the food.»</p>"
            "<p><b>already</b> = قبلاً (زودتر از انتظار): «We have <strong>already</strong> paid.»</p>"
            "<p><b>yet</b> = هنوز (منفی/سوال، آخر جمله): «I haven't eaten <strong>yet</strong>.»</p>"
        ),
        "examples": [
            {"en": "The food has just arrived.", "fa": "غذا همین الان رسید."},
            {"en": "I've already ordered dessert.", "fa": "من قبلاً دسر سفارش داده‌ام."},
            {"en": "Have you tried the new restaurant yet?", "fa": "تا حالا رستوران جدید را امتحان کرده‌ای؟"},
            {"en": "She hasn't paid the bill yet.", "fa": "او هنوز صورت‌حساب را پرداخت نکرده است."},
            {"en": "We've just finished our meal.", "fa": "ما همین الان غذایمان تمام شد."},
        ],
        "common_mistakes": (
            "yet فقط در منفی و سوال می‌آید و معمولاً آخر جمله است. "
            "just بین have و فعل اصلی می‌آید: «have just finished» نه «have finished just»."
        ),
        "usage_tips": (
            "در رستوران برای گزارش وضعیت: «We've just ordered» · «Have you paid yet?» — "
            "این قیدها مکالمه را طبیعی‌تر می‌کنند."
        ),
    },
    "passive": {
        "title": "Passive Voice — Simple Present & Past",
        "title_fa": "مجهول — حال و گذشته ساده",
        "level": "B1",
        "structure": "am/is/are + past participle  |  was/were + past participle",
        "explanation": (
            "<p>وقتی فاعلِ انجام‌دهنده مهم نیست یا معلوم نیست، از مجهول استفاده می‌کنیم "
            "(Grammar in Use — Units 41-42).</p>"
            "<p><b>حال ساده:</b> The food <strong>is cooked</strong> with fresh ingredients.</p>"
            "<p><b>گذشته ساده:</b> This dish <strong>was invented</strong> in Iran.</p>"
            "<p><b>با عامل:</b> The pizza <strong>was made by</strong> the chef.</p>"
        ),
        "examples": [
            {"en": "This bread is baked fresh every morning.", "fa": "این نان هر صبح تازه پخته می‌شود."},
            {"en": "The menu was changed last week.", "fa": "منو هفتهٔ پیش عوض شد."},
            {"en": "Persian food is known all over the world.", "fa": "غذای ایرانی در تمام دنیا شناخته‌شده است."},
            {"en": "The bill was paid by my friend.", "fa": "صورتحساب توسط دوستم پرداخت شد."},
            {"en": "Tea is served after every meal.", "fa": "چای بعد از هر وعده سرو می‌شود."},
        ],
        "common_mistakes": (
            "در مجهول، فعل اصلی به‌صورت قسمت سوم (past participle) می‌آید: «is cooked» نه «is cook». "
            "فراموش نکنید فعل to be را با فاعل هماهنگ کنید: «The dishes are served» نه «is served»."
        ),
        "usage_tips": (
            "در توضیح طرز تهیه غذا و رستوران‌ها خیلی رایج است: «The rice is cooked slowly» — "
            "در متون علمی و خبری هم مجهول پرکاربرد است."
        ),
    },
    "zero_first_conditional": {
        "title": "Zero & First Conditionals",
        "title_fa": "جملات شرطی نوع صفر و اول",
        "level": "B1",
        "structure": "If + present, present (صفر)  |  If + present, will + verb (اول)",
        "explanation": (
            "<p>جملات شرطی برای بیان «اگر… آنگاه…» (Grammar in Use — Units 38-39):</p>"
            "<p><b>نوع صفر (حقایق):</b> <b>If</b> you heat ice, it <strong>melts</strong>.</p>"
            "<p><b>نوع اول (محتمل):</b> <b>If</b> you order now, the food <strong>will arrive</strong> in 30 minutes.</p>"
            "<p>ترتیب جمله مهم نیست: «The food will arrive in 30 minutes if you order now.»</p>"
        ),
        "examples": [
            {"en": "If you add too much salt, the food gets salty.", "fa": "اگر نمک زیاد بزنی، غذا شور می‌شود."},
            {"en": "If the restaurant is full, we will go somewhere else.", "fa": "اگر رستوران پر باشد، جایی دیگر می‌رویم."},
            {"en": "You will love this dish if you like spicy food.", "fa": "اگر غذای تند دوست داری، این غذا را دوست خواهی داشت."},
            {"en": "If it rains, we will eat inside.", "fa": "اگر باران بیاید، داخل غذا می‌خوریم."},
            {"en": "If you don't book a table, you will wait a long time.", "fa": "اگر میز رزرو نکنی، مدت طولانی صبر می‌کنی."},
        ],
        "common_mistakes": (
            "در جملهٔ if از will استفاده نمی‌شود: «If it rains» نه «If it will rain». "
            "will فقط در جملهٔ اصلی می‌آید."
        ),
        "usage_tips": (
            "برای رزرو و برنامه‌ریزی: «If we arrive early, we will get a good table.» — "
            "نوع صفر برای حقایق غذایی: «If you freeze water, it becomes ice.»"
        ),
    },
    # ============================================================
    # WORLD 3 — EVERYDAY LIFE & CITY (A2/B1)
    # ============================================================
    "prepositions_time": {
        "title": "Prepositions of Time — In / On / At",
        "title_fa": "حروف اضافهٔ زمان — In، On، At",
        "level": "A2",
        "structure": "at + ساعت  |  on + روز  |  in + ماه/سال/فصل",
        "explanation": (
            "<p>سه حرف اضافهٔ اصلی زمان (Grammar in Use — Units 107-108):</p>"
            "<p><b>at</b> برای ساعت و لحظه: at 7 o'clock, at noon, at night</p>"
            "<p><b>on</b> برای روزها و تاریخ: on Monday, on 15 May</p>"
            "<p><b>in</b> برای ماه/سال/فصل و بخش‌های روز: in June, in 2026, in summer, in the morning</p>"
            "<p>استثنا: at night (نه in night).</p>"
        ),
        "examples": [
            {"en": "The class starts at 9 o'clock.", "fa": "کلاس ساعت ۹ شروع می‌شود."},
            {"en": "I have English lessons on Mondays and Wednesdays.", "fa": "من دوشنبه‌ها و چهارشنبه‌ها درس انگلیسی دارم."},
            {"en": "The city is beautiful in spring.", "fa": "شهر در بهار زیباست."},
            {"en": "We meet at noon in the park.", "fa": "ظهر در پارک ملاقات می‌کنیم."},
            {"en": "She was born in 2005.", "fa": "او در سال ۲۰۰۵ به دنیا آمده است."},
        ],
        "common_mistakes": (
            "«in Monday» ❌ → «on Monday» ✅ · «at the morning» ❌ → «in the morning» ✅ "
            "برای روزهای هفته همیشه on به کار می‌رود."
        ),
        "usage_tips": (
            "برای برنامهٔ روزانه: «I wake up at 7, exercise in the morning, and meet friends on Fridays.» — "
            "این سه حرف اضافه را با تقویم تمرین کنید."
        ),
    },
    "prepositions_place": {
        "title": "Prepositions of Place — In / On / At / Near",
        "title_fa": "حروف اضافهٔ مکان — In، On، At، Near",
        "level": "A2",
        "structure": "in + داخل  |  on + روی سطح  |  at + نقطه/مکان خاص  |  near + نزدیکی",
        "explanation": (
            "<p>حروف اضافهٔ مکان برای آدرس دادن و موقعیت (Grammar in Use — Units 109-110):</p>"
            "<p><b>in</b> = داخل شهر/کشور/اتاق: in Tehran, in the kitchen</p>"
            "<p><b>on</b> = روی سطح: on the table, on the second floor</p>"
            "<p><b>at</b> = نقطه یا مکان خاص: at the bus stop, at work, at home</p>"
            "<p><b>near</b> = نزدیک: near the bank</p>"
        ),
        "examples": [
            {"en": "The supermarket is near the metro station.", "fa": "سوپرمارکت نزدیک ایستگاه مترو است."},
            {"en": "My office is on the third floor.", "fa": "دفتر من در طبقهٔ سوم است."},
            {"en": "She lives in a small apartment in the city center.", "fa": "او در یک آپارتمان کوچک در مرکز شهر زندگی می‌کند."},
            {"en": "I'll meet you at the entrance.", "fa": "سر در ورودی می‌بینمت."},
            {"en": "The pharmacy is on the corner of the street.", "fa": "داروخانه سر کوچه است."},
        ],
        "common_mistakes": (
            "«in home» ❌ → «at home» ✅ · «on Tehran» ❌ → «in Tehran» ✅ "
            "برای آدرس کامل: at + شماره، on + خیابان، in + شهر."
        ),
        "usage_tips": (
            "برای مسیریابی: «Excuse me, where is the bank? — It's near the park, on the main street.» — "
            "این ساختار را برای گم نشدن در شهر یاد بگیرید."
        ),
    },
    "there_is_are": {
        "title": "There Is / There Are",
        "title_fa": "There Is / There Are — وجود داشتن",
        "level": "A1",
        "structure": "There is + مفرد  |  There are + جمع  |  Is there…? / Are there…?",
        "explanation": (
            "<p>برای گفتن «چیزی وجود دارد» (Grammar in Use — Unit 37):</p>"
            "<p><b>مفرد:</b> <strong>There is</strong> a bank near here.</p>"
            "<p><b>جمع:</b> <strong>There are</strong> two parks in my neighborhood.</p>"
            "<p><b>منفی:</b> <strong>There isn't</strong> a cinema nearby.</p>"
            "<p><b>سوالی:</b> <strong>Is there</strong> a pharmacy around here?</p>"
        ),
        "examples": [
            {"en": "There is a great café across the street.", "fa": "یک کافهٔ عالی آن طرف خیابان است."},
            {"en": "There are many museums in this city.", "fa": "موزه‌های زیادی در این شهر وجود دارد."},
            {"en": "Is there a bus stop near here?", "fa": "ایستگاه اتوبوس نزدیک اینجا هست؟"},
            {"en": "There isn't any parking space downtown.", "fa": "توی مرکز شهر جای پارک نیست."},
            {"en": "There are three hospitals in this area.", "fa": "سه بیمارستان در این منطقه وجود دارد."},
        ],
        "common_mistakes": (
            "با جمع حتماً are بیاورید: «There are two parks» نه «There is two parks». "
            "در سوال ترتیب برعکس می‌شود: «Is there…?» نه «There is…?»"
        ),
        "usage_tips": (
            "برای معرفی محله و شهر: «There is…», «There are…» — این دو الگو پایهٔ توصیف هر مکانی هستند."
        ),
    },
    "adverbs_frequency": {
        "title": "Adverbs of Frequency",
        "title_fa": "قیدهای تکرار",
        "level": "A1",
        "structure": "always / usually / often / sometimes / rarely / never + verb",
        "explanation": (
            "<p>قیدهای تکرار نشان می‌دهند کاری چقدر انجام می‌شود (Grammar in Use — Unit 2):</p>"
            "<p><b>همیشه:</b> always · <b>معمولاً:</b> usually · <b>اغلب:</b> often · "
            "<b>گاهی:</b> sometimes · <b>به‌ندرت:</b> rarely · <b>هرگز:</b> never</p>"
            "<p>این قیدها <b>قبل از فعل اصلی</b> می‌آیند: «I <strong>always</strong> take the bus.»</p>"
            "<p>اما بعد از am/is/are/was/were: «She <strong>is</strong> usually <strong>on time</strong>.»</p>"
        ),
        "examples": [
            {"en": "I always drink coffee in the morning.", "fa": "من همیشه صبح قهوه می‌نوشم."},
            {"en": "She usually walks to work.", "fa": "او معمولاً پیاده تا سر کار می‌رود."},
            {"en": "They often eat out on weekends.", "fa": "آن‌ها آخر هفته‌ها اغلب بیرون غذا می‌خورند."},
            {"en": "I rarely watch TV these days.", "fa": "این روزها به‌ندرت تلویزیون می‌بینم."},
            {"en": "He is never late for class.", "fa": "او هرگز برای کلاس دیر نمی‌کند."},
        ],
        "common_mistakes": (
            "قید تکرار قبل از فعل اصلی است نه قبل از فاعل: «I always go» نه «Always I go». "
            "با افعال to be قید بعد از فعل می‌آید: «She is always happy»."
        ),
        "usage_tips": (
            "برای توصیف سبک زندگی و عادت‌ها: «I always…, I sometimes…» — در معرفی خودتان و دیگران خیلی مفید است."
        ),
    },
    "gerunds_infinitives": {
        "title": "Verbs + -ing / to + verb",
        "title_fa": "فعل + ing یا to + فعل",
        "level": "B1",
        "structure": "enjoy/like/hate + verb-ing  |  want/decide/plan + to + verb",
        "explanation": (
            "<p>بعضی افعال بعد از خود ing می‌گیرند و بعضی to + فعل (Grammar in Use — Units 53-55):</p>"
            "<p><b>+ ing:</b> enjoy, like, love, hate, finish, avoid, consider, keep</p>"
            "<p><b>+ to:</b> want, decide, plan, hope, need, learn, offer, agree</p>"
            "<p><b>هر دو:</b> start, begin, continue, like, love, hate</p>"
            "<p>«I enjoy <strong>cooking</strong>.» · «I decided <strong>to learn</strong> English.»</p>"
        ),
        "examples": [
            {"en": "I enjoy meeting new people.", "fa": "از ملاقات آدم‌های جدید لذت می‌برم."},
            {"en": "She wants to learn Spanish next year.", "fa": "او می‌خواهد سال آینده اسپانیایی یاد بگیرد."},
            {"en": "We finished shopping before noon.", "fa": "قبل از ظهر خریدمان تمام شد."},
            {"en": "He plans to move to a bigger apartment.", "fa": "او قصد دارد به آپارتمان بزرگ‌تری نقل مکان کند."},
            {"en": "They avoid driving in rush hour.", "fa": "آن‌ها از رانندگی در ساعات شلوغ پرهیز می‌کنند."},
        ],
        "common_mistakes": (
            "«I enjoy to swim» ❌ → «I enjoy swimming» ✅ · «I want going» ❌ → «I want to go» ✅ — "
            "لیست افعال را حفظ کنید تا اشتباه نکنید."
        ),
        "usage_tips": (
            "در معرفی علاقه‌مندی‌ها: «I enjoy reading, I like playing football, I want to travel» — "
            "این ساختار برای مصاحبه و دوست‌یابی عالی است."
        ),
    },
    "second_conditional": {
        "title": "Second Conditional — Imaginary Situations",
        "title_fa": "جملات شرطی نوع دوم — موقعیت‌های خیالی",
        "level": "B1",
        "structure": "If + past simple, would + verb",
        "explanation": (
            "<p>برای موقعیت‌های خیالی یا غیرمحتمل (Grammar in Use — Unit 40):</p>"
            "<p><b>If</b> I <strong>had</strong> more time, I <strong>would learn</strong> two languages.</p>"
            "<p>در if از گذشته ساده استفاده می‌شود ولی معنی گذشته نیست — دربارهٔ الان/آیندهٔ خیالی است.</p>"
            "<p>was/were: هر دو درست است، were رسمی‌تر: «If I <strong>were</strong> you, I would…»</p>"
        ),
        "examples": [
            {"en": "If I lived in the city center, I would walk everywhere.", "fa": "اگر مرکز شهر زندگی می‌کردم، همه‌جا پیاده می‌رفتم."},
            {"en": "If I were you, I would take that job.", "fa": "اگر جای تو بودم، آن شغل را می‌گرفتم."},
            {"en": "She would travel more if she had more money.", "fa": "اگر پول بیشتری داشت، بیشتر سفر می‌کرد."},
            {"en": "If we had a car, we could visit you every week.", "fa": "اگر ماشین داشتیم، هر هفته به دیدن تو می‌آمدیم."},
            {"en": "What would you do if you won the lottery?", "fa": "اگر برندهٔ لاتاری می‌شدی چه کار می‌کردی؟"},
        ],
        "common_mistakes": (
            "در if از would استفاده نمی‌شود: «If I had» نه «If I would have». "
            "گذشته ساده در if معنی گذشته نمی‌دهد — فقط برای خیال است."
        ),
        "usage_tips": (
            "برای نصیحت: «If I were you, I would…» — و برای رویاها: «If I had a chance, I would…» — "
            "این ساختار در مکالمهٔ روزمره بسیار محبوب است."
        ),
    },
    "relative_clauses": {
        "title": "Relative Clauses — Who / Which / That / Where",
        "title_fa": "جمله‌های وابسته — Who، Which، That، Where",
        "level": "B1",
        "structure": "who/that + شخص  |  which/that + شیء  |  where + مکان",
        "explanation": (
            "<p>برای توضیح بیشتر دربارهٔ یک اسم (Grammar in Use — Units 93-94):</p>"
            "<p><b>شخص:</b> The woman <strong>who</strong> lives next door is a doctor.</p>"
            "<p><b>شیء:</b> The café <strong>which</strong> we visited was amazing.</p>"
            "<p><b>مکان:</b> This is the street <strong>where</strong> I grew up.</p>"
            "<p>that می‌تواند به‌جای who/which بیاید (غیررسمی‌تر).</p>"
        ),
        "examples": [
            {"en": "The man who is standing at the door is my uncle.", "fa": "مردی که دم در ایستاده عموی من است."},
            {"en": "This is the restaurant where we had dinner last week.", "fa": "این رستورانی است که هفتهٔ پیش آنجا شام خوردیم."},
            {"en": "I have a friend who speaks five languages.", "fa": "دوستی دارم که پنج زبان صحبت می‌کند."},
            {"en": "The book that you recommended was great.", "fa": "کتابی که پیشنهاد دادی عالی بود."},
            {"en": "That's the house where my grandmother lived.", "fa": "آن خانه‌ای است که مادربزرگم آنجا زندگی می‌کرد."},
        ],
        "common_mistakes": (
            "برای مکان از where استفاده کنید نه which: «the city where I live» نه «the city which I live». "
            "بعد از who فعل با فاعل هماهنگ می‌شود: «the man who lives» نه «who live»."
        ),
        "usage_tips": (
            "برای توصیف آدم‌ها و جاها: «a person who…», «a place where…» — در تعریف کردن و توضیح دادن خیلی کاربردی است."
        ),
    },
    "reported_speech": {
        "title": "Reported Speech — Say & Tell",
        "title_fa": "گفتار نقل‌قولی — Say و Tell",
        "level": "B1",
        "structure": "He said (that) + جمله  |  He told me (that) + جمله",
        "explanation": (
            "<p>برای نقل قول غیرمستقیم (Grammar in Use — Units 47-48):</p>"
            "<p><b>با said:</b> He <strong>said</strong> (that) he was tired.</p>"
            "<p><b>با told:</b> She <strong>told me</strong> (that) she would come.</p>"
            "<p>زمان‌ها یک قدم به عقب می‌روند: am→was, will→would, can→could, is going to→was going to</p>"
            "<p>نکته: بعد از tell حتماً مفعول می‌آید (told me) ولی بعد از say نمی‌آید (said that).</p>"
        ),
        "examples": [
            {"en": "He said that he was busy.", "fa": "او گفت که سرش شلوغ است (بود)."},
            {"en": "She told me she would call later.", "fa": "او به من گفت بعداً زنگ می‌زند."},
            {"en": "They said they had already eaten.", "fa": "آن‌ها گفتند قبلاً غذا خورده‌اند."},
            {"en": "My friend told me that the movie was boring.", "fa": "دوستم گفت فیلم کسل‌کننده بود."},
            {"en": "The teacher said we should practice every day.", "fa": "معلم گفت که باید هر روز تمرین کنیم."},
        ],
        "common_mistakes": (
            "«He said me» ❌ → «He said to me» یا «He told me» ✅ "
            "بعد از said که می‌آید یا nothing: «She said (that)…»."
        ),
        "usage_tips": (
            "در بازگو کردن مکالمه‌ها: «She told me…», «He said that…» — "
            "با تمرین روی زمان‌ها (امروز→دیروز) نقل قول طبیعی می‌شود."
        ),
    },
    "question_tags": {
        "title": "Question Tags",
        "title_fa": "برچسب سوالی (مگه نه؟)",
        "level": "B1",
        "structure": "جملهٔ مثبت + فعل کمکی منفی + فاعل؟  |  جملهٔ منفی + فعل کمکی مثبت + فاعل؟",
        "explanation": (
            "<p>برای تأیید گرفتن یا تعجب (Grammar in Use — Unit 50):</p>"
            "<p><b>مثبت → منفی:</b> It's a nice day, <strong>isn't it?</strong></p>"
            "<p><b>منفی → مثبت:</b> You don't like coffee, <strong>do you?</strong></p>"
            "<p>فعل کمکی با زمان جمله هماهنگ می‌شود: is/are/was/were, do/does/did, have/has, will, can…</p>"
        ),
        "examples": [
            {"en": "The weather is great today, isn't it?", "fa": "هوا امروز عالیه، مگه نه؟"},
            {"en": "You've been to this city before, haven't you?", "fa": "قبلاً به این شهر اومدی، مگه نه؟"},
            {"en": "She doesn't live here, does she?", "fa": "او اینجا زندگی نمی‌کنه، مگه نه؟"},
            {"en": "We can meet tomorrow, can't we?", "fa": "می‌تونیم فردا ببینمت، مگه نه؟"},
            {"en": "They will come to the party, won't they?", "fa": "آن‌ها به مهمونی میان، مگه نه؟"},
        ],
        "common_mistakes": (
            "جملهٔ مثبت با تگ منفی همراه می‌شود و برعکس. "
            "با I am تگ aren't I می‌شود: «I'm right, aren't I?»"
        ),
        "usage_tips": (
            "در مکالمهٔ روزمره برای تأیید: «It's nice, isn't it?» — با آهنگ صدای بالا، سوال واقعی می‌شود."
        ),
    },
}
