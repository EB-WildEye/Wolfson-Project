"""Centralized config — reads from AWS Secrets Manager (prod) or env vars (dev).

In Lambda, secrets come from Secrets Manager with in-memory caching.
Locally (ENV=dev), secrets fall back to environment variables / .env files.
"""

import os
import json
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Internal cache for Secrets Manager values
# ---------------------------------------------------------------------------
_secrets_cache: dict[str, str] = {}


def _fetch_secret(secret_name: str) -> str:
    """Fetch a secret from AWS Secrets Manager with in-memory caching.

    In production the Lambda's IAM role grants access to these secrets.
    Locally (ENV=dev) this function is never called — we fall back to env vars.
    """
    if secret_name in _secrets_cache:
        return _secrets_cache[secret_name]

    import boto3  # lazy — boto3 is pre-installed in Lambda
    from botocore.exceptions import ClientError

    client = boto3.client("secretsmanager")
    try:
        response = client.get_secret_value(SecretId=secret_name)
        value = response["SecretString"]
        _secrets_cache[secret_name] = value
        logger.info("Fetched secret: %s", secret_name)
        return value
    except ClientError as e:
        logger.error("Failed to fetch secret %s: %s", secret_name, e)
        raise


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def get_setting(name: str, default: str = "") -> str:
    """Read an environment variable with an optional fallback."""
    return os.environ.get(name, default)


def get_mongo_uri() -> str:
    """Return the MongoDB connection URI (session store — not RAG).

    - **prod**: fetches from Secrets Manager ``/gali/MONGO_URI``
    - **dev** : reads ``MONGO_URI`` env var
    """
    if get_setting("ENV", "dev") == "prod":
        raw = _fetch_secret("/gali/MONGO_URI")
        try:
            return json.loads(raw).get("uri", raw)
        except (json.JSONDecodeError, AttributeError):
            return raw
    return get_setting("MONGO_URI", "mongodb://localhost:27017")


def get_gemini_key() -> str:
    """Return the Gemini API key.

    - **prod**: fetches from Secrets Manager ``/gali/GEMINI_API_KEY``
    - **dev** : reads ``GEMINI_API_KEY`` env var
    """
    if get_setting("ENV", "dev") == "prod":
        raw = _fetch_secret("/gali/GEMINI_API_KEY")
        try:
            return json.loads(raw).get("key", raw)
        except (json.JSONDecodeError, AttributeError):
            return raw
    return get_setting("GEMINI_API_KEY", "")
