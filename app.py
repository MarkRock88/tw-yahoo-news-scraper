import os
import json
import csv
import requests
from bs4 import BeautifulSoup
from base64 import b64encode
from datetime import datetime

# 讀取環境變數
GITHUB_TOKEN = os.environ['GITHUB_TOKEN']
GITHUB_USERNAME = os.environ['GITHUB_USERNAME']
GITHUB_REPO = os.environ['GITHUB_REPO']  # 格式: username/repo
TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
TELEGRAM_CHAT_ID = os.environ['TELEGRAM_CHAT_ID']

# 今天日期（格式化）
today_date = datetime.now().strftime("%Y_%m_%d")
LOCAL_FILENAME = f"cs2_pro_settings_{today_date}.csv"
GITHUB_FILE_PATH = f"cs2_pro_settings/{LOCAL_FILENAME}"

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

def save_to_csv(headers, data, filename):
    try:
        with open(filename, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(data)
        print(f"✅ 已存成 CSV: {filename}")
    except Exception as e:
        print(f"❌ 存檔失敗：{e}")

def encode_file_to_base64(file_path):
    with open(file_path, "rb") as f:
        file_content = f.read()
    return b64encode(file_content).decode('utf-8')

def upload_file_to_github(local_file_path, github_path):
    """上傳檔案至 GitHub（不覆蓋，依照日期命名）"""
    file_content = encode_file_to_base64(local_file_path)

    commit_message = f"Add {os.path.basename(github_path)}"
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{github_path}"

    headers = {
        'Authorization': f'Bearer {GITHUB_TOKEN}'
    }

    data = {
        "message": commit_message,
        "content": file_content,
        "branch": "main"
    }

    response = requests.put(url, json=data, headers=headers)

    if response.status_code in [200, 201]:
        print(f"✅ 檔案已成功上傳至 GitHub: {github_path}")
    else:
        print(f"❌ 上傳失敗，狀態碼：{response.status_code}")
        print(response.json())

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

if __name__ == "__main__":
    result = fetch_full_cs2_table()
    if isinstance(result, str):
        print(result)
    else:
        headers, data = result

        # 儲存為本地 CSV
        save_to_csv(headers, data, filename=LOCAL_FILENAME)

        # 上傳到 GitHub，使用包含日期的路徑
        upload_file_to_github(LOCAL_FILENAME, GITHUB_FILE_PATH)

        # 傳送 ZOWIE 訊息
        msg = format_table_to_text(headers, data, limit=20)
        print(msg)
        send_telegram_message(msg)
