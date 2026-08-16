import os
from dotenv import load_dotenv

load_dotenv()  # loads variables from .env into the environment

DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. Copy .env.example to .env and fill in your "
        "cloud database connection string."
    )
