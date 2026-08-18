import random

from django.utils import timezone

from .ai_openrouter import available, chat, chat_json
from .models import (AIChallenge, AIChatMessage, Idiom, UserIdiomProgress,
                     UserLanguageEstimate, UserVocabularyProgress, Vocabulary)
from .placement_bank import LEVELS_ORDER, PLACEMENT_BANK

PLACEMENT_Q_COUNT = 8

_LANG = ("You are 'Questie', the friendly English-learning coach inside the LearnQuest app. "
         "The learner is a Persian speaker. Reply in warm, casual Persian (Farsi), keep English words in English. "
         "Be brief (2-4 sentences), encouraging, and practical. Never use markdown tables or headings.")


def _cefr_index(level):
    try:
        return LEVELS_ORDER.index(level)
    except ValueError:
        return 0


def build_placement_quiz(level):
    ai_ok = available()
    if ai_ok:
        sys = ("You write placement quizzes for English learners. Output ONLY a JSON array, no prose, "
               "exactly %d objects with keys: q (string), choices (array of exactly 4 strings), answer (int 0-3), "
               "why (one short sentence explaining the correct answer).") % PLACEMENT_Q_COUNT
        usr = ("Create %d multiple-choice questions to verify a learner really is at CEFR level %s "
               "(grammar and vocabulary). Questions must be calibrated to %s: a true %s student answers most "
               "correctly, a lower-level one fails at least half. Output the JSON array only.") % (
               PLACEMENT_Q_COUNT, level, level, level)
        data = chat_json([{'role': 'system', 'content': sys}, {'role': 'user', 'content': usr}], expected=list)
        if isinstance(data, list):
            cleaned = []
            for item in data[:PLACEMENT_Q_COUNT]:
                if not isinstance(item, dict):
                    continue
                q = str(item.get('q') or '').strip()
                choices = item.get('choices')
                ans = item.get('answer')
                why = str(item.get('why') or '')[:300]
                if not q or not isinstance(choices, list) or len(choices) != 4:
                    continue
                if not all(isinstance(cv, str) and cv.strip() for cv in choices):
                    continue
                if not isinstance(ans, int) or not 0 <= ans <= 3:
                    continue
                cleaned.append({'q': q[:400], 'choices': [cv[:200] for cv in choices], 'answer': ans, 'why': why})
            if len(cleaned) >= PLACEMENT_Q_COUNT - 2:
                return cleaned[:PLACEMENT_Q_COUNT], True
    bank = list(PLACEMENT_BANK.get(level) or PLACEMENT_BANK['B1'])
    random.shuffle(bank)
    quiz = [{'q': q['q'], 'choices': list(q['choices']), 'answer': q['answer'], 'why': q['why']} for q in bank[:PLACEMENT_Q_COUNT]]
    for item in quiz:
        ch = item['choices']
        correct = ch[item['answer']]
        random.shuffle(ch)
        item['answer'] = ch.index(correct)
    return quiz, ai_ok


def tutor_reply(user, message, history):
    sys = _LANG + _tutor_context(user)
    messages = [{'role': 'system', 'content': sys}]
    for h in history[-10:]:
        messages.append({'role': h['role'], 'content': h['content'][:800]})
    messages.append({'role': 'user', 'content': message[:800]})
    reply = chat(messages, temperature=0.5, max_tokens=500)
    if reply:
        return reply.strip()[:1500], True
    return _fallback_reply(user, message), False


def _tutor_context(user):
    est = UserLanguageEstimate.objects.filter(user=user).first()
    level = est.cefr_level if est else 'A1'
    learned = UserVocabularyProgress.objects.filter(user=user, mastery_level__gte=2).count()
    ilearned = UserIdiomProgress.objects.filter(user=user, mastery_level__gte=2).count()
    recent = (UserVocabularyProgress.objects.filter(user=user, mastery_level__gte=1)
              .select_related('vocabulary').order_by('-updated_at')[:8])
    words = ', '.join(p.vocabulary.word for p in recent if p.vocabulary_id)
    rid = (UserIdiomProgress.objects.filter(user=user).select_related('idiom').order_by('-updated_at')[:4])
    idioms = ', '.join(p.idiom.expression for p in rid if p.idiom_id)
    return (f"\nLearner facts: CEFR level ~{level}, words learned: {learned}, idioms learned: {ilearned}. "
            f"Recently practiced words: {words or 'none yet'}. Idioms in progress: {idioms or 'none yet'}. "
            "Use these facts to give personal suggestions, and occasionally quiz the learner on one of these items.")


def _fallback_reply(user, message):
    est = UserLanguageEstimate.objects.filter(user=user).first()
    level = est.cefr_level if est else 'A1'
    learned = UserVocabularyProgress.objects.filter(user=user, mastery_level__gte=2).count()
    m = (message or '').lower()
    tips = [
        f'سطح فعلیت {level} رو داریم؛ امروز ۵ تا فلش‌کارت مرور کن — تداوم از همه‌چیز مهم‌تره 💪',
        f'تا الان {learned} لغت رو ثبت کردی! یه چالش تصادفی رو هم بزن تا مغزت حواسش جمع بمونه 😉',
        'یه اصطلاح جدید امروز یاد بگیر و توی جملهٔ خودت به‌کارش ببر — مثلاً «piece of cake» 🍰',
        'اگه لغتی سخت بود، چند روز پشت‌سرمرورش کن؛ تکرار فاصله‌دار راز موندگاریه 🔁',
    ]
    if 'سلام' in m or 'hello' in m or 'hi' in m:
        return ('سلام! من کوئستی‌ام، مربی انگلیسیت 🎓 بگو چی یاد گرفتی، از روکم سوال بپرس '
                'یا بگو یه کوییز سریع برات بگیرم!')
    if 'سوال' in m or 'quiz' in m or 'چالش' in m or 'تست' in m:
        return 'عالیه! پایین صفحه یه «چالش هوشمند» باز می‌شه — بزنش شروع کنیم ⚡'
    return random.choice(tips)


def build_challenge(user, source='mixed'):
    pending = AIChallenge.objects.filter(user=user, is_correct__isnull=True).order_by('-created_at').first()
    if pending:
        return pending, False

    if source == 'mixed':
        source = random.choice(['vocab', 'idiom'])
    payload = None
    if source == 'idiom':
        est = UserLanguageEstimate.objects.filter(user=user).first()
        level = est.cefr_level if est else 'A1'
        iid = Idiom.objects.filter(is_active=True, level=level).order_by('?').first() or Idiom.objects.filter(is_active=True).order_by('?').first()
        if iid:
            others = list(Idiom.objects.exclude(id=iid.id).filter(is_active=True).order_by('?')[:3])
            if len(others) == 3:
                payload = {
                    'kind': 'idiom_meaning',
                    'question': f'What does “{iid.expression}” mean?',
                    'choices': [iid.definition_en] + [o.definition_en for o in others],
                    'answer': 0,
                    'why': f'“{iid.expression}” یعنی {iid.translation_fa} — مثال: {iid.example_en}',
                    'ref': iid.id,
                }
    if payload is None:
        source = 'vocab'
        cand = (UserVocabularyProgress.objects.filter(user=user, mastery_level__gte=1)
                .select_related('vocabulary').order_by('?')[:6])
        word = next((p.vocabulary for p in cand if p.vocabulary_id), None)
        if not word:
            word = Vocabulary.objects.filter(is_active=True).order_by('?').first()
        if word:
            others = list(Vocabulary.objects.exclude(id=word.id).filter(is_active=True).order_by('?')[:3])
            if len(others) == 3:
                payload = {
                    'kind': 'word_meaning',
                    'question': f'What is the meaning of “{word.word}”?',
                    'choices': [word.meaning[:160]] + [o.meaning[:160] for o in others],
                    'answer': 0,
                    'why': f'“{word.word}” یعنی {word.meaning_fa or word.meaning}',
                    'ref': word.id,
                }
    if payload is None:
        pool = PLACEMENT_BANK['B1'] + PLACEMENT_BANK['B2']
        q = random.choice(pool)
        payload = {'kind': 'grammar', 'question': q['q'], 'choices': list(q['choices']), 'answer': q['answer'], 'why': q['why'], 'ref': None}
        source = 'vocab'

    ch = payload['choices']
    correct = ch[payload['answer']]
    random.shuffle(ch)
    payload['answer'] = ch.index(correct)
    payload['source_label'] = source
    obj = AIChallenge.objects.create(user=user, source=source, payload=payload, used_ai=False)
    return obj, True


CHALLENGE_XP = 15
CHALLENGE_COINS = 5


def grade_challenge(user, challenge_id, index):
    from django.db import transaction
    with transaction.atomic():
        ch = (AIChallenge.objects.select_for_update()
              .filter(id=challenge_id, user=user, is_correct__isnull=True).first())
        if not ch:
            return None
        correct = ch.payload.get('answer') == index
        ch.answer_index = index
        ch.is_correct = correct
        ch.answered_at = timezone.now()
        xp = 0
        if correct and not ch.xp_awarded:
            from economy.services import grant_coins, grant_xp
            r_xp = grant_xp(user, CHALLENGE_XP, source='ai_challenge', source_id=ch.id,
                            idempotency_key=f'aich:{ch.id}:xp')
            xp = r_xp.get('granted', 0)
            if xp:
                grant_coins(user, CHALLENGE_COINS, source='ai_challenge', source_id=ch.id,
                            idempotency_key=f'aich:{ch.id}:coins')
            ch.xp_awarded = True
        ch.save()
    return {'correct': correct, 'why': ch.payload.get('why', ''), 'xp': xp,
            'correct_index': ch.payload.get('answer'),
            'question': ch.payload.get('question', ''), 'source': ch.source}
