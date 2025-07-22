import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os

def fetch_titles():
    url = 'https://tw.news.yahoo.com/'
    headers = {'User-Agent': 'Mozilla/5.0'}
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, 'html.parser')
    titles = soup.select('h3')[:5]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    msg = f"🕗 抓取時間：{now}\n\n"
    for i, tag in enumerate(titles, 1):
        msg += f"{i}. {tag.get_text(strip=True)}\n"
    return msg

def send_telegram_message(message):
    token = os.getenv("8129498978:AAGWiak-ThWYyb14HiBbBr1mLjCM8QbjUHo")
    chat_id = os.getenv("1734667191")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    response = requests.post(url, data=payload)
    print("✅ 發送狀態：", response.status_code)

if __name__ == "__main__":
    news = fetch_titles()
    print(news)
    send_telegram_message(news)

