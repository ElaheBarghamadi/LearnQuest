from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Game', '0003_alter_usergamestats_game_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usergamestats',
            name='game_name',
            field=models.CharField(choices=[('memory', 'بازی حافظه'), ('puzzle', 'پازل عددی'), ('sudoku', 'سودوکو'), ('iq_test', 'تست هوش'), ('snake', 'بازی مار'), ('2048', 'بازی ۲۰۴۸'), ('reaction', 'تست سرعت واکنش'), ('simon', 'حافظه رنگی سایمون'), ('whack', 'ضربه به موش'), ('tictactoe', 'دوز باهوش')], max_length=20, verbose_name='نام بازی'),
        ),
    ]
