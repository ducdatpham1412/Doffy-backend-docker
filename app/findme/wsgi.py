import os
from django.core.wsgi import get_wsgi_application
# import eventlet
# import eventlet.wsgi
# import socketio
# from chat.socket_io.views import sio
# import environ

# ENVIRON
# env = environ.Env()
# environ.Env().read_env()


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'findme.settings')

application = get_wsgi_application()

# application = socketio.WSGIApp(sio, get_wsgi_application())

# eventlet.wsgi.server(eventlet.listen(
#     ('', int(env('SOCKET_PORT')))), application)
