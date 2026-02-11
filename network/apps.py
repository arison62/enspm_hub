from django.apps import AppConfig


class NetworkConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'network'

    def ready(self):
        from .listeners.chat_listener import ChatEventListener
        ChatEventListener.register_handlers()
