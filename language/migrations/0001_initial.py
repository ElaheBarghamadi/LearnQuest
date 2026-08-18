from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Word',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('english_word', models.CharField(max_length=100, unique=True, verbose_name='کلمه انگلیسی')),
                ('persian_meaning', models.CharField(max_length=200, verbose_name='معنی فارسی')),
                ('level', models.CharField(choices=[('A1', 'A1 - مبتدی'), ('A2', 'A2 - مقدماتی'), ('B1', 'B1 - متوسط'), ('B2', 'B2 - بالای متوسط'), ('C1', 'C1 - پیشرفته')], default='A1', max_length=2, verbose_name='سطح')),
                ('example_sentence', models.TextField(blank=True, null=True, verbose_name='مثال')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')),
            ],
            options={
                'verbose_name': 'کلمه',
                'verbose_name_plural': 'کلمات',
                'ordering': ['english_word'],
            },
        ),
    ]
