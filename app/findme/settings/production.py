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


ONESIGNAL_API_KEY = env('ONESIGNAL_API_KEY')
ONESIGNAL_APP_ID = env('ONESIGNAL_APP_ID')

FACEBOOK_APP_ID = env('FACEBOOK_APP_ID')
FACEBOOK_APP_SECRET = env('FACEBOOK_APP_SECRET')

IOS_GOOGLE_OAUTH2_CLIENT_ID = env('IOS_GOOGLE_OAUTH2_CLIENT_ID')
ANDROID_GOOGLE_OAUTH2_CLIENT_ID = env('ANDROID_GOOGLE_OAUTH2_CLIENT_ID')

SOCIAL_AUTH_APPLE_TEAM_ID = env('SOCIAL_AUTH_APPLE_TEAM_ID')
SOCIAL_AUTH_APPLE_KEY_ID = env('SOCIAL_AUTH_APPLE_KEY_ID')
SOCIAL_AUTH_APPLE_PRIVATE_KEY = env('SOCIAL_AUTH_APPLE_PRIVATE_KEY')
CLIENT_ID = env('CLIENT_ID')
