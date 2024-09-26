import os
import requests
import json
import base64
import streamlit as st

# 環境変数から値を取得
API_KEY = st.secrets["DIFY_API_KEY"]
API_ENDPOINT = st.secrets["DIFY_API_ENDPOINT"]
USER_ID = st.secrets["USER_ID"]
UPLOAD_URL = st.secrets["UPLOAD_URL"]

# セッション状態を初期化
if 'button_clicked' not in st.session_state:
    st.session_state.button_clicked = False

# ボタンがクリックされたときの処理
def on_button_click():
    st.session_state.button_clicked = True

def upload_file(file_path, file_type):
    url = f"{UPLOAD_URL}/upload"
    
    # リクエストヘッダー
    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }

    # ファイル名を取得
    file_name = os.path.basename(file_path)

    # リクエストボディ
    files = {
        'file': (file_name, open(file_path, 'rb'), file_type)
    }

    data = {
        'user': USER_ID
    }
    
    # APIリクエスト送信
    response = requests.post(url, headers=headers, files=files, data=data)

    # ファイルIDの取得
    if 200 <= response.status_code < 300:
        return response.json()['id']
    else:
        print(f"エラー: {response.status_code}")
        print(response.text)
        return None

def run_dify_workflow(file_id):
    url = f"{API_ENDPOINT}/workflows/run"

    # リクエストヘッダー
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    # リクエストボディ
    payload = {
        "inputs": {},
        "query": "",
        "response_mode": "blocking",
        "conversation_id": "",  # 新しい会話ごとに空文字列を使用
        "user": USER_ID,
        "files": [
            {
                "type": "image",
                "transfer_method": "remote_url",
                "url": "https://storage.googleapis.com/tiktok_analysis/%E6%9C%AA%E8%A8%98%E5%85%A5%E3%82%A2%E3%83%B3%E3%82%B1%E3%83%BC%E3%83%88/template.png"
            },
            {
                "type": "image",
                "transfer_method": "local_file",
                "upload_file_id": file_id
            },
        ]
    }

    # APIリクエスト送信
    try:
        response = requests.post(
            url,
            headers=headers,
            data=json.dumps(payload),
            timeout=30  # タイムアウトを設定
        )
        response.raise_for_status()  # HTTPエラーがあれば例外を発生させる
    except requests.exceptions.RequestException as e:
        return f"Error: {e}"

    # レスポンス処理
    if response.status_code == 200:
        return response.json()
    else:
        return f"Error: {response.status_code}, {response.text}"

def main():
    st.title("アンケート集計")

    uploaded_file = st.file_uploader("画像ファイルを選択してください", type=["jpg", "jpeg", "png"])
    if uploaded_file is not None:
        file_type = uploaded_file.type

    if uploaded_file is not None:
        # 一時ファイルとして保存
        with open("temp_image.jpg", "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        if st.button("アップロードして処理を開始", on_click=on_button_click, disabled=st.session_state.button_clicked):
            file_id = upload_file("temp_image.jpg", file_type)
            if file_id:
                st.success(f"ファイルがアップロードされました。")

                # ワークフローを実行
                result = run_dify_workflow(file_id)

                # 結果をJSON形式に変換してターミナルに出力
                if isinstance(result, dict):
                    json_result = json.dumps(result, indent=2, ensure_ascii=False)

                    # JSONをパースして値を取得
                    parsed_result = json.loads(json_result)
                    
                    # textとurlの値を取得
                    text = parsed_result.get('data', {}).get('outputs', {}).get('text')
                    url = parsed_result.get('data', {}).get('outputs', {}).get('url')
                    
                    st.subheader("出力結果")
                    st.json(text)

                    st.subheader("スプレッドシート")
                    st.write(url)
                else:
                    print(f"予期しない結果タイプ: {type(result)}")
                    print(result)
                
            else:
                st.error("ファイルのアップロードに失敗しました。")

        # 一時ファイルを削除
        os.remove("temp_image.jpg")

        if st.session_state.button_clicked:
            # セッション状態を初期化
            st.session_state.button_clicked = False

if __name__ == "__main__":
    main()