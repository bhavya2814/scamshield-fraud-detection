import os

# SQLALCHEMY_DATABASE_URI defines where Superset stores its own configuration, users, and dashboards.
# We point this to our PostgreSQL database to persist all Superset assets.
SQLALCHEMY_DATABASE_URI = os.getenv(
    "SQLALCHEMY_DATABASE_URI",
    "postgresql://scamuser:scampass@db:5432/scamshield"
)

# Secret key for encrypting connection secrets
SECRET_KEY = os.getenv("SUPERSET_SECRET_KEY", "scamshieldsecretkeyfortestingonly12345")

# Enable embedding features and dashboard features
FEATURE_FLAGS = {
    "EMBEDDED_SUPERSET": True,
    "ALERT_REPORTS": True,
}

# Filesystem Caching Configuration
CACHE_CONFIG = {
    "CACHE_TYPE": "FileSystemCache",
    "CACHE_DIR": "/tmp/superset_cache",
    "CACHE_DEFAULT_TIMEOUT": 300,
}

DATA_CACHE_CONFIG = {
    "CACHE_TYPE": "FileSystemCache",
    "CACHE_DIR": "/tmp/superset_data_cache",
    "CACHE_DEFAULT_TIMEOUT": 300,
}
