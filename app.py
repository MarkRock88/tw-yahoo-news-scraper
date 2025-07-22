def upload_file_to_github(file_path):
    """上傳檔案至 GitHub"""
    file_sha = get_file_sha()  # 查詢 GitHub Repo 中檔案的 SHA 值
    file_content = encode_file_to_base64(file_path)
    
    commit_message = "Update cs2_pro_settings.csv"
    
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
    
    if response.status_code == 201:
        print("✅ 檔案上傳成功")
    else:
        print(f"❌ 上傳失敗，狀態碼：{response.status_code}")
        print(response.json())
