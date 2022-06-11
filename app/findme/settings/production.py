import environ
from datetime import timedelta

# ENVIRON
PROJECT_ROOT = environ.Path(__file__) - 2
PROJECT_ROOT.file('.env.production')
env = environ.Env()
env.read_env(PROJECT_ROOT('.env.production'))


SECRET_KEY = env('SECRET_KEY')


DEBUG = False


ALLOWED_HOSTS = ['localhost', 'www.doffy.xyz', '45.119.81.54', 'app']

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO"},
    },
}


EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_PASSWORD')

AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME')
AWS_IMAGE_URL = env('AWS_IMAGE_URL')


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'USER': env('DATABASE_USER'),
        'PASSWORD': env('DATABASE_PASSWORD'),
        'HOST': env('DATABASE_HOST'),
        'PORT': env('DATABASE_PORT'),
        'NAME': env('DATABASE_NAME'),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4'
        }
    }
}

MONGO_USER = env('MONGO_USER')
MONGO_PASSWORD = env('MONGO_PASSWORD')
MONGO_HOST = env('MONGO_HOST')


SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=5),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=100),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,

    'AUTH_HEADER_TYPES': ('Bearer', 'Token', ),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',

    'JTI_CLAIM': 'jti',

    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(days=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=100),
}

ONESIGNAL_API_KEY = env('ONESIGNAL_API_KEY')
ONESIGNAL_APP_ID = env('ONESIGNAL_APP_ID')

FACEBOOK_APP_ID = env('FACEBOOK_APP_ID')
FACEBOOK_APP_SECRET = env('FACEBOOK_APP_SECRET')

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = env('SOCIAL_AUTH_GOOGLE_OAUTH2_KEY')
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = env('SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET')
