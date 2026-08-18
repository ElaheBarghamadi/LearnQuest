from django.urls import path
from .views import *

urlpatterns = [
    path('', view=index, name='index'),
    path('games/', view=games, name='games'),
    path('profile/', view=profile_view, name='profile'),
    path("edit-profile/", view=edit_profile_view, name="edit_profile"),
    path('guide/', view=guide, name='guide'),
    path('add_test_activity/' , view=add_test_activity, name='add_test_activity'),
    path('remove-avatar/', view=remove_avatar, name='remove_avatar'),
]
