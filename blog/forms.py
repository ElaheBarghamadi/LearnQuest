from django import forms
from django.utils.text import slugify

from .models import Article, Category


class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ['title', 'slug', 'excerpt', 'content', 'image', 'category',
                  'published_at', 'is_published', 'is_featured', 'meta_description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 250}),
            'slug': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 250, 'placeholder': 'اختیاری — خودکار ساخته می‌شود'}),
            'excerpt': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'content': forms.Textarea(attrs={'rows': 14, 'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'published_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'meta_description': forms.Textarea(attrs={'rows': 2, 'class': 'form-control', 'maxlength': 300,
                                                      'placeholder': 'اختیاری — نمایش در گوگل؛ اگر خالی باشد از خلاصه استفاده می‌شود'}),
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['slug'].required = False
        self.fields['image'].required = False
        self.fields['published_at'].input_formats = ('%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M')

    def clean_slug(self):
        raw = (self.cleaned_data.get('slug') or '').strip()
        title = (self.cleaned_data.get('title') or '').strip()
        slug = slugify(raw or title, allow_unicode=True)[:240]
        if not slug:
            slug = 'article'
        base, i = slug, 2
        qs = Article.objects.filter(slug=slug)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        while qs.exists():
            slug = f'{base}-{i}'
            i += 1
            qs = Article.objects.filter(slug=slug)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
        return slug


class CategoryQuickForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'slug']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 100}),
            'slug': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 100, 'placeholder': 'اختیاری — خودکار'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['slug'].required = False

    def clean_slug(self):
        raw = (self.cleaned_data.get('slug') or '').strip()
        name = (self.cleaned_data.get('name') or '').strip()
        slug = slugify(raw or name, allow_unicode=True)[:95]
        if not slug:
            slug = 'category'
        base, i = slug, 2
        while Category.objects.filter(slug=slug).exists():
            slug = f'{base}-{i}'
            i += 1
        return slug


from .models import Comment


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'comment-input',
                'placeholder': 'نظر خود را بنویسید...',
                'rows': 3
            }),
        }
