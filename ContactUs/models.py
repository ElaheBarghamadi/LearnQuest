from django.db import models


class ContactModel(models.Model):
    name = models.CharField(max_length=50, verbose_name='نام و نام خانوادگی')
    email = models.EmailField(verbose_name='ایمیل')
    phone_number = models.TextField(verbose_name= 'شماره تلفن' , )
    message = models.TextField(verbose_name='پیام', blank=True)
    def __str__(self):
        return self.name
    class Meta:
        verbose_name = 'پیام'
        verbose_name_plural = 'پیام ها'
