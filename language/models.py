from django.utils import timezone
from django.db import models


class Word(models.Model):
    LEVEL_CHOICES = [
        ('A1', 'A1 - مبتدی'),
        ('A2', 'A2 - مقدماتی'),
        ('B1', 'B1 - متوسط'),
        ('B2', 'B2 - بالای متوسط'),
        ('C1', 'C1 - پیشرفته'),
    ]

    english_word = models.CharField(max_length=100, unique=True, verbose_name='کلمه انگلیسی')
    persian_meaning = models.CharField(max_length=200, verbose_name='معنی فارسی')
    level = models.CharField(max_length=2, choices=LEVEL_CHOICES, default='A1', verbose_name='سطح')
    example_sentence = models.TextField(blank=True, null=True, verbose_name='مثال')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='تاریخ ایجاد')
    def __str__(self):
        return f"{self.english_word} - {self.persian_meaning}"

    class Meta:
        verbose_name = 'کلمه'
        verbose_name_plural = 'کلمات'
        ordering = ['english_word']
