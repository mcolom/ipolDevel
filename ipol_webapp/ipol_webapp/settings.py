"""
Django settings for ipol_webapp project.

Generated by 'django-admin startproject' using Django 1.8.5.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""


####################################
#     GENRAL SETTINGS AND VARS     #
####################################

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import sys
import socket
from django.conf import global_settings
import logging
from django.core.urlresolvers import reverse_lazy
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_DIR = os.path.normpath(os.path.join(BASE_DIR, '..'))
OUTER_DIR = os.path.normpath(os.path.join(PROJECT_DIR, '..'))
PACKAGE_ROOT = os.path.abspath(os.path.dirname(__file__))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 's=pr=j8@u!0fp@59*d&$a)rbr30sp1b-sg4e8a*aw_&sjz4cg0'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# memcache switch for Per-Site caching, INVALIDATION  BY TIMEOUT.
USE_MEMCACHED = False

hostname = socket.gethostname()
local_machines = ['JAKmacmini', 'joses-mbp', 'Joses-MacBook-Pro.local']
if hostname in local_machines:
	HOST = 'local'
	DEBUG = True
	# to serve staticfiles from STATIC_ROOT folder (pruebas)
	# #DEBUG = False
	TEMPLATEDEBUG = True
	DBHOST = 'localhost'
	DBUSER = ''
	DBPSSWD = ''
	ALLOWED_HOSTS = []
	HTTPS = False

elif hostname in ['ipol.im']:
	# PRO USA APACHE
	HOST = 'produccion'
	DEBUG = False
	TEMPLATEDEBUG = False
	DBHOST = 'localhost'
	DBUSER = ''
	DBPSSWD = ''
	HTTPS = False
	# permite modo debug False
	DOMAIN_NAME = 'localhost'
	ADMINS = (('JAK', 'josearrecio@gmail.com'))
	# dominio y subdominios , ojo por ip no funciona.
	ALLOWED_HOSTS = ['ipol.im']
	MANAGERS = ADMINS
	USE_MEMCACHED = True

else:
	print("ERROR: invalid hostname")





# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'apps.controlpanel',
    'django.contrib.humanize',
    'rest_framework',

)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)



ROOT_URLCONF = 'ipol_webapp.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
	        #os.path.join(BASE_DIR, 'templates'),
	        os.path.join(BASE_DIR, 'apps/controlpanel/templates'),
	        #os.path.join(BASE_DIR, 'vendor/allauth/templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
	        'debug': [
                TEMPLATEDEBUG,
            ]
        },
    },
]



WSGI_APPLICATION = 'ipol_webapp.wsgi.application'


#####################
#     MEMCACHED     #
#####################

if USE_MEMCACHED:
	CACHES = {
		'default': {
			'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
			'LOCATION': '127.0.0.1:11211',
		}
	}

	MIDDLEWARE_CLASSES = (
		'django.middleware.cache.UpdateCacheMiddleware',
		'django.contrib.sessions.middleware.SessionMiddleware',
		'django.middleware.locale.LocaleMiddleware',
		'django.middleware.common.CommonMiddleware',
		'django.middleware.csrf.CsrfViewMiddleware',
		'django.contrib.auth.middleware.AuthenticationMiddleware',
		'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
		'django.contrib.messages.middleware.MessageMiddleware',
		'django.middleware.clickjacking.XFrameOptionsMiddleware',
		'django.middleware.cache.FetchFromCacheMiddleware',
	)
	# cache settings
	CACHE_MIDDLEWARE_ALIAS = 'default'
	CACHE_MIDDLEWARE_SECONDS = 60 * 60 * 1  # 1h
	CACHE_MIDDLEWARE_KEY_PREFIX = "IPOLCPCACHE"
	# only anonymous requests (i.e., not those made by a logged-in user) will be cached.
	CACHE_MIDDLEWARE_ANONYMOUS_ONLY = True

########################
#       DATABASES      #
########################

# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases
# python manage.py createsuperuser
# ipolcpadmin
# josearrecio@gmail.com
# ipolazsxdc

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

#Postgtress
# DATABASES = {
# 	'default': {
# 		'ENGINE': 'django.db.backends.postgresql_psycopg2',
# 		# Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
# 		'NAME': 'ipolwebapp',  # Or path to database file if using sqlite3.
# 		'USER': DBUSER,
# 		'PASSWORD': DBPSSWD,
# 		'HOST': DBHOST,  # Empty for localhost through domain sockets or   127.0.0.1' for localhost through TCP.
# 		'PORT': '5432',  # Set to empty string for default.
# 	}
# }


########################
#         I18N         #
########################
# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


########################
#   MEDIA AND STATIC   #
########################

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/
# donde junto todos mis statics para hacer el edeploy mas facil
# debe estar fuera del proyecto
STATIC_ROOT = os.path.join(OUTER_DIR, 'IPOLWEBAPP_STATIC')
if not os.path.exists(STATIC_ROOT):
	os.makedirs(STATIC_ROOT)
	print("********* Directorio creado: " + str(STATIC_ROOT))
# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
	# Put strings here, like "/home/html/static" or "C:/www/django/static".
	# Always use forward slashes, even on Windows.
	# Don't forget to use absolute paths, not relative paths.
	os.path.join(BASE_DIR, 'apps/controlpanel/controlpanel_static/'),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
	'django.contrib.staticfiles.finders.FileSystemFinder',
	'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = os.path.normpath(os.path.join(OUTER_DIR, 'IPOLWEBAPP_MEDIA'))
if not os.path.exists(MEDIA_ROOT):
	os.makedirs(MEDIA_ROOT)
	print("********* Directorio creado: " + str(MEDIA_ROOT))
# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = '/media/'

#####################
#       LOGS        #
#####################
RUTALOG = os.path.normpath(os.path.join(BASE_DIR, 'logs/'))
if not os.path.exists(RUTALOG):
	os.makedirs(RUTALOG)
	print("********* Directorio creado: " + str(RUTALOG))

DJANGO_PW_LOG = RUTALOG + "/ipolwebapp.log"
DJANGO_PW_REQUEST_LOG = RUTALOG + "/ipolwebapp_request.log"
LOG_LEVEL = 'DEBUG'

# False si no quiero q los logs vayan al django request log y si al gunicorn access log
DISABLE_GUNICOR_LOGUER = False



LOGGING = {
	'version': 1,
	'disable_existing_loggers': DISABLE_GUNICOR_LOGUER,
	'formatters': {
		'standard': {
			'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
		},
	},
	'handlers': {

		'default': {
			'level': LOG_LEVEL,
			'class': 'logging.handlers.RotatingFileHandler',
			'filename': DJANGO_PW_LOG,
			'maxBytes': 1024 * 1024 * 5,  # 5 MB
			'backupCount': 5,
			'formatter': 'standard',
		},
		'request_handler': {
			'level': LOG_LEVEL,
			'class': 'logging.handlers.RotatingFileHandler',
			'filename': DJANGO_PW_REQUEST_LOG,
			'maxBytes': 1024 * 1024 * 5,  # 5 MB
			'backupCount': 5,
			'formatter': 'standard',
		},
	},
	'root': {
		'handlers': ['default'],
		'level': LOG_LEVEL,
		'propagate': True
	},
	'loggers': {
		'django.request': {
			'handlers': ['request_handler'],
			'level': LOG_LEVEL,
			'propagate': False
		},
	}
}
#####################
#    REST WS        #
#####################

REST_FRAMEWORK = {
    'UNICODE_JSON': False
}

#####################
#       INFO        #
#####################

print("*************************** INFO SETTINGS *****************************")
print("********* " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " RUN AT : " + HOST + " *********")
print()
print('DEBUG:')
print(DEBUG)
print("BASE_DIR:")
print(BASE_DIR)
print("TEMPLATES:")
print(TEMPLATES)
print("PACKAGE_ROOT:")
print(PACKAGE_ROOT)
print('ALLOWED_HOSTS:')
print(ALLOWED_HOSTS)
print('TIME_ZONE:')
print(TIME_ZONE)
print('RUTA LOGS:')
print(RUTALOG)
print("DISABLE_GUNICOR_LOGUER:")
print(DISABLE_GUNICOR_LOGUER)
print("STATICFILES_DIRS:")
print(STATICFILES_DIRS)
print("MEDIA_ROOT:")
print(MEDIA_ROOT)
print("TEMPLATE_CONTEXT_PROCESSORS:")
print(global_settings.TEMPLATE_CONTEXT_PROCESSORS)
print("BASE_DIR:")
print(BASE_DIR)
print("STATIC_ROOT:")
print(STATIC_ROOT)
print("USE_MEMCACHED:")
print(USE_MEMCACHED)

print()
print("************************************************************************")