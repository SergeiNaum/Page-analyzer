from datetime import datetime
from typing import NamedTuple

from psycopg2.extras import NamedTupleCursor


def add_url(conn, url_name):
    with conn:
        with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
            curs.execute('INSERT INTO urls (name, created_at) VALUES (%s, %s) RETURNING id;',
                         (url_name, datetime.now()), )
            id = curs.fetchone()
            conn.commit()

    return id


def create_url_check(conn, url, status_code, tags_data):
    with conn:
        with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
            curs.execute(
                'INSERT INTO url_checks\
                (url_id, status_code, h1, title, description, created_at)\
                VALUES (%s, %s, %s, %s, %s, %s);',
                (
                    url.id,
                    status_code,
                    tags_data['h1'],
                    tags_data['title'],
                    tags_data['description'],
                    datetime.now(),
                ),
            )
            conn.commit()


def get_url_by_url_name(conn, url_name: str) -> NamedTuple:
    with conn:
        with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
            curs.execute('SELECT * FROM urls WHERE name = %s LIMIT 1;', (url_name,), )
            url = curs.fetchone()

    return url


def get_urls_and_last_checks_data(conn):
    with conn:
        with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
            curs.execute('SELECT DISTINCT ON (urls.id)\
                    urls.id,\
                    urls.name,\
                    url_checks.status_code,\
                    url_checks.created_at\
                FROM urls\
                LEFT JOIN url_checks\
                ON urls.id = url_checks.url_id\
                ORDER BY urls.id DESC, url_checks.created_at DESC;')
            data = curs.fetchall()

    return data


def get_url_by_id(conn, url_id):
    with conn:
        with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
            curs.execute('SELECT * FROM urls WHERE id = %s LIMIT 1;', (url_id,), )
            url = curs.fetchone()

    return url


def get_url_checks_by_url_id(conn, url_id):
    with conn:
        with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
            curs.execute('SELECT *\
                FROM url_checks\
                WHERE url_id = %s\
                ORDER BY id DESC;', (url_id,), )
            url_checks = curs.fetchall()

    return url_checks
