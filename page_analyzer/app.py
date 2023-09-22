
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

app = Flask(__name__)
# app config
app.secret_key = SECRET_KEY


# def get_db() -> Optional[Any]:
#     """Database connection, if not already install"""
#     if not hasattr(g, 'link_db'):
#         g.link_db = db.get_connection(DATABASE_URL)
#     return g.link_db


# dbase = None


# @app.before_request
# def before_request():
#     """Establishing a connection to the database before executing a query"""
#     conn = get_db()
#     global dbase
#     dbase = db.FDataBase(conn)
#
#
# @app.teardown_appcontext
# def close_db(error):
#     """Close the database connection, if it was established"""
#     if hasattr(g, 'link_db'):
#         g.link_db.close()


def get_redirect_to_url_details_page(id: int):
    return redirect(url_for('get_url_details', id=id))


@app.route('/')
def index():
    messages = get_flashed_messages(with_categories=True)
    return render_template('index.html', messages=messages)


@app.get('/urls')
def urls_show():
    data = db.get_urls_and_last_checks_data()

    return render_template('urls/index.html', data=data)


@app.post('/urls')
def post_url():
    url_name = request.form.get('url')
    errors = web_utils.validate_url(url_name)

    if errors:
        for error in errors:
            flash(error, 'danger')

        return render_template('index.html', url_name=url_name,
                               messages=get_flashed_messages(with_categories=True), ), 422

    url_name = web_utils.get_main_page_url(url_name)
    url = db.get_url_by_url_name(url_name)

    if url:
        flash('Страница уже существует', 'info')
        id = url.id
    else:
        id = db.add_url(url_name)
        flash('Страница успешно добавлена', 'success')

    return get_redirect_to_url_details_page(id)


@app.get('/urls/<int:id>')
def get_url_details(id: int):
    return render_template('urls/url.html', url=db.get_url_by_id(id),
                           url_checks=db.get_url_checks_by_url_id(id),
                           messages=get_flashed_messages(with_categories=True), )


@app.post('/urls/<int:id>/checks')
def post_url_check(id: int):
    url = db.get_url_by_id(id)
    # status_code = web_utils.get_status_code_by_url(url.name)
    tags_data = soup.get_page_data(url.name)
    status_code = tags_data['status_code']

    if status_code and status_code < 400:
        db.create_url_check(url, status_code, tags_data)

        flash('Страница успешно проверена', 'success')
    else:
        flash('Произошла ошибка при проверке', 'danger')

    return get_redirect_to_url_details_page(id)


@app.errorhandler(404)
def not_found_error(error):
    error_message = "Страница не найдена! Пожалуйста, проверьте URL."
    return render_template('errors.html', error_message=error_message), 404


@app.errorhandler(500)
def internal_error(error):
    error_message = "Внутренняя ошибка сервера! Пожалуйста, повторите попытку позже."
    return render_template('errors.html', error_message=error_message), 500
