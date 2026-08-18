from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Article, Comment


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'show_image', 'views', 'likes', 'published_at', 'is_featured']
    list_filter = ['category', 'is_featured', 'published_at']
    search_fields = ['title', 'content']
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ['is_featured']
    readonly_fields = ['views', 'likes']

    def show_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="border-radius: 8px;" />', obj.image.url)
        return '-'

    show_image.short_description = 'تصویر'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['user', 'article', 'short_content', 'likes', 'created_at', 'is_approved']
    list_filter = ['is_approved', 'created_at']
    search_fields = [ 'content']
    list_editable = ['is_approved']

    def short_content(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content

    short_content.short_description = 'متن نظر'
