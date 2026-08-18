from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse

User = get_user_model()


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="نام دسته‌بندی")
    slug = models.SlugField(unique=True, allow_unicode=True, verbose_name="اسلاگ")

    class Meta:
        verbose_name = "دسته‌بندی"
        verbose_name_plural = "دسته‌بندی‌ها"

    def __str__(self):
        return self.name


class Article(models.Model):
    title = models.CharField(max_length=250, verbose_name="عنوان مقاله")
    slug = models.SlugField(unique=True, allow_unicode=True, verbose_name="اسلاگ")
    excerpt = models.TextField(verbose_name="خلاصه مقاله")
    content = models.TextField(verbose_name="متن کامل مقاله")
    image = models.ImageField(upload_to='blog_images/', verbose_name="تصویر شاخص")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='articles', verbose_name="دسته‌بندی")

    views = models.PositiveIntegerField(default=0, verbose_name="تعداد بازدید")
    likes = models.PositiveIntegerField(default=0, verbose_name="تعداد لایک")

    published_at = models.DateTimeField(default=timezone.now, verbose_name="تاریخ انتشار")
    is_featured = models.BooleanField(default=False, verbose_name="مقاله ویژه")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "مقاله"
        verbose_name_plural = "مقالات"
        ordering = ['-published_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('blog:article_detail', args=[self.pk])

    @property
    def reading_time(self):
        words = len((self.content or '').split())
        return max(1, round(words / 200))

    def increment_views(self):
        self.views += 1
        self.save(update_fields=['views'])

    def increment_likes(self):
        self.likes += 1
        self.save(update_fields=['likes'])


class Comment(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='comments', verbose_name="مقاله")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blog_comments', verbose_name="کاربر")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies',
                               verbose_name="پاسخ به")
    content = models.TextField(verbose_name="متن نظر")
    likes = models.PositiveIntegerField(default=0, verbose_name="تعداد لایک")
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=True, verbose_name="تایید شده")
    class Meta:
        verbose_name = "نظر"
        verbose_name_plural = "نظرات"
        ordering = ['created_at']

    def __str__(self):
        return f"نظر {self.user.username} برای {self.article.title}"
