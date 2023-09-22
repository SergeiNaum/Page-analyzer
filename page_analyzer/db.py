from collections import namedtuple

import psycopg2

from datetime import datetime
from typing import NamedTuple, List
from psycopg2.extras import NamedTupleCursor
from dotenv import load_dotenv

from page_analyzer.app_config import DATABASE_URL


load_dotenv()


def get_connection(db_url):
    return psycopg2.connect(db_url)


def create_db_connection(database_url):
    def decorator(func):
        def wrapper(*args):
            db = get_connection(database_url)
            cur = db.cursor(cursor_factory=NamedTupleCursor)
            try:
                return func(*args, cur, db)
            except psycopg2.DatabaseError as e:
                print(f'Ошибка соединения с бд: \n {e}')
            finally:
                cur.close()
                db.close()
        return wrapper
    return decorator


@create_db_connection(DATABASE_URL)
def add_url(url_name: str, cur: psycopg2, db: psycopg2) -> NamedTuple:
    try:
        cur.execute(
            """INSERT INTO urls (name, created_at) VALUES (%s, %s) RETURNING id;""",
            (url_name, datetime.now())
        )
        id = cur.fetchone()
        db.commit()

        return id.id
    except psycopg2.DatabaseError as e:
        print('Ошибка add_url' + ' ' + str(e))


@create_db_connection(DATABASE_URL)
def create_url_check(url, status_code: int, tags_data: dict, cur: psycopg2, db: psycopg2):
    try:
        cur.execute(
            """INSERT INTO url_checks
            (url_id, status_code, h1, title, description, created_at)
            VALUES (%s, %s, %s, %s, %s, %s);""",
            (
                url.id,
                status_code,
                tags_data['h1'],
                tags_data['title'],
                tags_data['description'],
                datetime.now(),
            ),
        )
        db.commit()
    except psycopg2.DatabaseError as e:
        print('Ошибка create_url_check' + ' ' + str(e))


@create_db_connection(DATABASE_URL)
def get_url_by_url_name(url_name: str, cur: psycopg2, db: psycopg2) -> NamedTuple:
    try:
        cur.execute("""SELECT * FROM urls WHERE name = %s LIMIT 1;""", (url_name,), )
        url = cur.fetchone()

        return url

    except psycopg2.DatabaseError as e:
        print('Ошибка create_url_check' + ' ' + str(e))


@create_db_connection(DATABASE_URL)
def get_urls_and_last_checks_data(cur: psycopg2, db: psycopg2) -> List[NamedTuple]:
    try:

        cur.execute(
            """SELECT DISTINCT ON (urls.id) id, name FROM urls;"""
        )
        data_urls = cur.fetchall()
        cur.execute(
            """SELECT DISTINCT ON (url_checks.url_id) url_id, status_code, created_at
            FROM url_checks;"""
        )
        data_url_checks = cur.fetchall()
        data_urls_dict = {url.id: url for url in data_urls}
        record = namedtuple('Record', ['id', 'name', 'status_code', 'created_at'])

        data = []
        for check in data_url_checks:
            url = data_urls_dict.get(check.url_id)
            if url:
                data.append(record(url.id, url.name, check.status_code, check.created_at))
        data = sorted(data, key=lambda rec: (rec.id, rec.created_at), reverse=True)

        return data

    except psycopg2.DatabaseError as e:
        print('Ошибка get_urls_and_last_checks_data' + ' ' + str(e))


@create_db_connection(DATABASE_URL)
def get_url_by_id(url_id, cur: psycopg2, db: psycopg2) -> NamedTuple:
    try:
        cur.execute("""SELECT * FROM urls WHERE id = %s LIMIT 1;""", (url_id,), )
        url = cur.fetchone()

        return url

    except psycopg2.DatabaseError as e:
        print('Ошибка get_url_by_id' + ' ' + str(e))


@create_db_connection(DATABASE_URL)
def get_url_checks_by_url_id(url_id, cur: psycopg2, db: psycopg2) -> NamedTuple:
    try:
        cur.execute("""SELECT *
                FROM url_checks
                WHERE url_id = %s
                ORDER BY id DESC;""", (url_id,), )
        url_checks = cur.fetchall()
        return url_checks

    except psycopg2.DatabaseError as e:
        print('Ошибка get_url_checks_by_url_id' + ' ' + str(e))
