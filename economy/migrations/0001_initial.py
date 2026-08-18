import django

import django.db.models.deletion
import django.utils.timezone
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DailyRewardDay',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('day', models.PositiveSmallIntegerField(unique=True, verbose_name='روز چرخه (۱..N)')),
                ('coins', models.PositiveIntegerField(default=10)),
                ('xp', models.PositiveIntegerField(default=5)),
                ('gems', models.PositiveIntegerField(default=0)),
            ],
            options={
                'verbose_name': 'روز جایزه',
                'verbose_name_plural': 'برنامهٔ جایزهٔ روزانه',
                'ordering': ['day'],
            },
        ),
        migrations.CreateModel(
            name='PetSpecies',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=60)),
                ('emoji', models.CharField(default='🐣', max_length=8)),
                ('rarity', models.CharField(choices=[('common', 'معمولی'), ('rare', 'کمیاب'), ('epic', 'حماسی'), ('legendary', 'افسانه\u200cای')], default='common', max_length=12)),
                ('description', models.TextField(blank=True)),
                ('product_slug', models.SlugField(help_text='خرید این محصول = اخذ این پت', unique=True, verbose_name='اسلاگ محصول در فروشگاه')),
            ],
            options={
                'verbose_name': 'گونهٔ پت',
                'verbose_name_plural': 'گونه\u200cهای پت',
            },
        ),
        migrations.CreateModel(
            name='RewardRule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=60, unique=True, verbose_name='کد قانون')),
                ('name', models.CharField(max_length=120, verbose_name='نام فارسی')),
                ('currency', models.CharField(choices=[('coin', 'سکه 🪙'), ('gem', 'الماس 💎'), ('xp', 'امتیاز تجربه ⭐')], default='xp', max_length=8)),
                ('default_amount', models.PositiveIntegerField(default=10, verbose_name='مقدار پیش\u200cفرض')),
                ('daily_limit', models.PositiveIntegerField(default=0, verbose_name='سقف روزانه (۰=نامحدود)')),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'قانون پاداش',
                'verbose_name_plural': 'قوانین پاداش',
            },
        ),
        migrations.CreateModel(
            name='Season',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='نام فصل')),
                ('emoji', models.CharField(default='🌸', max_length=8)),
                ('description', models.TextField(blank=True)),
                ('starts_at', models.DateTimeField()),
                ('ends_at', models.DateTimeField()),
                ('is_active', models.BooleanField(default=False)),
                ('pass_price_gems', models.PositiveIntegerField(default=50, verbose_name='قیمت پس (الماس)')),
            ],
            options={
                'verbose_name': 'فصل',
                'verbose_name_plural': 'فصل\u200cها',
            },
        ),
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(db_index=True, max_length=60)),
                ('details', models.JSONField(blank=True, default=dict)),
                ('ip', models.GenericIPAddressField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('actor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='economy_audit_acts', to=settings.AUTH_USER_MODEL, verbose_name='عامل')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='economy_audit_logs', to=settings.AUTH_USER_MODEL, verbose_name='کاربر هدف')),
            ],
            options={
                'verbose_name': 'لاگ ممیز',
                'verbose_name_plural': 'لاگ\u200cهای ممیز',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ActiveBoost',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('boost_type', models.CharField(choices=[('xp', 'XP ⭐'), ('coin', 'سکه 🪙')], max_length=8)),
                ('multiplier', models.FloatField(default=1.5)),
                ('expires_at', models.DateTimeField()),
                ('inventory_item_id', models.PositiveIntegerField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='boosts', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'بوستر فعال',
                'verbose_name_plural': 'بوسترهای فعال',
                'ordering': ['-expires_at'],
                'indexes': [models.Index(fields=['user', 'boost_type', 'expires_at'], name='boost_user_expire_idx')],
            },
        ),
        migrations.CreateModel(
            name='DailyRewardClaim',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('claim_date', models.DateField(verbose_name='روز')),
                ('day_index', models.PositiveSmallIntegerField(default=1, verbose_name='روز چرخه')),
                ('streak', models.PositiveIntegerField(default=1)),
                ('claimed_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='daily_claims', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'جایزهٔ گرفته\u200cشدهٔ روزانه',
                'verbose_name_plural': 'جایزه\u200cهای روزانه',
                'constraints': [models.UniqueConstraint(fields=('user', 'claim_date'), name='uniq_daily_claim')],
            },
        ),
        migrations.CreateModel(
            name='LeaderboardEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('period', models.CharField(max_length=40)),
                ('xp', models.PositiveIntegerField(default=0)),
                ('rank', models.PositiveIntegerField(default=0)),
                ('computed_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='leaderboard_rows', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'ردیف لیدربرد',
                'verbose_name_plural': 'لیدربرد',
                'indexes': [models.Index(fields=['period', 'rank'], name='lb_period_rank_idx'), models.Index(fields=['period', '-xp'], name='lb_period_xp_idx')],
                'constraints': [models.UniqueConstraint(fields=('period', 'user'), name='uniq_lb_entry')],
            },
        ),
        migrations.CreateModel(
            name='RewardGrant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rule_code', models.CharField(max_length=100)),
                ('period_key', models.CharField(max_length=60)),
                ('granted_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reward_grants', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'سند پاداش',
                'verbose_name_plural': 'اسناد پاداش',
                'indexes': [models.Index(fields=['user', 'rule_code', 'granted_at'], name='grant_user_rule_idx')],
                'constraints': [models.UniqueConstraint(fields=('user', 'rule_code', 'period_key'), name='uniq_reward_grant')],
            },
        ),
        migrations.CreateModel(
            name='SeasonLevel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('level_number', models.PositiveSmallIntegerField()),
                ('xp_required', models.PositiveIntegerField(default=100, verbose_name='XP فصل لازم')),
                ('free_reward', models.JSONField(blank=True, default=dict, help_text='{"coins": 50} یا {"gems": 2} یا {"product_slug": "mystery-box-1"}')),
                ('premium_reward', models.JSONField(blank=True, default=dict)),
                ('season', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='levels', to='economy.season')),
            ],
            options={
                'verbose_name': 'پلهٔ فصل',
                'verbose_name_plural': 'پله\u200cهای فصل',
                'ordering': ['level_number'],
                'constraints': [models.UniqueConstraint(fields=('season', 'level_number'), name='uniq_season_level')],
            },
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('currency', models.CharField(choices=[('coin', 'سکه 🪙'), ('gem', 'الماس 💎'), ('xp', 'امتیاز تجربه ⭐')], max_length=8, verbose_name='ارز')),
                ('amount', models.IntegerField(verbose_name='مقدار (مثبت/منفی)')),
                ('balance_after', models.IntegerField(verbose_name='موجودی پس از تراکنش')),
                ('type', models.CharField(choices=[('earn', 'کسب'), ('spend', 'خرج'), ('reward', 'پاداش'), ('refund', 'بازگشت وجه'), ('admin_adjust', 'تنظیم دستی ادمین'), ('consume', 'مصرف آیتم')], max_length=20, verbose_name='نوع')),
                ('source', models.CharField(max_length=60, verbose_name='منبع')),
                ('source_id', models.CharField(blank=True, default='', max_length=60, verbose_name='شناسه منبع')),
                ('idempotency_key', models.CharField(default=uuid.uuid4, max_length=100, unique=True, verbose_name='کلید یکتا (ضد تکرار)')),
                ('metadata', models.JSONField(blank=True, default=dict, verbose_name='متادیتا')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('actor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='economy_actions', to=settings.AUTH_USER_MODEL, verbose_name='عامل (ادمین)')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transactions', to=settings.AUTH_USER_MODEL, verbose_name='کاربر')),
            ],
            options={
                'verbose_name': 'تراکنش',
                'verbose_name_plural': 'تراکنش\u200cها',
                'ordering': ['-created_at'],
                'indexes': [models.Index(fields=['user', 'created_at'], name='tx_user_date_idx'), models.Index(fields=['user', 'currency', 'created_at'], name='tx_user_cur_date_idx'), models.Index(fields=['source', 'source_id'], name='tx_source_idx')],
            },
        ),
        migrations.CreateModel(
            name='UserPet',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=40, verbose_name='نام پت')),
                ('level', models.PositiveSmallIntegerField(default=1)),
                ('xp', models.PositiveIntegerField(default=0)),
                ('is_active', models.BooleanField(default=False, verbose_name='پت فعال (نمایش)')),
                ('last_fed_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('adopted_at', models.DateTimeField(auto_now_add=True)),
                ('species', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='pets', to='economy.petspecies')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pets', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'پت کاربر',
                'verbose_name_plural': 'پت\u200cهای کاربران',
                'constraints': [models.UniqueConstraint(fields=('user', 'species'), name='uniq_user_pet_species')],
            },
        ),
        migrations.CreateModel(
            name='UserSeasonPass',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('has_pass', models.BooleanField(default=False, verbose_name='دارای پس ویژه')),
                ('season_xp', models.PositiveIntegerField(default=0)),
                ('claimed_free', models.JSONField(blank=True, default=list, help_text='لیست سطح\u200cهای رایگان گرفته\u200cشده')),
                ('claimed_premium', models.JSONField(blank=True, default=list)),
                ('season', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='participants', to='economy.season')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='season_passes', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'پاس فصل کاربر',
                'verbose_name_plural': 'پاس فصل\u200cها',
                'constraints': [models.UniqueConstraint(fields=('user', 'season'), name='uniq_user_season')],
            },
        ),
        migrations.CreateModel(
            name='Wallet',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('coins', models.PositiveIntegerField(default=0, verbose_name='سکه')),
                ('gems', models.PositiveIntegerField(default=0, verbose_name='الماس')),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='wallet', to=settings.AUTH_USER_MODEL, verbose_name='کاربر')),
            ],
            options={
                'verbose_name': 'کیف پول',
                'verbose_name_plural': 'کیف پول\u200cها',
                'constraints': [models.CheckConstraint(**{("condition" if django.VERSION >= (5, 1) else "check"):models.Q(('coins__gte', 0))}, name='wallet_coins_nonneg'), models.CheckConstraint(**{("condition" if django.VERSION >= (5, 1) else "check"):models.Q(('gems__gte', 0))}, name='wallet_gems_nonneg')],
            },
        ),
    ]
