import os
import json
import csv
import requests
from bs4 import BeautifulSoup
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# 使用環境變數設定
TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
TELEGRAM_CHAT_ID = os.environ['TELEGRAM_CHAT_ID']
GOOGLE_DRIVE_FOLDER_ID = os.environ['GOOGLE_DRIVE_FOLDER_ID']  # Google Drive 目標資料夾 ID

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


def upload_to_google_drive(local_file, folder_id):
    try:
        credentials_info = json.loads(os.environ["GOOGLE_APPLICATION_CREDENTIALS"])  # 從環境變數讀取憑證
        credentials = Credentials.from_service_account_info(credentials_info)
        drive_service = build('drive', 'v3', credentials=credentials)

        file_metadata = {
            'name': os.path.basename(local_file),
            'parents': [folder_id]  # 指定文件上傳的 Google Drive 資料夾
        }
        media = MediaFileUpload(local_file, mimetype='application/vnd.ms-excel')
        
        file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        print(f"✅ 已上傳 {local_file} 至 Google Drive 資料夾，文件 ID：{file.get('id')}")
    except Exception as e:
        print(f"❌ 上傳到 Google Drive 失敗：{e}")


if __name__ == "__main__":
    result = fetch_full_cs2_table()
    if isinstance(result, str):
        print(result)
        send_telegram_message(result)
    else:
        headers, data = result

        # 傳送前 ZOWIE 的前 20 筆資料到 Telegram
        msg = format_table_to_text(headers, data, limit=20)
        print(msg)
        send_telegram_message(msg)

        # 存成 CSV 檔
        filename = "cs2_pro_settings.csv"
        save_to_csv(headers, data, filename)

        # 上傳 CSV 至 Google Drive
        upload_to_google_drive(filename, GOOGLE_DRIVE_FOLDER_ID)
