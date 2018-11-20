from polyaxon.config_manager import config

DEBUG = config.is_debug_mode
POLYAXON_SERVICE = config.service
POLYAXON_ENVIRONMENT = config.env
K8S_NAMESPACE = config.namespace
K8S_NODE_NAME = config.node_name
K8S_GPU_RESOURCE_KEY = config.get_string('POLYAXON_K8S_GPU_RESOURCE_KEY')
CLUSTER_ID = config.cluster_id
REPOS_ARCHIVE_ROOT = '/tmp/archived_repos'
OUTPUTS_ARCHIVE_ROOT = '/tmp/archived_outputs'
OUTPUTS_DOWNLOAD_ROOT = '/tmp/download_outputs'
FILE_UPLOAD_PERMISSIONS = 0o644
ADMIN_VIEW_ENABLED = config.get_boolean('POLYAXON_ADMIN_VIEW_ENABLED',
                                        is_optional=True,
                                        default=False)
# Heartbeat timeout (status -> failed as zombie)
HEARTBEAT_TIMEOUT = config.get_int('POLYAXON_HEARTBEAT_TIMEOUT',
                                   is_optional=True,
                                   default=60 * 30)
# Token experiment time in days
TOKEN_EXPIRATION = config.get_int('POLYAXON_TOKEN_EXPIRATION',
                                  is_optional=True,
                                  default=30)

# Auditor backend
AUDITOR_BACKEND = config.get_string('POLYAXON_AUDITOR_BACKEND', is_optional=True)


def get_allowed_hosts():
    allowed_hosts = config.get_string('POLYAXON_ALLOWED_HOSTS',
                                      is_optional=True,
                                      is_list=True,
                                      default=['*'])
    allowed_hosts.append('.polyaxon.com')
    k8s_api_host = config.get_string('POLYAXON_K8S_API_HOST', is_optional=True)
    if k8s_api_host:
        allowed_hosts.append(k8s_api_host)

    return allowed_hosts


ALLOWED_HOSTS = get_allowed_hosts()

WSGI_APPLICATION = 'polyaxon.wsgi.application'
TIME_ZONE = config.get_string('POLYAXON_TIME_ZONE', is_optional=True) or 'Europe/Berlin'
LANGUAGE_CODE = 'en'
LANGUAGES = (
    ('en', u'English'),
)

USE_I18N = True
USE_L10N = True
USE_TZ = True

INTERNAL_IPS = ('127.0.0.1',)
APPEND_SLASH = True

ROOT_URLCONF = 'polyaxon.urls'
AUTH_USER_MODEL = 'db.User'

# user management
LOGIN_URL = '/users/login/'
LOGOUT_REDIRECT_URL = LOGIN_URL
LOGIN_REDIRECT_URL = '/'
ACCOUNT_ACTIVATION_DAYS = 7
INVITATION_TIMEOUT_DAYS = 30

SESSION_COOKIE_AGE = 24 * 60 * 60  # 24 hours
SESSION_COOKIE_HTTPONLY = True

DEFAULT_DB_ENGINE = 'django.db.backends.postgresql'
DATABASES = {
    'default': {
        'ENGINE': config.get_string('POLYAXON_DB_ENGINE', is_optional=True) or DEFAULT_DB_ENGINE,
        'NAME': config.get_string('POLYAXON_DB_NAME'),
        'USER': config.get_string('POLYAXON_DB_USER'),
        'PASSWORD': config.get_string('POLYAXON_DB_PASSWORD', is_secret=True),
        'HOST': config.get_string('POLYAXON_DB_HOST'),
        'PORT': config.get_string('POLYAXON_DB_PORT'),
        'ATOMIC_REQUESTS': True,
        'CONN_MAX_AGE': config.get_int('POLYAXON_DB_CONN_MAX_AGE', is_optional=True, default=0),
    }
}
