from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("Messenger", "0002_alter_message_options_remove_message_receiver_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="message",
            name="content",
        ),
        migrations.AddField(
            model_name="message",
            name="encrypted_content",
            field=models.TextField(default=1),
            preserve_default=False,
        ),
    ]
