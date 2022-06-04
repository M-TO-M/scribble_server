import os
from dotenv import load_dotenv

from pathlib import Path


load_dotenv()

NAVER_API_CLIENT_ID = os.environ.get('NAVER_API_CLIENT_ID')
NAVER_API_CLIENT_SECRET = os.environ.get('NAVER_API_CLIENT_SECRET')

SECRET_KEY = os.environ.get('SECRET_KEY')

RUN_ENV = os.environ.get('RUN_ENV')
DEV_ALLOWED_HOSTS = os.environ.get('EC2_DNS')

BASE_DIR = Path(__file__).resolve().parent.parent.parent
