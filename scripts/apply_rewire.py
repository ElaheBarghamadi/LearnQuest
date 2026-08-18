import sys

FAILED = []


def patch(path, old, new, count=1, label=''):
    with open(path, 'r', encoding='utf-8') as f:
        src = f.read()
    found = src.count(old)
    if found != count:
        FAILED.append(f'{label or path}: expected {count}, found {found} >> {old[:70]!r}')
        return
    src = src.replace(old, new)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(src)
    print(f'  ✔ {label or path}: +{count}')


G = 'Game/views.py'

patch(G, 'from django.views.decorators.csrf import csrf_exempt\n', '', 1, 'G: drop csrf import')

patch(G, 'from user.models import UserActivity  # فقط این خط اضافه شد\n', '''from user.models import UserActivity  # فقط این خط اضافه شد
from economy.services import grant_xp as _eco_grant_xp


def _grant_game_xp(user, xp_gained, game_name, source_id=None):
    """
    واریز امن XP بازی — فقط از «دروازهٔ اقتصاد»:
    - سقف روزانهٔ قانون game_play (ضد فارم)
    - اعمال خودکار بوستر فعال
    - بدون race (قفل سطر + F()) و ثبت در دفتر تراکنش
    خروجی: (مقدار واقعی واریزشده، به سقف روزانه خورد؟)
    """
    if xp_gained <= 0:
        return 0, False
    r = _eco_grant_xp(user, xp_gained, source=f'game:{game_name}', source_id=source_id,
                      rule_code='game_play')
    return r.get('granted', 0), bool(r.get('capped'))


def _level_up_activity(user, old_level):
    """ثبت فعالیت لِوِل‌آپ (user باید قبلاً refresh شده باشد)."""
    if old_level != user.level:
        UserActivity.objects.create(
            user=user,
            title=f'رسیدن به سطح {user.level}',
            description=f'شما به سطح {user.level} در بازی رسیدید',
            icon='level-up'
        )
''', 1, 'G: helpers')


for fn in ('save_memory_score', 'save_puzzle_score', 'save_sudoku_score', 'save_iq_score'):
    patch(G, f'@csrf_exempt\n@require_http_methods(["POST"])\ndef {fn}',
          f'@login_required\n@require_http_methods(["POST"])\ndef {fn}',
          1, f'G: secure decorator {fn}')


patch(G, '@login_required\n@csrf_exempt\n@require_http_methods(["POST"])',
      '@login_required\n@require_http_methods(["POST"])', 6, 'G: drop csrf_exempt x6')


patch(G, '''        moves = data.get('moves', 0)
        time_seconds = data.get('time', 0)
        completed = data.get('completed', True)
''', '''        moves = max(0, int(data.get('moves', 0) or 0))
        time_seconds = max(0, int(data.get('time', 0) or 0))
        completed = bool(data.get('completed', True))
''', 2, 'G: clamp memory+puzzle')

patch(G, '''        time_seconds = data.get('time', 0)
        hints_used = data.get('hints_used', 0)
        completed = data.get('completed', True)
''', '''        time_seconds = max(0, int(data.get('time', 0) or 0))
        hints_used = max(0, int(data.get('hints_used', 0) or 0))
        completed = bool(data.get('completed', True))
''', 1, 'G: clamp sudoku')

patch(G, '''        score = data.get('score', 0)
        total = data.get('total', 10)
        completed = data.get('completed', True)
''', '''        score = max(0, int(data.get('score', 0) or 0))
        total = max(1, int(data.get('total', 10) or 10))
        completed = bool(data.get('completed', True))
''', 1, 'G: clamp iq')


patch(G, '''        user.xp += xp_gained

        # ========== سطح‌بندی جدید با استفاده از متد مدل ==========
        old_level = user.level
        if user.update_level():
            if old_level != user.level:
                UserActivity.objects.create(
                    user=user,
                    title=f'رسیدن به سطح {user.level}',
                    description=f'شما به سطح {user.level} در بازی رسیدید',
                    icon='level-up'
                )
        # ====================================================

        user.save()

        return JsonResponse({
            'success': True,
            'xp_gained': xp_gained,
            'total_xp': user.xp,
            'new_level': user.level,
''', '''        old_level = user.level
        xp_gained, xp_capped = _grant_game_xp(user, xp_gained, GAME_TAG)
        user.refresh_from_db(fields=['xp', 'level'])
        _level_up_activity(user, old_level)

        return JsonResponse({
            'success': True,
            'xp_gained': xp_gained,
            'xp_capped': xp_capped,
            'total_xp': user.xp,
            'new_level': user.level,
''', 4, 'G: legacy xp block x4 (memory/puzzle/sudoku/iq)')


patch(G, "        xp_gained = 30\n        if moves < 20:\n", "        GAME_TAG = 'memory'\n        xp_gained = 30\n        if moves < 20:\n", 1, 'G: tag memory')
patch(G, "        xp_gained = 40\n        if moves < 100:\n", "        GAME_TAG = 'puzzle'\n        xp_gained = 40\n        if moves < 100:\n", 1, 'G: tag puzzle')
patch(G, "        xp_gained = 35\n        if time_seconds < 300:\n", "        GAME_TAG = 'sudoku'\n        xp_gained = 35\n        if time_seconds < 300:\n", 1, 'G: tag sudoku')
patch(G, "        xp_gained = 30\n\n        if correct_percent >= 80:\n", "        GAME_TAG = 'iq_test'\n        xp_gained = 30\n\n        if correct_percent >= 80:\n", 1, 'G: tag iq')


patch(G, '''        xp_gained = min(xp_base + max(0, score // 50 if not lower_is_better else 10),
                        xp_base + max_xp_bonus)
        user.xp += xp_gained

        old_level = user.level
        if user.update_level() and old_level != user.level:
            UserActivity.objects.create(
                user=user,
                title=f'رسیدن به سطح {user.level}',
                description=f'شما به سطح {user.level} در بازی رسیدید',
                icon='level-up'
            )
        user.save()
    else:
        xp_gained = 0
        new_best = False
''', '''        xp_gained = min(xp_base + max(0, score // 50 if not lower_is_better else 10),
                        xp_base + max_xp_bonus)

        old_level = user.level
        xp_gained, xp_capped = _grant_game_xp(user, xp_gained, game_name)
        user.refresh_from_db(fields=['xp', 'level'])
        _level_up_activity(user, old_level)
    else:
        xp_gained = 0
        xp_capped = False
        new_best = False
''', 1, 'G: _record_score xp block')

patch(G, "        'xp_gained': xp_gained,\n        'total_xp': user.xp,\n        'level': user.level,\n",
      "        'xp_gained': xp_gained,\n        'xp_capped': xp_capped,\n        'total_xp': user.xp,\n        'level': user.level,\n", 1, 'G: _record_score json')


patch(G, '''    stats, _ = UserGameStats.objects.get_or_create(user=user, game_name=game_name)
    stats.games_played += 1
''', '''    score = max(0, int(score or 0))
    stats, _ = UserGameStats.objects.get_or_create(user=user, game_name=game_name)
    stats.games_played += 1
''', 1, 'G: clamp _record_score')


L = 'language/views.py'

patch(L, 'from django.views.decorators.csrf import csrf_exempt\n', '', 1, 'L: drop import')
patch(L, '@csrf_exempt\n', '', 6, 'L: drop decorators x6')

patch(L, 'from Game.models import UserAchievement, UserGameStats  # اضافه شد\n', '''from Game.models import UserAchievement, UserGameStats  # اضافه شد
from Game.views import _grant_game_xp, _level_up_activity
''', 1, 'L: import game helpers')


patch(L, '''        matched_count = data.get('matched_count', 0)
        total_words = data.get('total_words', 5)
        mistakes = data.get('mistakes', 0)

        user = request.user

        base_xp = matched_count * 10
        bonus_xp = 20 if matched_count == total_words else 0
        mistake_penalty = mistakes * 2

        xp_gained = base_xp + bonus_xp - mistake_penalty
        if xp_gained < 0:
            xp_gained = 0

        user.xp = (user.xp or 0) + xp_gained
''', '''        matched_count = max(0, int(data.get('matched_count', 0) or 0))
        total_words = max(1, int(data.get('total_words', 5) or 5))
        mistakes = max(0, int(data.get('mistakes', 0) or 0))

        user = request.user

        base_xp = matched_count * 10
        bonus_xp = 20 if matched_count == total_words else 0
        mistake_penalty = mistakes * 2

        xp_gained = base_xp + bonus_xp - mistake_penalty
        if xp_gained < 0:
            xp_gained = 0

        old_level = user.level
        xp_gained, xp_capped = _grant_game_xp(user, xp_gained, 'connect')
''', 1, 'L: connect xp')


patch(L, '''        score = data.get('score', 0)
        total_questions = data.get('total_questions', 10)
        hints_used = data.get('hints_used', 0)
        time_seconds = data.get('time_seconds', 0)
''', '''        score = max(0, int(data.get('score', 0) or 0))
        total_questions = max(1, int(data.get('total_questions', 10) or 10))
        hints_used = max(0, int(data.get('hints_used', 0) or 0))
        time_seconds = max(0, int(data.get('time_seconds', 0) or 0))
''', 1, 'L: clamp guessing')

patch(L, '''        xp_gained = base_xp + bonus_xp + speed_bonus - hint_penalty
        if xp_gained < 0:
            xp_gained = 0

        user.xp = (user.xp or 0) + xp_gained
''', '''        xp_gained = base_xp + bonus_xp + speed_bonus - hint_penalty
        if xp_gained < 0:
            xp_gained = 0

        old_level = user.level
        xp_gained, xp_capped = _grant_game_xp(user, xp_gained, 'guessing')
''', 1, 'L: guessing xp')


patch(L, '''        score = data.get('score', 0)
        total_questions = data.get('total_questions', 8)
        time_seconds = data.get('time_seconds', 0)
        level = data.get('level', 'medium')
''', '''        score = max(0, int(data.get('score', 0) or 0))
        total_questions = max(1, int(data.get('total_questions', 8) or 8))
        time_seconds = max(0, int(data.get('time_seconds', 0) or 0))
        level = data.get('level', 'medium')
''', 1, 'L: clamp scramble')

patch(L, '''        xp_gained = base_xp + bonus_xp + speed_bonus
        if xp_gained < 0:
            xp_gained = 0

        user.xp = (user.xp or 0) + xp_gained
''', '''        xp_gained = base_xp + bonus_xp + speed_bonus
        if xp_gained < 0:
            xp_gained = 0

        old_level = user.level
        xp_gained, xp_capped = _grant_game_xp(user, xp_gained, 'scramble')
''', 1, 'L: scramble xp')


patch(L, '''        # ========== سطح‌بندی جدید با استفاده از متد مدل ==========
        old_level = user.level
        if user.update_level():
            if old_level != user.level:
                UserActivity.objects.create(
                    user=user,
                    title=f'رسیدن به سطح {user.level}',
                    description=f'شما به سطح {user.level} در بازی رسیدید',
                    icon='level-up'
                )
        # ====================================================
''', '''        user.refresh_from_db(fields=['xp', 'level'])
        _level_up_activity(user, old_level)
''', 3, 'L: legacy level block x3')


patch('user/models.py', '''    def add_xp(self, amount, source='', source_id=None):
        """
        اضافه کردن XP به کاربر

        Args:
            amount (int): مقدار XP
            source (str): منبع (مثلاً 'quiz_completion', 'lesson_completion')
            source_id (int): ID منبع (اختیاری)
        """
        self.xp += amount
        self.save()

        # سطح‌بندی بر اساس XP
        self.update_level()

        return self.xp
''', '''    def add_xp(self, amount, source='', source_id=None):
        """
        [سازگاری قدیمی] واریز XP — حالا فقط از «دروازهٔ اقتصاد»:
        ledger + قفل سطر + بوستر فعال + ثبت تراکنش.
        """
        from economy.services import grant_xp
        result = grant_xp(self, amount, source=source or 'legacy', source_id=source_id)
        try:
            self.refresh_from_db(fields=['xp', 'level'])
        except Exception:
            pass
        return self.xp
''', 1, 'U: add_xp -> economy')


patch('Home/views.py', '''    try:
        xp_in_current_level = user.xp - ((user.level - 1) * 100)
        if xp_in_current_level < 0:
            xp_in_current_level = 0
        progress_percentage = (xp_in_current_level / 100) * 100
        if progress_percentage > 100:
            progress_percentage = 100
    except:
        progress_percentage = 0
''', '''    try:
        progress_percentage = user.get_level_progress()
    except Exception:
        progress_percentage = 0
''', 1, 'H: profile level progress fix')


patch('language_academy/models.py', '''    is_published = models.BooleanField(default=False, verbose_name='منتشر شده')
    is_free_preview = models.BooleanField(default=False, verbose_name='پیش‌نمایش رایگان')
    created_at = models.DateTimeField(auto_now_add=True)
''', '''    is_published = models.BooleanField(default=False, verbose_name='منتشر شده')
    is_free_preview = models.BooleanField(default=False, verbose_name='پیش‌نمایش رایگان')
    is_exclusive = models.BooleanField(default=False, verbose_name='درس ویژه (نیازمند خرید بلیط از فروشگاه)')
    created_at = models.DateTimeField(auto_now_add=True)
''', 1, 'LA-M: Lesson.is_exclusive')


V = 'language_academy/views.py'

patch(V, '''    DailyGoal, CoinTransaction, WritingSubmission, SpeakingSubmission, QuizSession
)


def _grant_pass_rewards_once(user, rewardable, kind):
    """
    پاداش قبولی فقط یک‌بار روی «اولین پاس» — ضد فارم:
    - RewardGrant یکتا روی (user, rule_code, period_key=kind:id)
    - سکه با idempotency_key یکتا
    - بوستر فعال به‌صورت خودکار ضرب می‌شود
    خروجی: (xp_granted, coins_granted, first_time)
    """
    from economy.services import grant_xp, grant_coins
    period_key = f'{kind}:{rewardable.id}'
    r_xp = grant_xp(user, rewardable.xp_reward, source=f'{kind}_pass', source_id=rewardable.id,
                    rule_code=f'{kind}_pass', period_key=period_key)
    if r_xp.get('already'):
        return 0, 0, False
    coins = 0
    if rewardable.coin_reward:
        r_c = grant_coins(user, rewardable.coin_reward, source=f'{kind}_pass', source_id=rewardable.id,
                          idempotency_key=f'{kind}coin:{user.pk}:{rewardable.id}')
        coins = r_c.get('granted', 0)
    return r_xp.get('granted', 0), coins, True


# ============================================================
# WORLD MAP & NAVIGATION
# ============================================================
''', 1, 'V: pass-reward helper')


patch(V, '''    if not lesson.chapter.is_unlocked_for_user(request.user):
        messages.warning(request, 'ابتدا باید فصل قبلی را کامل کنید!')
        return redirect('language_academy:chapter_detail', chapter_id=lesson.chapter.id)
''', '''    if not lesson.chapter.is_unlocked_for_user(request.user):
        messages.warning(request, 'ابتدا باید فصل قبلی را کامل کنید!')
        return redirect('language_academy:chapter_detail', chapter_id=lesson.chapter.id)

    # 🔒 درس ویژه: فقط با بلیط خریداری‌شده از فروشگاه
    if getattr(lesson, 'is_exclusive', False):
        from shop.services import has_unlock
        if not has_unlock(request.user, 'exclusive_lesson', lesson_id=lesson.id):
            messages.warning(request, '🔒 این درس ویژه است — برای دسترسی، بلیط آن را از فروشگاه بخر! 🛒')
            return redirect('shop:home')
''', 1, 'V: exclusive lesson gate')


patch(V, '''    attempts_count = QuizAttempt.objects.filter(user=request.user, quiz=quiz).count()
    if attempts_count >= quiz.max_attempts:
        messages.error(request, f'حداکثر {quiz.max_attempts} بار می‌توانید در این کوئیز شرکت کنید.')
        return redirect('language_academy:lesson_detail', lesson_id=quiz.lesson.id)
''', '''    attempts_count = QuizAttempt.objects.filter(user=request.user, quiz=quiz).count()
    if attempts_count >= quiz.max_attempts:
        # 🎫 بلیط تلاش مجدد: یک تلاش اضافه به‌ازای مصرف یک بلیط
        from shop.services import consume_item_by_effect
        r = consume_item_by_effect(request.user, 'retry_ticket', source={'quiz': quiz.id})
        if r.get('ok'):
            messages.info(request, '🎫 بلیط تلاش مجدد استفاده شد — یک تلاش اضافه گرفتی! موفق باشی 🍀')
        else:
            messages.error(request, f'حداکثر {quiz.max_attempts} بار می‌توانید در این کوئیز شرکت کنید. (می‌توانی «بلیط تلاش مجدد» از فروشگاه بخری 🎫)')
            return redirect('language_academy:lesson_detail', lesson_id=quiz.lesson.id)
''', 1, 'V: retry ticket flow')


patch(V, '''    if passed:
        request.user.add_xp(quiz.xp_reward, 'quiz_pass', f'Passed quiz: {quiz.title}')
        request.user.coins += quiz.coin_reward
        request.user.save()

    messages.warning(request, f'زمان کوئیز به پایان رسید! نمره شما: {final_score}%')
''', '''    if passed:
        _grant_pass_rewards_once(request.user, quiz, 'quiz')

    messages.warning(request, f'زمان کوئیز به پایان رسید! نمره شما: {final_score}%')
''', 1, 'V: submit_quiz_auto rewards')


patch(V, '''        if lesson_progress.xp_earned == 0:
            request.user.add_xp(lesson.xp_reward, 'lesson_completion', f'Completed: {lesson.name}')
            lesson_progress.xp_earned = lesson.xp_reward

        request.user.add_xp(quiz.xp_reward, 'quiz_pass', f'Passed quiz: {quiz.title}')
        request.user.coins += quiz.coin_reward
        request.user.save()
''', '''        if lesson_progress.xp_earned == 0:
            from economy.services import grant_xp as _grant_lesson_xp
            _grant_lesson_xp(request.user, lesson.xp_reward, source='lesson_completion',
                             source_id=lesson.id, rule_code='lesson_complete',
                             period_key=f'lesson:{lesson.id}')
            request.user.refresh_from_db(fields=['xp', 'level'])
            lesson_progress.xp_earned = lesson.xp_reward

        q_xp, q_coins, first_pass = _grant_pass_rewards_once(request.user, quiz, 'quiz')
        if not first_pass:
            messages.info(request, '🔁 این کوئیز را قبلاً پاس کرده‌ای — پاداش فقط برای «اولین قبولی» است.')
''', 1, 'V: submit_quiz rewards')


patch(V, '''    if passed:
        request.user.add_xp(exam.xp_reward, 'exam_pass', f'Passed exam: {exam.title}')
        request.user.coins += exam.coin_reward
        request.user.save()
''', '''    if passed:
        _grant_pass_rewards_once(request.user, exam, 'exam')
''', 2, 'V: exam rewards x2')


if FAILED:
    print('\n❌ شکست‌ها:')
    for f in FAILED:
        print('  -', f)
    sys.exit(1)
print('\n✅ همهٔ سیم‌کشی‌ها انجام شد.')
