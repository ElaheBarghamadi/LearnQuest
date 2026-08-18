from django.shortcuts import render, redirect
from .forms import ContactForm
from .models import ContactModel
from django.views import View


class ContactUs_View(View):
    def get (self, request):
        if request.method == 'GET':
            form = ContactForm
            return render(request, 'contact_us.html', {
                'form': form
            })

    def post(self, request):
        if request.method == 'POST':
            form = ContactForm(request.POST)
            if form.is_valid():
                name = form.cleaned_data.get('name')
                email = form.cleaned_data.get('email')
                phone_number = form.cleaned_data.get('phone_number')
                message = form.cleaned_data.get('message')
                new_message = ContactModel(name=name, email=email, phone_number=phone_number, message=message)
                new_message.save()
                return redirect('index')
            else:
                return render(request, 'contact_us.html', {
                    'form': form,
                    'errors': True
                })
