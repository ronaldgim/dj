"""
Django settings for gimpromed project.

Generated by 'django-admin startproject' using Django 3.2.13.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""
import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-$xt9tf@7)u9ic)=6!1rko=7-jlq2k%b2b%ixbm#wqpic1crvh3'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # API
    'rest_framework',
    'rest_framework.authtoken',
    
    # JWT
    # 'rest_framework_simplejwt',
    
    # Django Celery Results
    'django_celery_results',
    
    # My apps
    'users',
    'datos',
    'carta',
    'mantenimiento',
    'etiquetado',
    'inventario',
    'bpa',
    'compras_publicas',
    'regulatorio_legal',
    'ventas',

    # WMS
    'wms'
]

X_FRAME_OPTIONS = 'SAMEORIGIN'

REST_FRAMEWORK = {

    # JWT
    # 'DEFAULT_AUTHENTICATION_CLASSES': (
    #     'rest_framework_simplejwt.authentication.JWTAuthentication',
    # ),
    
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    
}


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Asegúrate de tener configurado esto
CSRF_TRUSTED_ORIGINS = [
    'http://127.0.0.1:8000',   # Desarrollo
    'http://172.16.28.17:8000', # .17
    'http://ems.gimpromed.com' #En producción
]

CSRF_COOKIE_SAMESITE = 'Lax'  # Esto asegura compatibilidad con cookies
CSRF_COOKIE_SECURE = False    # Cambia a True en producción con HTTPS

ROOT_URLCONF = 'gimpromed.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
                    os.path.join(BASE_DIR, 'templates')
            ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'gimpromed.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    # 'default': {
    #     'ENGINE': 'django.db.backends.sqlite3',
    #     'NAME': BASE_DIR / 'db.sqlite3',
    # },
    
    # base de datos sql  
    'default':{
        'ENGINE': 'django.db.backends.mysql',
        'NAME':'gim_web',
        'PASSWORD':'gimpromed',
        'USER':'standard',
        'HOST':'172.16.28.102',
    },
    
    # base de datos alterna a MBA  
    'gimpromed_sql':{
        'ENGINE': 'django.db.backends.mysql',
        'NAME':'warehouse',
        'PASSWORD':'gimpromed',
        'USER':'standard',
        'HOST':'172.16.28.102',
    },

    # base de datos infimas
    'infimas_sql':{
        'ENGINE': 'django.db.backends.mysql',
        'NAME':'infimas_publicos',
        'PASSWORD':'gimpromed',
        'USER':'standard',
        'HOST':'172.16.28.102',
    },
    
    # base de datos infimas
    'procesos_sercop':{
        'ENGINE': 'django.db.backends.mysql',
        'NAME':'procesos_sercop',
        'PASSWORD':'gimpromed',
        'USER':'standard',
        'HOST':'172.16.28.102',
    },

    
    # etiquetado stock
    # 'etiquetado_stock':{
    #     'ENGINE': 'django.db.backends.sqlite3',
    #     'NAME': BASE_DIR / 'C:/Erik/Egares Gimpromed/Desktop/ReposiciónAndagoya/test_etiquetado',
    # },
}


# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# URL LOGIN
LOGIN_URL = '/users/login/'
LOGIN_REDIRECT_URL = 'inicio'
LOGOUT_REDIRECT_URL = LOGIN_URL

# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'es' #'en-us'

TIME_ZONE = 'America/Guayaquil' #'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = False #True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)


MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# GMAIL
# App name = gimpromed.web
# email: gimpromed.web@gmail.com
# contraseña: webgim2024/*
# autentication gmail: ejkv sofw saui vcfj 
EMAIL_BACKEND= 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'gimpromed.web@gmail.com'
EMAIL_HOST_PASSWORD = 'ejkv sofw saui vcfj'
EMAIL_USE_TLS = True


# CELERY
# Configuración de Celery
CELERY_TIMEZONE = 'America/Guayaquil'
# CELERY_TASK_TRACK_STARTED = True
# CELERY_TASK_TIME_LIMIT = 30 * 60

CELERY_BROKER_URL = 'redis://localhost:6379/0'  # URL del broker, en este caso Redis
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'  # Donde almacenar los resultados
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

CELERY_RESULT_BACKEND = 'django-db'
CELERY_CACHE_BACKEND = 'django-cache'

CELERY_CACHE_BACKEND = 'default'
# django setting.
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'my_cache_table',
    }
}

CELERY_TIMEZONE = 'America/Guayaquil' #'UTC'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60



# LAPTOP
# user: admin
# passoword: Gim2023anydesk

# SUPERUSER
# username: admin
# password: gimpromed2022

# GIT
# username = Erik Garces
# repositorio -> usuario = egarcesgim
# repositorio -> repo = gimpromed_web
# password repositorio = same as my laptop
# passphrase = django gimpromed app edgh