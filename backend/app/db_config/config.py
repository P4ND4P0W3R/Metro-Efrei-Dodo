from tortoise import Tortoise
from tortoise.contrib.fastapi import register_tortoise
from dotenv import load_dotenv
import os

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

TORTOISE_ORM = {
    "connections": {
        "default": DATABASE_URL,
    },
    "apps": {
        "models": {
            "models": ["db_config.models", "aerospike"],
            "default_connection": "default",
        },
    },
    "use_tz": False,
    "timezone": "Europe/Paris",
}

# Function to register TortoiseORM with FastAPI
def register_tortoise_orm(app, config):
    register_tortoise(
        app=app,  # Pass the FastAPI app instance here
        db_url=config["connections"]["default"],
        modules={"models": ["db_config.models"]},
        generate_schemas=True,
        add_exception_handlers=True,
    )