import requests
from bs4 import BeautifulSoup


def get_page_data(url_name: str) -> dict:
    h1 = ''
    title = ''
    description = ''

    try:
        resp = requests.get(url_name)
        status_code = resp.status_code
        soup = BeautifulSoup(resp.text, 'html.parser')

        h1_tag = soup.h1
        title_tag = soup.title
        meta_tag = soup.find('meta', attrs={'name': 'description'})

        if h1_tag:
            h1 = h1_tag.text
        if title_tag:
            title = title_tag.text
        if meta_tag:
            description = meta_tag.get('content')

        return {
            'h1': h1,
            'title': title,
            'description': description,
            'status_code': status_code
        }
    except requests.RequestException:
        print(f'Ошибка запроса на url: {url_name}')
