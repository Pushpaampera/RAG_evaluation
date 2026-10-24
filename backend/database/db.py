import os

import psycopg
from dotenv import load_dotenv
from psycopg import Connection
from psycopg.conninfo import make_conninfo

load_dotenv()


def get_connection() -> Connection:
    """
    Create and return a PostgreSQL connection.

    Connection details are loaded from environment variables.
    """

    required_variables = [
        "DATABASE_HOST",
        "DATABASE_PORT",
        "DATABASE_NAME",
        "DATABASE_USER",
        "DATABASE_PASSWORD",
    ]

    missing_variables = [
        name
        for name in required_variables
        if not os.getenv(name)
    ]

    if missing_variables:
        raise RuntimeError(
            "Missing database configuration: "
            + ", ".join(missing_variables)
        )

    connection_string = make_conninfo(
        host=os.environ["DATABASE_HOST"],
        port=int(os.environ["DATABASE_PORT"]),
        dbname=os.environ["DATABASE_NAME"],
        user=os.environ["DATABASE_USER"],
        password=os.environ["DATABASE_PASSWORD"],
        connect_timeout=5,
    )

    return psycopg.connect(connection_string)