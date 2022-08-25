import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'findme.settings')

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    # 'websocket': AllowedHostsOriginValidator(
    #     AuthMiddlewareStack(
    #         URLRouter(
    #             routings.websocket_urlpatterns
    #         )
    #     )
    # )
})
