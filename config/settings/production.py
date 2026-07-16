import os
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

from .base import *

SECRET_KEY = os.environ['DJANGO_SECRET_KEY']
DEBUG = False
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '.vercel.app').split(',')

tmp = urlparse(os.environ['DATABASE_URL'])
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': tmp.path.replace('/', ''),
        'USER': tmp.username,
        'PASSWORD': tmp.password,
        'HOST': tmp.hostname,
        'PORT': tmp.port or 5432,
    }
}

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
