from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [('Messenger', '0005_conversation_created_by_conversation_invite_token_and_more')]
    operations = [migrations.AddField(model_name='message', name='reply_to', field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='replies', to='Messenger.message', verbose_name='پاسخ به'))]
