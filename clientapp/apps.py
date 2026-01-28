from django.apps import AppConfig


class ClientappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'clientapp'

    def ready(self):
        import clientapp.storefront_signals
        import clientapp.signals  # Auto-audit signals for product changes

