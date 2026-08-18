from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


class UserGameStats(models.Model):
    GAME_CHOICES = [
        ('memory', 'بازی حافظه'),
        ('puzzle', 'پازل عددی'),
        ('sudoku', 'سودوکو'),
        ('iq_test', 'تست هوش'),
        ('snake', 'بازی مار'),
        ('2048', 'بازی ۲۰۴۸'),
        ('reaction', 'تست سرعت واکنش'),
        ('simon', 'حافظه رنگی سایمون'),
        ('whack', 'ضربه به موش'),
        ('tictactoe', 'دوز باهوش'),
        ('language', 'بازی وصل کن'),
        ('guessing', 'حدس کلمه'),
        ('scramble', 'جورچین کلمات'),
        ('dictation', 'دیکته صوتی'),
        ('sprint', 'دوئل کلمات'),
        ('minesweeper', 'مین‌روب'),
        ('breakout', 'آجرشکن'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='game_stats')
    game_name = models.CharField(max_length=20, choices=GAME_CHOICES, verbose_name='نام بازی')
    games_played = models.IntegerField(default=0, verbose_name='تعداد بازی انجام شده')
    games_completed = models.IntegerField(default=0, verbose_name='تعداد بازی کامل شده')
    best_score = models.IntegerField(default=0, verbose_name='بهترین امتیاز')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ به‌روزرسانی')

    class Meta:
        unique_together = ['user', 'game_name']
        verbose_name = 'آمار بازی'
        verbose_name_plural = 'آمار بازی‌ها'
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.username} - {self.get_game_name_display()}"


class UserAchievement(models.Model):
    ACHIEVEMENT_CHOICES = [
        ('memory_10', '۱۰ بازی حافظه'),
        ('puzzle_10', '۱۰ بازی پازل'),
        ('sudoku_10', '۱۰ بازی سودوکو'),
        ('iq_10', '۱۰ بازی تست هوش'),
        ('memory_master', 'استاد حافظه'),
        ('puzzle_master', 'استاد پازل'),
        ('sudoku_master', 'استاد سودوکو'),
        ('iq_master', 'نابغه هوش'),
        ('language_10', '۱۰ بازی وصل کن'),
        ('guessing_10', '۱۰ بازی حدس کلمه'),
        ('scramble_10', '۱۰ بازی جورچین'),
        ('dictation_10', '۱۰ بازی دیکته صوتی'),
        ('sprint_10', '۱۰ دوئل کلمات'),
        ('minesweeper_10', '۱۰ بازی مین‌روب'),
        ('breakout_10', '۱۰ بازی آجرشکن'),
        ('language_master', 'استاد زبان'),
        ('word_genius', 'نابغه کلمات'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements')
    achievement_type = models.CharField(max_length=30, choices=ACHIEVEMENT_CHOICES, verbose_name='نوع دستاورد')
    name = models.CharField(max_length=100, verbose_name='نام دستاورد')
    description = models.TextField(blank=True, verbose_name='توضیحات')
    icon = models.CharField(max_length=50, default='trophy', verbose_name='آیکون')
    earned_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ دریافت')

    class Meta:
        unique_together = ['user', 'achievement_type']
        verbose_name = 'دستاورد'
        verbose_name_plural = 'دستاوردها'
        ordering = ['-earned_at']

    def __str__(self):
        return f"{self.user.username} - {self.name}"
