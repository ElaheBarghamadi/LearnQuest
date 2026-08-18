import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='category',
            options={'verbose_name': 'دسته\u200cبندی', 'verbose_name_plural': 'دسته\u200cبندی\u200cها'},
        ),
        migrations.AlterField(
            model_name='blogpost',
            name='author',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='posts', to=settings.AUTH_USER_MODEL, verbose_name='نویسنده'),
        ),
        migrations.AlterField(
            model_name='blogpost',
            name='category',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='posts', to='blog.category', verbose_name='دسته'),
        ),
        migrations.AlterField(
            model_name='blogpost',
            name='content',
            field=models.TextField(verbose_name='متن کامل'),
        ),
        migrations.AlterField(
            model_name='blogpost',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد'),
        ),
        migrations.AlterField(
            model_name='blogpost',
            name='excerpt',
            field=models.TextField(max_length=500, verbose_name='خلاصه'),
        ),
        migrations.AlterField(
            model_name='blogpost',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='blog/images/', verbose_name='تصویر شاخص'),
        ),
        migrations.AlterField(
            model_name='blogpost',
            name='is_published',
            field=models.BooleanField(default=True, verbose_name='منتشر شود'),
        ),
        migrations.AlterField(
            model_name='blogpost',
            name='likes',
            field=models.PositiveIntegerField(default=0, verbose_name='لایک'),
        ),
        migrations.AlterField(
            model_name='blogpost',
            name='published_at',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='تاریخ انتشار'),
        ),
        migrations.AlterField(
            model_name='blogpost',
            name='slug',
            field=models.SlugField(unique=True, verbose_name='اسلاگ'),
        ),
        migrations.AlterField(
            model_name='blogpost',
            name='title',
            field=models.CharField(max_length=250, verbose_name='عنوان'),
        ),
        migrations.AlterField(
            model_name='blogpost',
            name='views',
            field=models.PositiveIntegerField(default=0, verbose_name='بازدید'),
        ),
        migrations.AlterField(
            model_name='category',
            name='name',
            field=models.CharField(max_length=100, verbose_name='نام دسته'),
        ),
        migrations.AlterField(
            model_name='category',
            name='slug',
            field=models.SlugField(unique=True, verbose_name='اسلاگ'),
        ),
    ]
