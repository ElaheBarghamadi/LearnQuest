
from django.urls import path
from django.views.generic import edit

from .views import *
urlpatterns = [
    path('', view=index, name='index'),
    path('english/', view=english, name='english'),
    path('games/', view=games, name='games'),
    path('blog/', view=blog, name='blog'),
    path('profile/', view=profile, name='profile'),
    path("edit-profile/", view=edit_profile, name="edit_profile"),

]
