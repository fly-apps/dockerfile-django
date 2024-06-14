import os
import random
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def get_random_secret_key():
    """
    Generate a random secret key.
    """
    chars = "abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)"
    return "".join(random.SystemRandom().choice(chars) for _ in range(50))


SECRET_KEY = os.environ.get("SECRET_KEY", get_random_secret_key())

STATIC_ROOT = BASE_DIR / "staticfiles"
