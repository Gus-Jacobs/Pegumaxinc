from django.apps import AppConfig


class MainSiteConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main_site'

    def ready(self):
        import main_site.signals # noqa