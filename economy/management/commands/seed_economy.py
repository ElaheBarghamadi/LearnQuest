from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from economy.models import (RewardRule, DailyRewardDay, Season, SeasonLevel,
                            PetSpecies, Wallet, Transaction)


class Command(BaseCommand):
    help = 'Seed economy: reward rules, daily rewards, season 1, pet species, wallet backfill'

    def handle(self, *args, **options):
        self._rules()
        self._daily()
        self._season()
        self._pets()
        self._backfill_wallets()
        self.stdout.write(self.style.SUCCESS('✅ seed_economy کامل شد'))

    def _rules(self):
        rules = [
            ('lesson_complete', 'تکمیل درس', 'xp', 50, 0),
            ('quiz_pass', 'قبولی کوئیز (اولین بار)', 'xp', 50, 0),
            ('exam_pass', 'قبولی امتحان (اولین بار)', 'xp', 100, 0),
            ('game_play', 'انجام بازی', 'xp', 20, 100),
            ('daily_login', 'ورود روزانه', 'coin', 10, 1),
            ('review', 'مرور واژگان/تکرار فاصله‌دار', 'xp', 10, 60),
        ]
        for code, name, cur, amount, limit in rules:
            RewardRule.objects.update_or_create(
                code=code, defaults={'name': name, 'currency': cur,
                                     'default_amount': amount, 'daily_limit': limit})
        self.stdout.write('  📜 قوانین پاداش: ۶ قانون')

    def _daily(self):
        plan = [
            (1, 10, 5, 0), (2, 15, 5, 0), (3, 20, 8, 0),
            (4, 25, 8, 1), (5, 30, 10, 0), (6, 35, 10, 1), (7, 50, 20, 3),
        ]
        for day, c, x, g in plan:
            DailyRewardDay.objects.update_or_create(day=day, defaults={'coins': c, 'xp': x, 'gems': g})
        self.stdout.write('  📅 جایزهٔ ورود روزانه: چرخهٔ ۷ روزه')

    def _season(self):
        now = timezone.now()
        season, created = Season.objects.update_or_create(
            name='فصل اول: بهار دانش', defaults=dict(
                emoji='🌸', description='۶۰ روز رقابت، یادگیری و جایزه! با هر XP که می‌گیری در فصل هم بالا می‌روی.',
                starts_at=now - timezone.timedelta(days=1),
                ends_at=now + timezone.timedelta(days=60),
                is_active=True, pass_price_gems=50))
        levels = [
            (1, 100,  {'coins': 30},               {'coins': 100}),
            (2, 250,  {'coins': 40},               {'coins': 120, 'product_slug': 'hint-ticket'}),
            (3, 450,  {'coins': 50},               {'xp': 150}),
            (4, 700,  {'coins': 60},               {'coins': 150, 'product_slug': 'lucky-spin'}),
            (5, 1000, {'gems': 3},                 {'product_slug': 'mystery-box'}),
            (6, 1400, {'coins': 80},               {'coins': 200, 'gems': 5}),
            (7, 1900, {'coins': 100, 'gems': 2},   {'product_slug': 'xp-booster-15'}),
            (8, 2500, {'coins': 120, 'gems': 3},   {'coins': 300, 'product_slug': 'time-card'}),
            (9, 3200, {'coins': 150, 'gems': 4},   {'gems': 15, 'product_slug': 'retry-ticket'}),
            (10, 4000, {'coins': 200, 'gems': 6},  {'gems': 30, 'product_slug': 'frame-royal'}),
        ]
        for lvl, req, free, prem in levels:
            SeasonLevel.objects.update_or_create(
                season=season, level_number=lvl,
                defaults={'xp_required': req, 'free_reward': free, 'premium_reward': prem})
        self.stdout.write(f'  🌸 فصل فعال: {season} با {len(levels)} پله')

    def _pets(self):
        species = [
            ('جوجه', '🐤', 'common', 'جوجهٔ کوچک و بامزه — بهترین دوست تازه‌کارها!', 'pet-chick'),
            ('روباه', '🦊', 'rare', 'روباه باهوش — همراهی تیز برای مسیر یادگیری.', 'pet-fox'),
            ('پاندا', '🐼', 'epic', 'پاندای آرام و دوست‌داشتنی؛ عاشق درس خواندن!', 'pet-panda'),
            ('اژدهای کوچک', '🐲', 'legendary', 'اژدهای افسانه‌ای — فقط برای قهرمانان واقعی!', 'pet-dragon'),
        ]
        for name, emoji, rarity, desc, slug in species:
            PetSpecies.objects.update_or_create(
                product_slug=slug, defaults={'name': name, 'emoji': emoji,
                                             'rarity': rarity, 'description': desc})
        self.stdout.write('  🐾 گونه‌های پت: ۴ گونه')

    def _backfill_wallets(self):
        User = get_user_model()
        created_n = synced = 0
        for user in User.objects.all():
            wallet, was_created = Wallet.objects.get_or_create(user=user)
            if was_created:
                created_n += 1

            if getattr(user, 'coins', 0) and not Transaction.objects.filter(user=user).exists():
                if wallet.coins != user.coins:
                    wallet.coins = user.coins
                    wallet.save(update_fields=['coins'])
                    Transaction.objects.create(
                        user=user, currency='coin', amount=user.coins,
                        balance_after=user.coins, type='admin_adjust', source='legacy_backfill',
                        idempotency_key=f'backfill:{user.pk}',
                        metadata={'note': 'انتقال سکه‌های سیستم قدیمی به کیف پول جدید'})
                    synced += 1
        self.stdout.write(f'  👛 کیف پول: {created_n} ساخته شد، {synced} بک‌فیل سکه')
