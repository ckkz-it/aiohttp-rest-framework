import os

from dotenv import load_dotenv

load_dotenv()

db = {
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_DATABASE"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "default_database": os.getenv("DB_DEFAULT_DATABASE", "postgres")
}

postgres_url = "postgresql://{user}:{password}@{host}:{port}/{database}".format(**db)
