import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Read configurations safely from .env or environment variables
try:
    from decouple import config, Csv
    SECRET_KEY = config('SECRET_KEY', default='django-insecure-iru+2z!%3=aw8jq2odmi(==&4k4a&@l*le6jq^u))9au=1v6p*')
    DEBUG = config('DEBUG', default=False, cast=bool)
    ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,.vercel.app,.now.sh,*', cast=Csv())
    DATABASE_URL = config('DATABASE_URL', default='')
    VERCEL_URL = config('VERCEL_URL', default='')
except ImportError:
    env_vars = {}
    env_file = BASE_DIR / '.env'
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    env_vars[k.strip()] = v.strip().strip('\'"')
    SECRET_KEY = env_vars.get('SECRET_KEY', os.environ.get('SECRET_KEY', 'django-insecure-default-key'))
    DEBUG = env_vars.get('DEBUG', os.environ.get('DEBUG', 'False')).lower() in ('true', '1', 'yes')
    hosts_str = env_vars.get('ALLOWED_HOSTS', os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1,.vercel.app,.now.sh,*'))
    ALLOWED_HOSTS = [h.strip() for h in hosts_str.split(',') if h.strip()]
    DATABASE_URL = env_vars.get('DATABASE_URL', os.environ.get('DATABASE_URL', ''))
    VERCEL_URL = env_vars.get('VERCEL_URL', os.environ.get('VERCEL_URL', ''))


# ============================================================
# CSRF TRUSTED ORIGINS — Required for Vercel login to work!
# ============================================================
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'https://*.vercel.app',
    'https://*.now.sh',
]

# Add the specific Vercel project URL if set
if VERCEL_URL:
    if not VERCEL_URL.startswith('http'):
        VERCEL_URL = 'https://' + VERCEL_URL
    CSRF_TRUSTED_ORIGINS.append(VERCEL_URL)

# Also read CSRF from env for custom domains
_extra_origins = os.environ.get('CSRF_TRUSTED_ORIGINS', '')
if _extra_origins:
    CSRF_TRUSTED_ORIGINS += [o.strip() for o in _extra_origins.split(',') if o.strip()]


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # PESO Core App
    'peso.apps.PesoConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # Whitenoise: serve static files on Vercel/production (must be AFTER SecurityMiddleware)
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'peso_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'peso.context_processors.peso_global_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'peso_project.wsgi.application'


# ============================================================
# DATABASE — Supabase PostgreSQL via Session Pooler
# ============================================================
try:
    import dj_database_url
    if DATABASE_URL:
        DATABASES = {
            'default': dj_database_url.parse(
                DATABASE_URL,
                conn_max_age=0,        # Vercel is serverless — no persistent connections
                ssl_require=True,
            )
        }
    else:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': BASE_DIR / 'db.sqlite3',
            }
        }
except ImportError:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# ============================================================
# SESSION — Use database-backed sessions (works on serverless)
# ============================================================
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 86400 * 7           # 7 days
SESSION_COOKIE_SECURE = not DEBUG         # True on HTTPS (Vercel), False on local
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# CSRF cookie settings for Vercel
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_HTTPONLY = False              # Must be False for JS to read it if needed
CSRF_COOKIE_SAMESITE = 'Lax'


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Manila'
USE_I18N = True
USE_TZ = True


# ============================================================
# STATIC FILES — Whitenoise for Vercel / Production
# ============================================================
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Whitenoise compressed static files
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Auth URLs
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = 'login'

# Security headers for production
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
