import os
from .base import *


environment = os.environ.get('ENVIRONMENT_TYPE')


if environment == 'development':
    from .development import *
elif environment == 'production':
    from .production import *
