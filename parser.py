import asyncio
import json
import time

import aiohttp
import nest_asyncio
from bs4 import BeautifulSoup

SITE_URL = 'https://naked-science.ru/article'
PAGE_URL = lambda page_number: f'{SITE_URL}/page/{page_number}'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36'
}


async def fetch_content(url, session):
    async with session.get(url, headers=HEADERS) as response:
        return await response.text()


async def get_page_urls(session):
    async with session.get(SITE_URL, headers=HEADERS) as response:
        if response.status == 200:
            content = await response.text()
            soup = BeautifulSoup(content, 'html.parser')
            pagination = soup.find(class_='pagination-block')
            cleaned_text = pagination.text.strip()
            pages = cleaned_text.replace('\xa0', '').split('\n')
            pages = [int(page) for page in pages if page != '…']
            min_page = min(pages)

            # Ограничение на парсинг только 5 первых страниц сайта (100 статей)
            # max_page = max(pages)
            max_page = 1
            return [PAGE_URL(page_number) for page_number in range(min_page, max_page + 1)]
        else:
            print('Ошибка при запросе:', response.status)
            return []


async def get_article_urls(url, session):
    async with session.get(url, headers=HEADERS) as response:
        if response.status == 200:
            content = await response.text()
            soup = BeautifulSoup(content, 'html.parser')
            content = soup.find_all(class_='news-item')
            return [item.find('a').get('href') for item in content]
        else:
            print('Ошибка при запросе:', response.status)
            return []


async def get_article_content(url, session):
    async with session.get(url, headers=HEADERS) as response:
        if response.status == 200:
            content = await response.text()
            soup = BeautifulSoup(content, 'html.parser')
            title = soup.find('h1').text
            body = [p.text for p in soup.find('body').find_all('p')][3:-19]
            body = ' '.join(body)
            category = [a.get_text(separator='\n', strip=True) for a in soup.find(class_='terms-items grid')][3::2]
            comments = [comment.text.strip() for comment in soup.find(class_='shesht-comments-list-tab').find_all(
                class_='shesht-comment-template__content-text')]
            created_date = soup.find('meta', property='article:published_time').get('content')[:10]
            index_importance = soup.find(class_='index_importance_news').text
            views = soup.find(class_='fvc-count').text.replace(' ', '')

            return {
                'title': title,
                'body': body,
                'category': category,
                'comments': comments,
                'created_date': created_date,
                'index_importance': index_importance,
                'views': views
            }
        else:
            print('Ошибка при запросе:', response.status)
            return None, None


async def main():
    articles = []
    async with aiohttp.ClientSession() as session:
        page_urls = await get_page_urls(session)
        for page_url in page_urls:
            article_urls = await get_article_urls(page_url, session)
            for article_url in article_urls:
                article_data = await get_article_content(article_url, session)
                if article_data:
                    articles.append(article_data)
                    print(article_data['title'])

    # Записываем статьи в файл articles.json
    with open('articles.json', 'w', encoding='utf-8') as file:
        json.dump(articles, file, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    nest_asyncio.apply()
    start_time = time.time()
    asyncio.run(main())
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Время выполнения скрипта: {elapsed_time} секунд")
