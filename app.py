import requests
from bs4 import BeautifulSoup
from datetime import datetime

def fetch_titles():
    url = 'https://tw.news.yahoo.com/'
    headers = {'User-Agent': 'Mozilla/5.0'}
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, 'html.parser')
    titles = soup.select('h3')[:5]

    print(f"🕗 抓取時間：{datetime.now()}")
    for i, tag in enumerate(titles, 1):
        print(f"{i}. {tag.get_text(strip=True)}")

if __name__ == "__main__":
    fetch_titles()
