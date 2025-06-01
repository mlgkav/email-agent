"""Configuration utilities."""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def get_env_var(name: str, default: Optional[str] = None) -> str:
    """Get an environment variable.

    Args:
        name: The name of the environment variable
        default: Optional default value if the variable is not set

    Returns:
        str: The value of the environment variable

    Raises:
        ValueError: If the variable is not set and no default is provided
    """
    value = os.environ.get(name, default)
    if value is None:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def get_db_connection_string() -> str:
    """Get the database connection string from environment variables."""
    host = get_env_var("DB_HOST")
    port = get_env_var("DB_PORT", "5432")
    user = get_env_var("DB_USER")
    password = get_env_var("DB_PASSWORD")
    database = get_env_var("DB_NAME")

    return f"postgresql://{user}:{password}@{host}:{port}/{database}"
