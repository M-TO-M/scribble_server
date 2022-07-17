import os
import json
from dotenv import load_dotenv

from pathlib import Path


load_dotenv()

NAVER_API_CLIENT_ID = os.environ.get('NAVER_API_CLIENT_ID')
NAVER_API_CLIENT_SECRET = os.environ.get('NAVER_API_CLIENT_SECRET')

SECRET_KEY = os.environ.get('SECRET_KEY')

RUN_ENV = os.environ.get('RUN_ENV')

HOST_KEY = 'DEV_ALLOWED_HOSTS' if RUN_ENV == 'dev' else 'PROD_ALLOWED_HOSTS'
ALLOWED_HOSTS = json.loads(os.environ.get(HOST_KEY))

BASE_DIR = Path(__file__).resolve().parent.parent.parent

DB_NAME = os.environ.get('DB_NAME')
DB_USER = os.environ.get('DB_USER')
DB_HOST = os.environ.get('DB_HOST')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
