import os
import json
import csv
import requests
from bs4 import BeautifulSoup
from base64 import b64encode
from datetime import datetime  # 引入 datetime 模組

# 讀取環境變數
GITHUB_TOKEN = os.environ['GITHUB_TOKEN']
GITHUB_USERNAME = os.environ['GITHUB_USERNAME']
GITHUB_REPO = os.environ['GITHUB_REPO']  # 格式: username/repo
GITHUB_FILE_PATH = 'cs2_pro_settings.csv'  # repo 裡的路徑與檔名
TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
TELEGRAM_CHAT_ID = os.environ['TELEGRAM_CHAT_ID']

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


# 取得今天的日期並格式化為 yyyy/mm/dd
today_date = datetime.now().strftime("%Y/%m/%d").replace("/", "_")  # 轉換為 yyyy_mm_dd 格式

def save_to_csv(headers, data, filename=None):
    if filename is None:
        # 如果沒有提供 filename 參數，則默認使用包含日期的檔名
        filename = f"cs2_pro_settings_{today_date}.csv"
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

def get_file_sha():
    """查詢 GitHub Repo 中目標檔案的 SHA 值，若檔案存在，便能進行更新操作"""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE_PATH}"
    headers = {
        'Authorization': f'Bearer {GITHUB_TOKEN}'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()['sha']  # 取得檔案的 SHA 值
    elif response.status_code == 404:
        return None  # 檔案不存在
    else:
        print(f"❌ 查詢檔案 SHA 錯誤: {response.status_code}")
        return None

def upload_file_to_github(file_path):
    """上傳檔案至 GitHub"""
    file_sha = get_file_sha()  # 查詢 GitHub Repo 中檔案的 SHA 值
    file_content = encode_file_to_base64(file_path)

    # 取得今天的日期並格式化為 yyyy/mm/dd
    today_date = datetime.now().strftime("%Y/%m/%d").replace("/", "_")  # 轉換為 yyyy_mm_dd 格式
    # 組合檔案名稱
    commit_message = f"cs2_pro_settings_{today_date}.csv"
    
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE_PATH}"
    
    # 檢查檔案是否存在
    data = {
        "message": commit_message,
        "content": file_content,
        "branch": "main"  # 可以改成自己的分支名稱
    }
    
    if file_sha:
        # 檔案已經存在，傳遞 SHA 值來更新
        data["sha"] = file_sha
    
    headers = {
        'Authorization': f'Bearer {GITHUB_TOKEN}'
    }
    
    response = requests.put(url, json=data, headers=headers)
    
    if response.status_code == 201 or response.status_code == 200:
        response_data = response.json()
        commit_sha = response_data.get('commit', {}).get('sha')
        if commit_sha:
            print(f"✅ 檔案已成功更新，新的 commit SHA: {commit_sha}")
        else:
            print(f"✅ 檔案已成功上傳，但未返回 commit 詳細資料。")
    else:
        print(f"❌ 上傳失敗，狀態碼：{response.status_code}")
        print(response.json())

# A代碼部分
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
    # 取得今天的日期並格式化為 yyyy/mm/dd
    today_date = datetime.now().strftime("%Y/%m/%d").replace("/", "_")  # 轉換為 yyyy_mm_dd 格式
    # 組合檔案名稱
    filename = f"cs2_pro_settings_{today_date}.csv"
    
    # 抓取並處理資料
    result = fetch_full_cs2_table()
    if isinstance(result, str):
        print(result)
    else:
        headers, data = result
        # 存成 CSV 檔，使用包含日期的檔案名稱
        save_to_csv(headers, data, filename=filename)

        # 上傳至 GitHub Repo
        upload_file_to_github(filename)

        # 傳送前 ZOWIE 的前 20 筆資料到 Telegram
        msg = format_table_to_text(headers, data, limit=20)
        print(msg)
        send_telegram_message(msg)
