from .base import *

DEBUG = True
ALLOWED_HOSTS = env.list('DJANGO_ALLOWED_HOSTS')


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': env('DATABASE_NAME'),
        'USER': env('DATABASE_USER'),
        'PASSWORD': env('DATABASE_PASSWORD'),
        'HOST': env('DATABASE_HOST'),
        'PORT': env('DATABASE_PORT'),
        'OPTIONS': {"charset": "utf8mb4",'init_command': "SET sql_mode='STRICT_TRANS_TABLES'"},
    }
}
