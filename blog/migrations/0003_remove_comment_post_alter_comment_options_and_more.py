import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0002_alter_category_options_alter_blogpost_author_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(
            model_name='comment',
            name='post',
        ),
        migrations.AlterModelOptions(
            name='comment',
            options={'ordering': ['created_at'], 'verbose_name': 'نظر', 'verbose_name_plural': 'نظرات'},
        ),
        migrations.RemoveField(
            model_name='comment',
            name='author',
        ),
        migrations.AddField(
            model_name='comment',
            name='user',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='blog_comments', to=settings.AUTH_USER_MODEL, verbose_name='کاربر'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='category',
            name='name',
            field=models.CharField(max_length=100, verbose_name='نام دسته\u200cبندی'),
        ),
        migrations.AlterField(
            model_name='category',
            name='slug',
            field=models.SlugField(allow_unicode=True, unique=True, verbose_name='اسلاگ'),
        ),
        migrations.AlterField(
            model_name='comment',
            name='content',
            field=models.TextField(verbose_name='متن نظر'),
        ),
        migrations.AlterField(
            model_name='comment',
            name='is_approved',
            field=models.BooleanField(default=True, verbose_name='تایید شده'),
        ),
        migrations.AlterField(
            model_name='comment',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='replies', to='blog.comment', verbose_name='پاسخ به'),
        ),
        migrations.CreateModel(
            name='Article',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=250, verbose_name='عنوان مقاله')),
                ('slug', models.SlugField(allow_unicode=True, unique=True, verbose_name='اسلاگ')),
                ('excerpt', models.TextField(verbose_name='خلاصه مقاله')),
                ('content', models.TextField(verbose_name='متن کامل مقاله')),
                ('image', models.ImageField(upload_to='blog_images/', verbose_name='تصویر شاخص')),
                ('views', models.PositiveIntegerField(default=0, verbose_name='تعداد بازدید')),
                ('likes', models.PositiveIntegerField(default=0, verbose_name='تعداد لایک')),
                ('published_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='تاریخ انتشار')),
                ('is_featured', models.BooleanField(default=False, verbose_name='مقاله ویژه')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='articles', to='blog.category', verbose_name='دسته\u200cبندی')),
            ],
            options={
                'verbose_name': 'مقاله',
                'verbose_name_plural': 'مقالات',
                'ordering': ['-published_at'],
            },
        ),
        migrations.AddField(
            model_name='comment',
            name='article',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='blog.article', verbose_name='مقاله'),
            preserve_default=False,
        ),
        migrations.DeleteModel(
            name='BlogPost',
        ),
    ]
