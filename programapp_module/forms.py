from django import forms
import re


class NumbersForm(forms.Form):
    numbers = forms.CharField(
        label='اعداد خود را وارد کنید (با کاما جدا شده)',
        widget=forms.Textarea(attrs={
            'rows': 4,
            'class': 'form-control',
            'placeholder': 'مثال: 12, 45, 67, 23'
        })
    )

    def clean_numbers(self):
        data = self.cleaned_data.get('numbers')
        if not data:
            raise forms.ValidationError("لطفاً اعداد را وارد کنید.")
        if not re.fullmatch(r'^\s*-?\d+(\.\d+)?(\s*,\s*-?\d+(\.\d+)?)*\s*$', data):
            raise forms.ValidationError("لطفاً فقط اعداد را با کاما جدا کنید. مثال: 12, 45.5, 78")
        return data
