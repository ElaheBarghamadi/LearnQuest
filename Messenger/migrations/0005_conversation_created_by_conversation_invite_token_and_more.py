import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Messenger', '0004_alter_conversation_options_alter_message_options_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='conversation',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_groups', to=settings.AUTH_USER_MODEL, verbose_name='سازنده (مدیر گروه)'),
        ),
        migrations.AddField(
            model_name='conversation',
            name='invite_token',
            field=models.CharField(blank=True, max_length=32, null=True, unique=True, verbose_name='توکن لینک دعوت'),
        ),
        migrations.AddField(
            model_name='conversation',
            name='is_group',
            field=models.BooleanField(default=False, verbose_name='گروه است؟'),
        ),
        migrations.CreateModel(
            name='BlockedUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('blocked', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='blocked_by', to=settings.AUTH_USER_MODEL, verbose_name='بلاک\u200cشده')),
                ('blocker', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='blocks_made', to=settings.AUTH_USER_MODEL, verbose_name='بلاک\u200cکننده')),
            ],
            options={
                'verbose_name': 'بلاک کاربر',
                'verbose_name_plural': 'بلاک\u200cهای کاربران',
                'unique_together': {('blocker', 'blocked')},
            },
        ),
    ]
