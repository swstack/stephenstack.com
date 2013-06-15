import os

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))

PROJECT_ROOT = os.path.join(ROOT, "src")

HTTP_STATIC = os.path.join(PROJECT_ROOT, "view", "static")

HTTP_TEMPLATES = os.path.join(PROJECT_ROOT, "view", "templates")

STORE_DIR = os.path.join(ROOT, "store")
