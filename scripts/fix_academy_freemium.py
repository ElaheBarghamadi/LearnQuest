import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Config.settings')

import django
django.setup()

from language_academy.models import Lesson, LessonContent, Chapter
from shop.models import Product

first = Lesson.objects.get(pk=1)
if first.is_exclusive:
    first.is_exclusive = False
    first.save(update_fields=['is_exclusive'])
    print('Lesson #1 -> free')

CAFE = dict(
    chapter_id=4, order=91, name='Cafe Conversation', name_fa='مکالمهٔ کافه',
    lesson_type='dialogue', xp_reward=120, coin_reward=40, estimated_time_minutes=20,
    intro='<p>Welcome to the English Cafe! ☕ In this exclusive lesson you will learn to order confidently, chat with the barista, and pay the bill — through real-life dialogues.</p>',
    objectives=['Order drinks and food in English', 'Understand menus and prices', 'Politely ask to change an order', 'Pay and ask for the check'],
    sentences=[
        {'en': "Hi! A table for one, please.", 'fa': 'سلام! یه میز برای یک نفر لطفاً.'},
        {'en': "Could I get a caramel latte, medium?", 'fa': 'یه لاتهٔ کاراملی سایز متوسط می‌شه؟'},
        {'en': "Is it possible to make it with oat milk?", 'fa': 'می‌شه با شیر جو درستش کنید؟'},
        {'en': "Can I have the check, please?", 'fa': 'ممکنه صورتحساب رو بیارید؟'},
        {'en': "Keep the change!", 'fa': 'بقیه‌ش رو نگه دارید!'},
    ],
    summary='<p>Great job! You can now order, ask questions, and pay in English at any cafe. Practice these dialogues out loud!</p>',
    takeaways=['"Could I get...?" is the most useful ordering formula', '"Can I have...?" is correct and polite too', '"Keep the change" means the extra money is a tip'],
    reading='Living in a city means coffee shops everywhere. Maria walks into a small cafe. "Good morning! A cappuccino and a croissant, please." The barista smiles: "For here or to go?" Maria answers: "For here, thanks."',
    reading_fa='زندگی در شهر یعنی کافه‌ها همه‌جا هستند. ماریا وارد یک کافهٔ کوچک می‌شود. «صبح بخیر! یه کاپوچینو و یه کرواسان لطفاً.» باریستا لبخند می‌زند: «اینجا میل می‌کنید یا ببرید؟» ماریا جواب می‌دهد: «اینجا، ممنون.»',
    product_slug='exclusive-lesson-cafe',
)

BIZ = dict(
    chapter_id=3, order=92, name='Business Travel Pro', name_fa='سفر کاری و فرودگاه بین‌المللی',
    lesson_type='mixed', xp_reward=120, coin_reward=40, estimated_time_minutes=25,
    intro='<p>The exclusive lesson for business travelers! 🧳 From check-in to the transit lounge and talking to the customs officer — the English you really need at the airport.</p>',
    objectives=['Talk professionally with airport staff', 'Understand flight and gate announcements', 'Answer customs questions', 'Handle delays and flight changes'],
    sentences=[
        {'en': "I'm traveling for business.", 'fa': 'برای کار سفر می‌کنم.'},
        {'en': "What's the gate number for flight TK102?", 'fa': 'گیت پرواز TK102 چنده؟'},
        {'en': "Is my flight on time?", 'fa': 'پروازم سر وقت‌ه؟'},
        {'en': "I'd like a lounge pass, please.", 'fa': 'یه بلیط سالن انتظار (لانژ) می‌خوام.'},
        {'en': "Nothing to declare.", 'fa': 'چیزی برای اظهار ندارم. (گمرک)'},
    ],
    summary='<p>Excellent! You can now handle any international airport with confidence. Note the key phrases and review them before your trip.</p>',
    takeaways=['gate = the exit door to your plane', 'on time = not late', '"Nothing to declare" = you have no taxable goods'],
    reading='David checks his phone: flight delayed by two hours. No problem. He walks to the lounge, shows his boarding pass, and opens his laptop. A business trip always has surprises.',
    reading_fa='دیوید گوشی‌اش را چک می‌کند: پرواز دو ساعت تأخیر دارد. مشکلی نیست. به سمت لانژ می‌رود، کارت پروازش را نشان می‌دهد و لپ‌تاپش را باز می‌کند. سفر کاری همیشه غافلگیری دارد.',
    product_slug='exclusive-lesson-business-travel',
)


def make_lesson(spec):
    lesson, created = Lesson.objects.update_or_create(
        name=spec['name'],
        defaults=dict(
            chapter_id=spec['chapter_id'], order=spec['order'],
            name_fa=spec['name_fa'], lesson_type=spec['lesson_type'],
            xp_reward=spec['xp_reward'], coin_reward=spec['coin_reward'],
            estimated_time_minutes=spec['estimated_time_minutes'],
            is_published=True, is_exclusive=True,
        )
    )
    LessonContent.objects.update_or_create(
        lesson=lesson,
        defaults=dict(
            introduction=spec['intro'], summary=spec['summary'],
            learning_objectives=spec['objectives'],
            example_sentences=spec['sentences'],
            key_takeaways=spec['takeaways'],
            grammar_notes='', grammar_examples=[],
            reading_text=spec['reading'], reading_translation=spec['reading_fa'],
        )
    )
    print(('created' if created else 'updated'), 'lesson ->', lesson.id, lesson.name)
    return lesson


cafe = make_lesson(CAFE)
biz = make_lesson(BIZ)

prod = Product.objects.get(slug='exclusive-lesson-cafe')
if prod.effect_payload.get('lesson_id') != cafe.id:
    prod.effect_payload = {'lesson_id': cafe.id}
    prod.save(update_fields=['effect_payload'])
    print('cafe product repointed ->', cafe.id)

biz_prod, created = Product.objects.update_or_create(
    slug='exclusive-lesson-business-travel',
    defaults=dict(
        category=prod.category, name='بلیط درس ویژه: سفر کاری ✈️',
        description='دسترسی دائمی به درس ویژهٔ «سفر کاری و فرودگاه بین‌المللی» در آکادمی.',
        product_type=prod.product_type, effect_type='exclusive_lesson',
        effect_payload={'lesson_id': biz.id},
        price_coins=450, is_active=True,
    )
)
print(('created' if created else 'updated'), 'product ->', biz_prod.slug, '| payload', biz_prod.effect_payload)

ticketed = {cafe.id, biz.id}
healed = Lesson.objects.filter(is_exclusive=True).exclude(pk__in=ticketed).update(is_exclusive=False)
if healed:
    print(f'healed {healed} wrongly-flagged lesson(s)')

disabled = Product.objects.filter(effect_type='exclusive_chapter', is_active=True).update(is_active=False)
if disabled:
    print(f'disabled {disabled} chapter-unlock ticket(s)')
print('DONE')
