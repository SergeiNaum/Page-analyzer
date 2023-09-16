import os
import psycopg2

from datetime import datetime
from typing import NamedTuple
from psycopg2.extras import NamedTupleCursor

DATABASE_URL = os.getenv('DATABASE_URL')


def get_connection():
    return psycopg2.connect(DATABASE_URL)


class FDataBase:

    def __init__(self, conn):
        self.__db = conn
        self.__cur = self.__db.cursor(cursor_factory=NamedTupleCursor)

    def add_url(self, url_name: str) -> NamedTuple:
        try:
            self.__cur.execute(
                """INSERT INTO urls (name, created_at) VALUES (%s, %s) RETURNING id;""",
                (url_name, datetime.now())
            )
            id = self.__cur.fetchone()
            self.__db.commit()

            return id.id
        except psycopg2.DatabaseError as e:
            print('Ошибка add_url' + ' ' + str(e))

    def create_url_check(self, url, status_code: int, tags_data: dict):
        try:
            self.__cur.execute(
                """INSERT INTO url_checks
                (url_id, status_code, h1, title, description, created_at)\
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
            self.__db.commit()
        except psycopg2.DatabaseError as e:
            print('Ошибка create_url_check' + ' ' + str(e))

    def get_url_by_url_name(self, url_name: str) -> NamedTuple:
        try:
            self.__cur.execute("""SELECT * FROM urls WHERE name = %s LIMIT 1;""", (url_name,), )
            url = self.__cur.fetchone()

            return url

        except psycopg2.DatabaseError as e:
            print('Ошибка create_url_check' + ' ' + str(e))

    def get_urls_and_last_checks_data(self) -> NamedTuple:
        try:
            self.__cur.execute("""SELECT DISTINCT ON (urls.id)
                        urls.id,
                        urls.name,
                        url_checks.status_code,
                        url_checks.created_at
                        FROM urls
                        LEFT JOIN url_checks
                        ON urls.id = url_checks.url_id
                        ORDER BY urls.id DESC, url_checks.created_at DESC;""")
            data = self.__cur.fetchall()

            return data
        except psycopg2.DatabaseError as e:
            print('Ошибка get_urls_and_last_checks_data' + ' ' + str(e))

    def get_url_by_id(self, url_id) -> NamedTuple:
        try:
            self.__cur.execute("""SELECT * FROM urls WHERE id = %s LIMIT 1;""", (url_id,), )
            url = self.__cur.fetchone()

            return url
        except psycopg2.DatabaseError as e:
            print('Ошибка get_url_by_id' + ' ' + str(e))

    def get_url_checks_by_url_id(self, url_id) -> NamedTuple:
        try:
            self.__cur.execute("""SELECT *
                    FROM url_checks
                    WHERE url_id = %s
                    ORDER BY id DESC;""", (url_id,), )
            url_checks = self.__cur.fetchall()
            return url_checks

        except psycopg2.DatabaseError as e:
            print('Ошибка get_url_checks_by_url_id' + ' ' + str(e))
