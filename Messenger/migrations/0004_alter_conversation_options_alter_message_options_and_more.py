from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("Messenger", "0003_remove_message_content_message_encrypted_content"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="conversation",
            options={
                "ordering": ["-updated_at"],
                "verbose_name": "مکالمه",
                "verbose_name_plural": "مکالمات",
            },
        ),
        migrations.AlterModelOptions(
            name="message",
            options={
                "ordering": ["created_at"],
                "verbose_name": "پیام",
                "verbose_name_plural": "پیام\u200cها",
            },
        ),
        migrations.AddField(
            model_name="conversation",
            name="name",
            field=models.CharField(
                blank=True, max_length=255, null=True, verbose_name="نام گروه"
            ),
        ),
        migrations.AlterField(
            model_name="message",
            name="encrypted_content",
            field=models.TextField(verbose_name="محتوای رمزنگاری\u200cشده"),
        ),
    ]
