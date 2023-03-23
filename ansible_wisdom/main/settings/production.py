import os
from typing import Literal

from .base import *  # NOQA

DEBUG = False

ANSIBLE_AI_MODEL_MESH_HOST = os.environ["ANSIBLE_AI_MODEL_MESH_HOST"]
ANSIBLE_AI_MODEL_MESH_INFERENCE_PORT = os.environ["ANSIBLE_AI_MODEL_MESH_INFERENCE_PORT"]

# For wildcard, use a "." prefix.
# Example: .wisdom.ansible.com

ANSIBLE_AI_MODEL_MESH_INFERENCE_URL = (
    f"{ANSIBLE_AI_MODEL_MESH_HOST}:{ANSIBLE_AI_MODEL_MESH_INFERENCE_PORT}"
)

SECRET_KEY = os.environ["SECRET_KEY"]

ALLOWED_HOSTS = list(filter(len, os.getenv("ANSIBLE_WISDOM_DOMAIN", "").split(",")))

ANSIBLE_AI_MODEL_MESH_API_TYPE: Literal["grpc", "http", "mock"] = os.getenv(
    "ANSIBLE_AI_MODEL_MESH_API_TYPE", "http"
)
SOCIAL_AUTH_REDIRECT_IS_HTTPS = True

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"
CACHES = {
    "default": {
        # In production, we use a Redis in Cluster mode. The consequence is that
        # we cannot use the standard driver and we need instead to use Redis-Py's
        # new RedisCluster client. This is what main.redis.CustomRedisCluster is
        # for.
        "BACKEND": "main.redis.CustomRedisCluster",
        # NOTE: Use ',' to seperate the different servers
        "LOCATION": os.environ["ANSIBLE_AI_CACHE_URI"],
    }
}

REDIS_URL = CACHES["default"]["LOCATION"]  # for Redis health-check
