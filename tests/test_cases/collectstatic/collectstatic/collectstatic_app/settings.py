from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# SECRET_KEY = os.environ.get('SECRET_KEY', get_random_secret_key())

STATIC_ROOT = BASE_DIR / "staticfiles"
