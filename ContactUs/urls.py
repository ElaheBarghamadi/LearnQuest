from django.urls import path
from .views import *
urlpatterns = [
    path('' ,ContactUs_View.as_view() , name = 'contact' )
]
