from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users'
    def ready(self):
        """
        Import signals when app is ready.
        
        This ensures all signal handlers are registered
        before any database operations occur.
        """
        import apps.users.signals