"""
Django settings for Riddle project.

Generated by 'django-admin startproject' using Django 1.9.1.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.9/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
from core.cache import config_client_redis_zhz, config_redis_ab_test
from core.utils import conf

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '+matthg$w)x_5#ax0uug(jdy0)@^5(a)%w6mr$bmbcsac-n7x4'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = conf.debug == 'True'

ALLOWED_HOSTS = [
    'nginx',
    '127.0.0.1',
    'localhost',
    'g.rapo.cc',
    '192.168.1.98',
    'n.rapo.cc',
    '202.112.237.65',
    '121.4.103.23',
    'app.cai-ta.plutus-cat.com',
    'app.guess-song.plutus-cat.com',
    'tapp.guess-song.plutus-cat.com',
]

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'account',
    'question',
    'finance',
    'baseconf',
    'event',
    'corsheaders',
    'task',
   # 'django_prometheus',
]

MIDDLEWARE = [
   # 'django_prometheus.middleware.PrometheusBeforeMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.ABTestMiddleWare',
   # 'django_prometheus.middleware.PrometheusAfterMiddleware',
]

ROOT_URLCONF = 'Riddle.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')]
        ,
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

WSGI_APPLICATION = 'Riddle.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django_prometheus.db.backends.postgresql',
        'NAME': conf.riddle_name,
        'USER': conf.riddle_user,
        'PASSWORD': conf.riddle_password,
        'HOST': conf.riddle_host,
        'PORT': conf.riddle_port,
    }
}

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': os.path.join(BASE_DIR, 'riddle.db'),
#     }
# }

# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

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

# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/

STATIC_URL = '/static/'

STATIC_ROOT = './static/'

STATIC_MEDIA = './static/'

CORS_ALLOW_CREDENTIALS = True
CORS_ORIGIN_WHITELIST = ("http://cai-ta.ecdn.plutus-cat.com", "https://cai-ta.ecdn.plutus-cat.com")
CORS_ALLOWED_ORIGINS = ["http://cai-ta.ecdn.plutus-cat.com",
                        "https://cai-ta.ecdn.plutus-cat.com"]

# init dependency
config_client_redis_zhz()
config_redis_ab_test()
