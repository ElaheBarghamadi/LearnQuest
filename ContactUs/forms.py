from django import forms
from .models import ContactModel


class ContactForm(forms.Form):
    name = forms.CharField(
        max_length=50,
        min_length=5,
        widget=forms.TextInput(attrs={
            'class': "form-control",
            'type': "text",
            'id': "name",
            'name': "name",
            'required': "required",
            'placeholder': "نام خود را وارد کنید"
        }),
        error_messages={
            'required': 'نام و نام خانوادگی اجباری است ',
            'min_length': 'نام و نام خانوادگی حداقل پنج کارکتر باشد '
        }
    )

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': "form-control",
            'type': "email",
            'id': "email",
            'name': "email",
            'required': "required",
            'placeholder': "example@domain.com"
        }),
        error_messages={
            'required': 'ایمیل اجباری است ',
            'invalid': 'لطفا یک ایمیل معتبر وارد کنید !!'
        }
    )


    phone_number = forms.CharField(
        label='شماره تلفن',
        required=False,
        widget=forms.TextInput(attrs={
            'type': "tel",
            'name': "phone",
            'class': "form-control",
            'placeholder': "0912 123 4567",
            'id': "phone_number"
        })
    )

    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': "form-control",
            'id': "message",
            'name': "message",
            'rows': "5",
            'placeholder': "پیام خود را یادداشت کنید",
            'required': "required"
        })
    )
