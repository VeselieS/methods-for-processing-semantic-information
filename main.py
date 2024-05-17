import aiohttp
import asyncio
from bs4 import BeautifulSoup

SITE_URL = 'https://m.lenta.ru/parts/news/'
PAGE_URL = lambda page_number: f'{SITE_URL}{page_number}'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'
}


async def fetch_content(url, session):
    async with session.get(url, headers=headers) as response:
        return await response.text()


async def get_page_urls(session):
    async with session.get(SITE_URL, headers=headers) as response:
        if response.status == 200:
            content = await response.text()
            soup = BeautifulSoup(content, 'html.parser')
            pagination = soup.find(class_='parts-page__item')
            cleaned_text = pagination.text.strip()
            pages = cleaned_text.replace('\xa0', '').split('\n')
            # pages = [int(page) for page in pages if page != '…']
            pages = [10]
            min_page = min(pages)
            max_page = max(pages)
            return [PAGE_URL(page_number) for page_number in range(min_page, max_page + 1)]
        else:
            print('Ошибка при запросе:', response.status)
            return []


async def get_article_urls(url, session):
    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            content = await response.text()
            soup = BeautifulSoup(content, 'html.parser')
            content = soup.find_all(class_='news-item')
            return [item.find('a').get('href') for item in content]
        else:
            print('Ошибка при запросе:', response.status)
            return []


async def get_article_content(url, session):
    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            content = await response.text()
            soup = BeautifulSoup(content, 'html.parser')
            title = soup.find('h1').text
            body = [p.text for p in soup.find('body').find_all('p')]
            return title, body
        else:
            print('Ошибка при запросе:', response.status)
            return None, None


async def main():
    async with aiohttp.ClientSession() as session:
        page_urls = await get_page_urls(session)
        for page_url in page_urls:
            article_urls = await get_article_urls(page_url, session)
            for article_url in article_urls:
                title, body = await get_article_content(article_url, session)
                if title and body:
                    print(title)


if __name__ == '__main__':
    asyncio.run(main())
