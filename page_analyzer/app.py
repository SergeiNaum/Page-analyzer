import math

from polog import log
from flask import (
    Flask,
    render_template,
    get_flashed_messages,
    request,
    flash,
    redirect,
    url_for,
    abort,
)

from page_analyzer import db, web_utils
from page_analyzer import soup
from page_analyzer.app_config import SECRET_KEY
from page_analyzer.app_config import DATABASE_URL


# app config
app = Flask(__name__)
app.secret_key = SECRET_KEY


@log
def get_pagination():
    conn = db.get_connection(DATABASE_URL)
    try:
        page_size = 5
        total_count = db.get_records_count(conn)
        page_count = math.ceil(total_count / page_size)
        current_page = int(request.args.get('page', 1))
        offset = (current_page - 1) * page_size

        return page_size, offset, page_count, current_page
    finally:
        db.close_connection(conn)


def get_redirect_to_url_details_page(id: int):
    return redirect(url_for('get_url_details', id=id))


@log
@app.route('/')
def index():
    messages = get_flashed_messages(with_categories=True)
    return render_template('index.html', messages=messages)


@log
@app.get('/urls')
def urls_show():
    conn = db.get_connection(DATABASE_URL)
    page_size, offset, page_count, current_page = get_pagination()
    try:
        data = db.get_urls_and_last_checks_data(conn, page_size, offset)
        return render_template('urls/index.html',
                               data=data, page_count=page_count, current_page=current_page)
    finally:
        db.close_connection(conn)


@log
@app.post('/urls')
def post_url():
    conn = db.get_connection(DATABASE_URL)
    try:
        url_name = request.form.get('url')
        errors = web_utils.validate_url(url_name)

        if errors:
            for error in errors:
                flash(error, 'danger')

            return render_template('index.html', url_name=url_name,
                                   messages=get_flashed_messages(with_categories=True), ), 422

        url_name = web_utils.get_main_page_url(url_name)
        url = db.get_url_by_url_name(conn, url_name)

        if url:
            flash('Страница уже существует', 'info')
            id = url.id
        else:
            id = db.add_url(conn, url_name)
            flash('Страница успешно добавлена', 'success')

        return get_redirect_to_url_details_page(id)

    finally:
        db.close_connection(conn)


@log
@app.get('/urls/<int:id>')
def get_url_details(id: int):
    conn = db.get_connection(DATABASE_URL)
    try:
        return render_template('urls/url.html', url=db.get_url_by_id(conn, id),
                               url_checks=db.get_url_checks_by_url_id(conn, id),
                               messages=get_flashed_messages(with_categories=True), )
    finally:
        db.close_connection(conn)


@log
@app.post('/urls/<int:id>/checks')
def post_url_check(id: int):
    conn = db.get_connection(DATABASE_URL)
    try:
        url = db.get_url_by_id(conn, id)
        page_data = soup.get_page_data(url.name)
        status_code = page_data['status_code']

        if status_code and status_code < 400:
            db.create_url_check(conn, url, status_code, page_data)

            flash('Страница успешно проверена', 'success')

        elif status_code is None:
            abort(500, 'internal_error')

        else:
            flash('Произошла ошибка при проверке', 'danger')

        return get_redirect_to_url_details_page(id)

    finally:
        db.close_connection(conn)


@log
@app.errorhandler(404)
def not_found_error(error):
    error_message = "Страница не найдена! Пожалуйста, проверьте URL."
    return render_template('errors/error_404.html', error_message=error_message), 404


@log
@app.errorhandler(500)
def internal_error(error):
    error_message = "Внутренняя ошибка сервера! Пожалуйста, повторите попытку позже."
    return render_template('errors/error_500.html', error_message=error_message), 500
