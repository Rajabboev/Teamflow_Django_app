"""
Django production settings for teamflow project.
Imports base and overrides for production (DEBUG=False, security, static/media).
"""
from decouple import config, Csv

from .base import *

DEBUG = False

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost', cast=Csv())

# Security
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Static and media (WhiteNoise serves static; media usually from CDN or separate storage)
STATIC_URL = config('STATIC_URL', default='/static/')
STATIC_ROOT = BASE_DIR / config('STATIC_ROOT', default='staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = config('MEDIA_URL', default='/media/')
MEDIA_ROOT = BASE_DIR / config('MEDIA_ROOT', default='media')
