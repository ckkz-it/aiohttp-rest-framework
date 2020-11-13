import os

from dotenv import load_dotenv

load_dotenv()

db = {
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_DATABASE"),
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT", 5432)),
    # db to which you can login and create other (test) databases
    "default_database": os.getenv("DB_DEFAULT_DATABASE", "postgres")
}
url_template = "postgresql://{user}:{password}@{host}:{port}/{database}"
db_url = url_template.format(**db)
