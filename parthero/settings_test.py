from parthero.settings import *

DEBUG = False
SECRET_KEY = "test-secret-key"
ALLOWED_HOSTS = ["*"]

# Keep side-effects local/in-memory
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

# Test client / RequestFactory hosts
CSRF_TRUSTED_ORIGINS = ["http://testserver", "http://localhost"]


# import everything from your main settings

# Point Django at your Docker PostgreSQL
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "parthero",
        "USER": "parthero",
        "PASSWORD": "password",
        "HOST": "localhost",
        "PORT": "5432",
        "TEST": {
            "NAME": "parthero_test",
        },
    }
}
