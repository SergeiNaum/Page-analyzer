import psycopg2
from psycopg2.extensions import connection
from psycopg2.extras import NamedTupleCursor

from datetime import datetime
from collections import namedtuple
from polog import log

from typing import NamedTuple, List



@log
def get_connection(db_url):
    return psycopg2.connect(db_url)


@log
def close_connection(conn):
    if conn:
        conn.close()


@log
def add_url(conn: connection, url_name: str) -> NamedTuple:
    with conn.cursor(cursor_factory=NamedTupleCursor) as cur:
        try:
            cur.execute(
                'INSERT INTO urls (name, created_at) VALUES (%s, %s) RETURNING id;',
                (url_name, datetime.now())
            )
            id = cur.fetchone()
            conn.commit()

            return id.id
        except psycopg2.DatabaseError as e:
            raise Exception('An error occurred while adding the URL') from e


@log
def create_url_check(conn: connection, url, status_code: int, tags_data: dict):
    with conn.cursor(cursor_factory=NamedTupleCursor) as cur:
        try:
            cur.execute(
                '''INSERT INTO url_checks
                (url_id, status_code, h1, title, description, created_at)
                VALUES (%s, %s, %s, %s, %s, %s);''',
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
        except psycopg2.DatabaseError as e:
            raise Exception('An error occurred while creating URL check !') from e


@log
def get_url_by_url_name(conn: connection, url_name: str) -> NamedTuple:
    with conn:
        with conn.cursor(cursor_factory=NamedTupleCursor) as cur:
            try:
                cur.execute('SELECT * FROM urls WHERE name = %s LIMIT 1;', (url_name,), )
                url = cur.fetchone()

                return url

            except psycopg2.DatabaseError as e:
                raise Exception('An error occurred while getting URL by URL name !') from e


@log
def get_urls_and_last_checks_data(conn: connection) -> List[NamedTuple]:
    with conn:
        with conn.cursor(cursor_factory=NamedTupleCursor) as cur:
            try:

                cur.execute(
                    'SELECT DISTINCT ON (urls.id) id, name FROM urls;'
                )
                data_urls = cur.fetchall()
                cur.execute(
                    '''SELECT DISTINCT ON (url_checks.url_id) url_id, status_code, created_at
                    FROM url_checks;'''
                )
                url_checks = cur.fetchall()
                urls_dict = {url.id: url for url in data_urls}
                record = namedtuple('Record', ['id', 'name', 'status_code', 'created_at'])

                data = []

                for check in url_checks:
                    url = urls_dict.get(check.url_id)
                    if url:
                        data.append(record(url.id, url.name, check.status_code, check.created_at))
                data = sorted(data, key=lambda rec: (rec.id, rec.created_at), reverse=True)

                return data

            except psycopg2.DatabaseError as e:
                raise Exception('An error occurred while getting URLs & last checks !') from e


@log
def get_url_by_id(conn: connection, url_id) -> NamedTuple:
    with conn:
        with conn.cursor(cursor_factory=NamedTupleCursor) as cur:
            try:
                cur.execute('SELECT * FROM urls WHERE id = %s LIMIT 1;', (url_id,), )
                url = cur.fetchone()

                return url

            except psycopg2.DatabaseError as e:
                raise Exception('An error occurred while getting URL by ID !') from e


@log
def get_url_checks_by_url_id(conn: connection, url_id) -> NamedTuple:
    with conn:
        with conn.cursor(cursor_factory=NamedTupleCursor) as cur:
            try:
                cur.execute('''SELECT *
                        FROM url_checks
                        WHERE url_id = %s
                        ORDER BY id DESC;''', (url_id,), )
                url_checks = cur.fetchall()
                return url_checks

            except psycopg2.DatabaseError as e:
                raise Exception('An error occurred while getting URL checks by URL ID!') from e
