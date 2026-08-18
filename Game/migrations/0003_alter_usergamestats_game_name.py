from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Game', '0002_alter_userachievement_achievement_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usergamestats',
            name='game_name',
            field=models.CharField(choices=[('memory', 'بازی حافظه'), ('puzzle', 'پازل عددی'), ('sudoku', 'سودوکو'), ('iq_test', 'تست هوش'), ('snake', 'بازی مار'), ('2048', 'بازی ۲۰۴۸'), ('reaction', 'تست سرعت واکنش')], max_length=20, verbose_name='نام بازی'),
        ),
    ]
