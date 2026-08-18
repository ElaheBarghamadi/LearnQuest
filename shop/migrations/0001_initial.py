import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('economy', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=80, verbose_name='نام')),
                ('slug', models.SlugField(allow_unicode=True, unique=True)),
                ('emoji', models.CharField(default='🛍️', max_length=8)),
                ('order', models.PositiveSmallIntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='children', to='shop.category')),
            ],
            options={
                'verbose_name': 'دسته\u200cبندی فروشگاه',
                'verbose_name_plural': 'دسته\u200cبندی\u200cهای فروشگاه',
                'ordering': ['order', 'name'],
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120, verbose_name='نام محصول')),
                ('slug', models.SlugField(allow_unicode=True, unique=True)),
                ('product_type', models.CharField(choices=[('cosmetic', 'آرایشی'), ('consumable', 'مصرفی'), ('booster', 'بوستر زمانی'), ('unlock', 'بازکننده محتوا'), ('bundle', 'بسته (باندل)'), ('currency_pack', 'بسته ارز (آینده)')], max_length=20, verbose_name='نوع')),
                ('effect_type', models.CharField(help_text='مثل frame / username_color / xp_booster / pet / mystery_box / exclusive_lesson', max_length=40, verbose_name='کد اثر')),
                ('effect_payload', models.JSONField(blank=True, default=dict, help_text='مثل {"frame_class":"frame-gold"} یا {"multiplier":2,"hours":24}', verbose_name='پیلود اثر')),
                ('description', models.TextField(blank=True)),
                ('preview_emoji', models.CharField(blank=True, default='', max_length=8)),
                ('image', models.ImageField(blank=True, null=True, upload_to='shop_products/')),
                ('price_coins', models.PositiveIntegerField(default=0, verbose_name='قیمت (سکه)')),
                ('price_gems', models.PositiveIntegerField(default=0, verbose_name='قیمت (الماس)')),
                ('discount_percent', models.PositiveSmallIntegerField(default=0, verbose_name='تخفیف ٪')),
                ('discount_ends_at', models.DateTimeField(blank=True, null=True)),
                ('is_featured', models.BooleanField(default=False, verbose_name='ویژه')),
                ('is_active', models.BooleanField(default=True)),
                ('stock_limit', models.PositiveIntegerField(blank=True, null=True, verbose_name='موجودی محدود (خالی=نامحدود)')),
                ('sold_count', models.PositiveIntegerField(default=0)),
                ('per_user_limit', models.PositiveIntegerField(default=0, verbose_name='سقف خرید هر کاربر (۰=نامحدود)')),
                ('available_from', models.DateTimeField(blank=True, null=True)),
                ('available_until', models.DateTimeField(blank=True, null=True)),
                ('views_count', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('bundle_items', models.ManyToManyField(blank=True, related_name='bundled_in', to='shop.product', verbose_name='اقلام داخل باندل')),
                ('category', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='products', to='shop.category', verbose_name='دسته')),
            ],
            options={
                'verbose_name': 'محصول',
                'verbose_name_plural': 'محصولات',
                'ordering': ['-is_featured', '-created_at'],
            },
        ),
        migrations.CreateModel(
            name='InventoryItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('equipped', models.BooleanField(default=False)),
                ('source', models.CharField(default='shop', max_length=30)),
                ('acquired_at', models.DateTimeField(auto_now_add=True)),
                ('used_at', models.DateTimeField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='inventory', to=settings.AUTH_USER_MODEL)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='inventory_items', to='shop.product')),
            ],
            options={
                'verbose_name': 'آیتم موجودی',
                'verbose_name_plural': 'موجودی کاربران',
            },
        ),
        migrations.CreateModel(
            name='Purchase',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('coins_paid', models.PositiveIntegerField(default=0)),
                ('gems_paid', models.PositiveIntegerField(default=0)),
                ('status', models.CharField(choices=[('completed', 'تکمیل\u200cشده'), ('refunded', 'بازگشت\u200cداده\u200cشده'), ('failed', 'ناموفق')], default='completed', max_length=12)),
                ('idempotency_key', models.CharField(max_length=100, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('refunded_at', models.DateTimeField(blank=True, null=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='purchases', to='shop.product')),
                ('transaction', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='purchases', to='economy.transaction')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='purchases', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'خرید',
                'verbose_name_plural': 'خریدها',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='RecentlyViewed',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('viewed_at', models.DateTimeField(auto_now=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='shop.product')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recently_viewed', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'بازدید اخیر',
                'verbose_name_plural': 'بازدیدهای اخیر',
                'ordering': ['-viewed_at'],
            },
        ),
        migrations.CreateModel(
            name='Wishlist',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('added_at', models.DateTimeField(auto_now_add=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='wishlisted_by', to='shop.product')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='wishlist', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'علاقه\u200cمندی',
                'verbose_name_plural': 'علاقه\u200cمندی\u200cها',
            },
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['is_active', 'is_featured'], name='prod_active_feat_idx'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['category', 'is_active'], name='prod_cat_idx'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['price_coins'], name='prod_price_idx'),
        ),
        migrations.AddIndex(
            model_name='inventoryitem',
            index=models.Index(fields=['user', 'equipped'], name='inv_user_equipped_idx'),
        ),
        migrations.AddConstraint(
            model_name='inventoryitem',
            constraint=models.UniqueConstraint(fields=('user', 'product'), name='uniq_inventory_user_product'),
        ),
        migrations.AddIndex(
            model_name='purchase',
            index=models.Index(fields=['user', 'created_at'], name='purchase_user_idx'),
        ),
        migrations.AddConstraint(
            model_name='recentlyviewed',
            constraint=models.UniqueConstraint(fields=('user', 'product'), name='uniq_recent_view'),
        ),
        migrations.AddConstraint(
            model_name='wishlist',
            constraint=models.UniqueConstraint(fields=('user', 'product'), name='uniq_wishlist'),
        ),
    ]
