import os
import json
import csv
import requests
from bs4 import BeautifulSoup
from base64 import b64encode

# 讀取環境變數
GITHUB_TOKEN = os.environ['GITHUB_TOKEN']
GITHUB_USERNAME = os.environ['GITHUB_USERNAME']
GITHUB_REPO = os.environ['GITHUB_REPO']  # 格式: username/repo
GITHUB_FILE_PATH = 'cs2_pro_settings.csv'  # repo 裡的路徑與檔名

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

def save_to_csv(headers, data, filename="cs2_pro_settings.csv"):
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
    file_sha = get_file_sha()
    file_content = encode_file_to_base64(file_path)
    
    commit_message = "Update cs2_pro_settings.csv"
    
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE_PATH}"
    
    data = {
        "message": commit_message,
        "content": file_content,
        "branch": "main"  # 可以改成自己的分支名稱
    }
    
    # 如果檔案已存在，更新檔案
    if file_sha:
        data["sha"] = file_sha  # 加入 SHA 值，告訴 GitHub 進行更新
    
    headers = {
        'Authorization': f'Bearer {GITHUB_TOKEN}'
    }
    
    response = requests.put(url, json=data, headers=headers)
    
    if response.status_code == 201:
        print("✅ 檔案上傳成功")
    else:
        print(f"❌ 上傳失敗: {response.status_code}")
        print(response.json())

if __name__ == "__main__":
    # 抓取並處理資料
    result = fetch_full_cs2_table()
    if isinstance(result, str):
        print(result)
    else:
        headers, data = result
        # 存成 CSV 檔
        save_to_csv(headers, data)

        # 上傳至 GitHub Repo
        upload_file_to_github("cs2_pro_settings.csv")
