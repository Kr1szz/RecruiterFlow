"""Small Psycopg 3 connection boundary; all application SQL is handwritten."""

import os
from collections.abc import Iterator
from contextlib import contextmanager

import psycopg


def database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/recruiter_bot",
    )


@contextmanager
def get_connection() -> Iterator[psycopg.Connection]:
    with psycopg.connect(database_url(), row_factory=psycopg.rows.dict_row) as connection:
        yield connection

