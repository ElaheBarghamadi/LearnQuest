from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView


admin.site.site_header = '⚙️ مدیریت LearnQuest'
admin.site.site_title = 'مدیریت LearnQuest'
admin.site.index_title = 'داشبورد مدیریت پلتفرم آموزش گیمیفای‌شده'

urlpatterns = [
    path('favicon.ico', RedirectView.as_view(url='/static/img/favicon.svg', permanent=True)),
    path('admin/', admin.site.urls),
    path('', include('user.urls')),
    path('home/', include('Home.urls')),
    path('games/', include('Game.urls')),
    path('messenger/', include('Messenger.urls')),
    path('app/', include('programapp_module.urls')),
    path('blog/', include('blog.urls')),
    path('language/', include('language.urls')),
    path('contact_us/', include('ContactUs.urls')),
    path('academy/' , include('language_academy.urls')),
    path('academy/manage/', include('language_academy.admin_cms.urls')),
    path('economy/', include('economy.urls')),
    path('shop/', include('shop.urls')),
    path('panel/', include('panel.urls')),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
