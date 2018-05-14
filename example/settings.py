# encoding: utf-8
from __future__ import absolute_import, unicode_literals
"""
Django settings for example project.

Generated by 'django-admin startproject' using Django 1.11.12.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

import os

from kombu import Queue, Exchange

from core.celery_annotations import celery_annotations_dict
from . import local_settings as ls
from .local_settings import *  # NOQA

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# SECRET_KEY = 'change the SECRET_KEY'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'import_export',
    'apiview',
    'apps.isv',
    'apps.corp',
]
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apiview.middlewares.RequestCompatMiddleware',
    'core.middlewares.AccessControlAllowOriginMiddleware',
]

SESSION_ENGINE = "redis_sessions.session"

SESSION_REDIS = {
    'host': ls.REDIS_HOST,
    'port': ls.REDIS_PORT,
    'db': ls.REDIS_SESSION_DB,
    'password': ls.REDIS_PASSWORD,
    'prefix': 'session',
    'socket_timeout': 1
}

REDIS_DINGTALK_URL = 'redis://%s%s@%s:%s/%d' % (
    ':' if ls.REDIS_PASSWORD else '',
    ls.REDIS_PASSWORD,
    ls.REDIS_HOST,
    ls.REDIS_PORT,
    ls.REDIS_DINGTALK_DB)

CACHES = {
    'default': {
        'BACKEND': 'redis_cache.RedisCache',
        'LOCATION': [
            '%s:%s' % (ls.REDIS_HOST, ls.REDIS_PORT),
        ],
        'OPTIONS': {
            'DB': ls.REDIS_CACHE_DB,
            'PASSWORD': ls.REDIS_PASSWORD,
            'PARSER_CLASS': 'redis.connection.HiredisParser',
            'CONNECTION_POOL_CLASS': 'redis.BlockingConnectionPool',
            'CONNECTION_POOL_CLASS_KWARGS': {
                'max_connections': 50,
                'timeout': 20,
            },
            'MAX_CONNECTIONS': 1000,
            'PICKLE_VERSION': -1,
        },
    },
}

DATE_FORMAT = '%Y-%m-%d'
TIME_FORMAT = '%H:%M:%S'
DATETIME_FORMAT = DATE_FORMAT + ' ' + TIME_FORMAT

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.JSONParser',
        'core.parsers.RawParser',

    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'apiview.renderers.JSONPRenderer',
    ],
    'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.AllowAny',),
    'DATETIME_FORMAT': DATETIME_FORMAT,
    'TIME_FORMAT': TIME_FORMAT,
    'DATE_FORMAT': DATE_FORMAT,
}

if DEBUG:
    REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'].append('apiview.renderers.BrowsableAPIRenderer')

ROOT_URLCONF = 'example.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates'), ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.static',
            ],
        },
    },
]

WSGI_APPLICATION = 'example.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': ls.MYSQL_DBNAME,
        'USER': ls.MYSQL_USERNAME,
        'PASSWORD': ls.MYSQL_PASSWORD,
        'HOST': ls.MYSQL_HOST,
        'PORT': ls.MYSQL_PORT,
        'TEST_CHARSET': "utf8mb4",
        'TEST_COLLATION': "utf8mb4_unicode_ci",
        'STORAGE_ENGINE': 'INNODB',
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}


# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

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

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'apps.isv.backend.ISVBackend',
)
# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'zh-hans'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = True

USE_TZ = True

KILL_CSRF = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_URL = '/static/'

MEDIA_URL = '/dj/'
STATIC_ROOT = os.path.join(BASE_DIR, 'www_static')

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'django.contrib.staticfiles.finders.FileSystemFinder',
)

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static/'),
)

DEFAULT_FILE_STORAGE = 'core.storage.EnableUrlFileSystemStorage'

# celery settings

CELERY_BROKER_URL = 'redis://%s%s@%s:%s/%d' % (
    ':' if ls.REDIS_PASSWORD else '',
    ls.REDIS_PASSWORD,
    ls.REDIS_HOST,
    ls.REDIS_PORT,
    ls.REDIS_CELERY_DB)

CELERY_RESULT_BACKEND = CELERY_BROKER_URL

CELERY_WORKER_HIJACK_ROOT_LOGGER = False

# 任务执行最长时间20分钟
CELERY_TASK_SOFT_TIME_LIMIT = 1200
CELERY_TASK_TIME_LIMIT = 1200

CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_DEFAULT_QUEUE = 'default'

CELERY_TASK_SERIALIZER = 'pickle'
CELERY_RESULT_SERIALIZER = 'pickle'
CELERY_ACCEPT_CONTENT = ['pickle', 'json']

# 定义执行队列
CELERY_TASK_QUEUES = (
    Queue('default', Exchange('default'), routing_key='default'),
    Queue('crontab', Exchange('crontab'), routing_key='crontab'),
    Queue('async', Exchange('async'), routing_key='async')
)

# 制定特定任务路由到特定执行队列
CELERY_TASK_ROUTES = {
    'example.celery._async_call': {'queue': 'async', 'routing_key': 'async'},
}

CELERY_TASK_ANNOTATIONS = {'*': celery_annotations_dict}

# celery settings end

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': '[%(asctime)s.%(msecs)d] %(levelname)s [%(module)s:%(funcName)s:%(lineno)d]- %(message)s',
            'datefmt': "%y/%m/%d %H:%M:%S",
        },
    },
    'filters': {
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
            'formatter': 'standard'
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['console', 'mail_admins', ],
            'level': 'ERROR',
            'propagate': False,
        },
        'exception': {
            'handlers': ['console', 'mail_admins'],
            'level': 'ERROR',
            'propagate': False
        },
        'apiview': {
            'handlers': ['console', ],
            'level': 'DEBUG',
            'propagate': False,
        },
        'dingtalk': {
            'handlers': ['console', ],
            'level': 'DEBUG',
            'propagate': False,
        }
    },
    'root': {
        'handlers': ['console', ],
        'level': 'INFO',
        'propagate': True
    }
}

ERROR_CODE_DEFINE = (
    ('ERR_AUTH_NOLOGIN',            10001,  '请先登陆'),
    ('ERR_AUTH_NOTFOUND',           10002,  '用户名密码错误'),
    ('ERR_AUTH_PERMISSION',         10003,  '权限错误'),

    ('ERR_PAGE_SIZE',               11001,  '页码错误'),

    ('ERR_VCODE_INVALID',           12001,  '验证码无效'),
    ('ERR_VCODE_MAX_TIMES',         12002,  '验证码验证次数超限'),
    ('ERR_VCODE_EXPIRE',            12003,  '请重新获取验证码'),
    ('ERR_VCODE_WAIT',              12004,  '获取验证码频繁'),
    ('ERR_VCODE_MOBILE_COUNT',      12005,  '该手机号今日获取次数超限'),
    ('ERR_VCODE_SEND_FAIL',         12006,  '验证码发送失败'),
)
