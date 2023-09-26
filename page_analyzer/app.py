
from flask_caching import Cache
from polog import log
from flask import (
    Flask,
    render_template,
    get_flashed_messages,
    request,
    flash,
    redirect,
    url_for,
)

from page_analyzer import db, web_utils
from page_analyzer import soup
from page_analyzer.app_config import SECRET_KEY
from page_analyzer.app_config import DATABASE_URL


# app config
config = {
    "CACHE_TYPE": "FileSystemCache",
    "CACHE_DEFAULT_TIMEOUT": 300,
    "CACHE_DIR": "cache"
}


app = Flask(__name__)


app.secret_key = SECRET_KEY
app.config.from_mapping(config)
cache = Cache(app)


def get_redirect_to_url_details_page(id: int):
    return redirect(url_for('get_url_details', id=id))


@log
@app.route('/')
@cache.cached(timeout=50)
def index():
    messages = get_flashed_messages(with_categories=True)
    return render_template('index.html', messages=messages)


@log
@app.get('/urls')
def urls_show():
    conn = db.get_connection(DATABASE_URL)
    try:
        data = db.get_urls_and_last_checks_data(conn)
        return render_template('urls/index.html', data=data)
    finally:
        conn.close()


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
        url = db.get_url_by_url_name(url_name, conn)

        if url:
            flash('Страница уже существует', 'info')
            id = url.id
        else:
            id = db.add_url(url_name, conn)
            flash('Страница успешно добавлена', 'success')

        return get_redirect_to_url_details_page(id)

    finally:
        conn.close()


@log
@app.get('/urls/<int:id>')
def get_url_details(id: int):
    conn = db.get_connection(DATABASE_URL)
    try:
        return render_template('urls/url.html', url=db.get_url_by_id(id, conn),
                               url_checks=db.get_url_checks_by_url_id(id, conn),
                               messages=get_flashed_messages(with_categories=True), )
    finally:
        conn.close()


@log
@app.post('/urls/<int:id>/checks')
def post_url_check(id: int):
    conn = db.get_connection(DATABASE_URL)
    try:
        url = db.get_url_by_id(id, conn)
        page_data = soup.get_page_data(url.name)
        status_code = page_data['status_code']

        if status_code and status_code < 400:
            db.create_url_check(url, status_code, page_data, conn)

            flash('Страница успешно проверена', 'success')

        elif status_code is None:
            redirect(url_for('internal_error'))

        else:
            flash('Произошла ошибка при проверке', 'danger')

        return get_redirect_to_url_details_page(id)

    finally:
        conn.close()


@log
@app.errorhandler(404)
def not_found_error(error):
    error_message = "Страница не найдена! Пожалуйста, проверьте URL."
    return render_template('error_404.html', error_message=error_message), 404


@log
@app.errorhandler(500)
def internal_error(error):
    error_message = "Внутренняя ошибка сервера! Пожалуйста, повторите попытку позже."
    return render_template('error_500.html', error_message=error_message), 500
