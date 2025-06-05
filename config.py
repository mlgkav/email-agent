from dotenv import load_dotenv
import logging
import os
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)5s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

def get_env_var(name):
    value = os.environ.get(name)
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value

OPENAI_CLIENT = OpenAI(api_key=get_env_var("OPENAI_API_KEY"))

STORE_NAME = "emails"