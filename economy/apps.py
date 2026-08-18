from django.apps import AppConfig


class EconomyConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'economy'
    verbose_name = 'اقتصاد'

    def ready(self):
        import economy.signals
