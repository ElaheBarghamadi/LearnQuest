import json

from django import forms
from django.utils.text import slugify

from .models import Product


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name', 'slug', 'category', 'product_type', 'effect_type',
            'effect_payload', 'description', 'preview_emoji', 'image',
            'price_coins', 'price_gems', 'discount_percent', 'discount_ends_at',
            'is_featured', 'is_active', 'stock_limit', 'per_user_limit',
            'available_from', 'available_until', 'bundle_items',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'خالی = خودکار از نام'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'product_type': forms.Select(attrs={'class': 'form-select'}),
            'effect_type': forms.TextInput(attrs={
                'class': 'form-control', 'dir': 'ltr',
                'placeholder': 'frame / pet / xp_booster / exclusive_lesson / mystery_box ...'}),
            'effect_payload': forms.Textarea(attrs={
                'class': 'form-control', 'dir': 'ltr', 'rows': 3,
                'placeholder': '{"frame_class":"frame-gold"} یا {"lesson_id": 5}'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'preview_emoji': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '🎁'}),
            'price_coins': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'price_gems': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'discount_percent': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
            'discount_ends_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'stock_limit': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'per_user_limit': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'available_from': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'available_until': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'bundle_items': forms.SelectMultiple(attrs={'class': 'form-select', 'size': 6}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['slug'].required = False
        self.fields['category'].required = False
        for f in ('discount_ends_at', 'available_from', 'available_until'):
            self.fields[f].input_formats = ['%Y-%m-%dT%H:%M']
            self.fields[f].required = False
        if self.instance and self.instance.pk:
            self.fields['bundle_items'].queryset = Product.objects.exclude(pk=self.instance.pk)
        self.fields['bundle_items'].help_text = 'فقط برای محصولات «بسته» — آیتم‌های داخل باندل را انتخاب کنید (Ctrl+Click)'

    def clean_slug(self):
        slug = (self.cleaned_data.get('slug') or '').strip()
        name = (self.cleaned_data.get('name') or '').strip()
        if not slug:
            base = slugify(name, allow_unicode=True) or 'product'
            slug = base
            i = 2
            qs = Product.objects.all()
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            while qs.filter(slug=slug).exists():
                slug = f'{base}-{i}'
                i += 1
        return slug

    def clean_effect_payload(self):
        data = self.cleaned_data.get('effect_payload')
        if data in (None, ''):
            return {}
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except ValueError:
                raise forms.ValidationError('پیلود اثر باید JSON معتبر باشد (مثل {"hours": 24}).')
        if not isinstance(data, dict):
            raise forms.ValidationError('پیلود اثر باید یک آبجکت JSON باشد ({...}).')
        if len(json.dumps(data, ensure_ascii=False)) > 2000:
            raise forms.ValidationError('پیلود اثر خیلی بزرگ است (حداکثر ۲۰۰۰ نویسه).')
        return data

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('name', '').strip():
            self.add_error('name', 'نام محصول الزامی است.')
        if not (cleaned.get('effect_type') or '').strip():
            self.add_error('effect_type', 'کد اثر الزامی است (مثل frame یا exclusive_lesson).')
        if cleaned.get('product_type') == 'bundle' and not cleaned.get('bundle_items'):
            self.add_error('bundle_items', 'برای بسته، حداقل یک آیتم انتخاب کنید.')
        av_from = cleaned.get('available_from')
        av_until = cleaned.get('available_until')
        if av_from and av_until and av_until <= av_from:
            self.add_error('available_until', 'پایان دسترسی باید بعد از شروع باشد.')
        return cleaned
