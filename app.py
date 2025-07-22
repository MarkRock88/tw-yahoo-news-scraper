import os
import json
import csv
import requests
import subprocess
from bs4 import BeautifulSoup

# 讀取環境變數
TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
TELEGRAM_CHAT_ID = os.environ['TELEGRAM_CHAT_ID']
GITHUB_TOKEN = os.environ['GITHUB_TOKEN']
GITHUB_USERNAME = os.environ['GITHUB_USERNAME']
GITHUB_REPO = os.environ['GITHUB_REPO']  # 格式 username/repo，例如 yourname/yourrepo

def fetch_full_cs2_table():
    url = 'https://prosettings.net/lists/cs2/'
    headers = {'User-Agent': 'Mozilla/5.0'}
    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        return f"❌ 無法取得資料（{r.status_code}）"

    soup = BeautifulSoup(r.text, 'html.parser')
    table = soup.find('table')

    if not table:
        return "❌ 找不到表格"

    thead = table.find('thead')
    tbody = table.find('tbody')
    header_cells = thead.find_all('th')
    headers = [th.get_text(strip=True) for th in header_cells]

    rows = tbody.find_all('tr')
    data = []
    for row in rows:
        cols = row.find_all('td')
        row_data = [col.get_text(strip=True) for col in cols]
        if len(row_data) == len(headers):
            data.append(dict(zip(headers, row_data)))
        else:
            print("⚠️ 欄位數不一致，跳過一筆")
    return headers, data

def format_table_to_text(headers, data, limit=20):
    filtered_data = [
        row for row in data
        if any("zowie" in str(value).lower() for value in row.values())
    ]
    count = len(filtered_data)
    msg = f"📊 含有 'ZOWIE' 的設定資料：共 {count} 筆，以下列出前 {limit} 筆\n\n"
    for i, row in enumerate(filtered_data[:limit]):
        msg += f"{i+1}. {row.get('Player', 'N/A')} - {row.get('Team', '')}\n"
        msg += f"   Mouse: {row.get('Mouse', '')} | DPI: {row.get('DPI', '')} | Sensitivity: {row.get('Sens', '')}\n"
        msg += f"   Monitor: {row.get('Monitor', '')}, Mousepad: {row.get('Mousepad', '')}\n"
        msg += "—" * 30 + "\n"
    return msg

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            print("✅ 成功發送 Telegram 訊息")
        else:
            print("❌ 發送失敗，狀態碼：", response.status_code)
    except Exception as e:
        print("❌ 發送錯誤：", e)

def save_to_csv(headers, data, filename="cs2_pro_settings.csv"):
    try:
        with open(filename, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(data)
        print(f"✅ 已存成 CSV: {filename}")
    except Exception as e:
        print(f"❌ 存檔失敗：{e}")

def setup_git():
    subprocess.run(['git', 'config', '--global', 'user.email', 'ma0815rk54@gmail.com'], check=True)
    subprocess.run(['git', 'config', '--global', 'user.name', GITHUB_USERNAME], check=True)

def git_commit_and_push(file_path, commit_message="自動更新 csv 備份"):
    try:
        setup_git()
        subprocess.run(['git', 'add', file_path], check=True)
        subprocess.run(['git', 'commit', '-m', commit_message], check=True)

        remote_url = f"https://{GITHUB_TOKEN}@github.com/{GITHUB_REPO}.git"

        # 移除 origin，如果不存在不會報錯
        subprocess.run(['git', 'remote', 'remove', 'origin'], check=False)
        subprocess.run(['git', 'remote', 'add', 'origin', remote_url], check=True)

        subprocess.run(['git', 'push', '-u', 'origin', 'main'], check=True)  # 如果是 master 分支，把 main 換成 master

        print("✅ 成功 commit 並推送到 GitHub")
    except subprocess.CalledProcessError as e:
        print(f"❌ Git 操作失敗：{e}")

if __name__ == "__main__":
    result = fetch_full_cs2_table()
    if isinstance(result, str):
        print(result)
        send_telegram_message(result)
    else:
        headers, data = result

        msg = format_table_to_text(headers, data, limit=20)
        print(msg)
        send_telegram_message(msg)

        filename = "cs2_pro_settings.csv"
        save_to_csv(headers, data, filename)

        git_commit_and_push(filename)
