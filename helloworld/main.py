import os
import httpx

from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv


def get_headers() -> dict:
    """認証ヘッダーを取得する"""
    credential = DefaultAzureCredential()
    token = credential.get_token("https://dynamicsessions.io/.default")
    return {
        "Authorization": f"Bearer {token.token}",
        "Content-Type": "application/json"
    }


def list_sessions(base_url: str, headers: dict) -> dict:
    """動的セッションの一覧を取得する"""
    list_url = f"{base_url}/listSessions?api-version=2025-10-02-preview"
    with httpx.Client() as client:
        response = client.get(list_url, headers=headers)
        response.raise_for_status()
        return response.json()


def execute_code(base_url: str, headers: dict, exec_id: str, code: str, timeout: int = 60) -> dict:
    """セッションでコードを実行する"""
    exec_url = f"{base_url}/executions?identifier={exec_id}&api-version=2025-10-02-preview"
    payload = {
        "codeInputType": "inline",
        "executionType": "synchronous",
        "code": code,
        "timeoutInSeconds": timeout
    }
    with httpx.Client() as client:
        response = client.post(exec_url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()


def main():
    # .env ファイルを読み込み
    load_dotenv()

    base_url = os.getenv("POOL_ENDPOINT")
    headers = get_headers()

    # 現在の動的セッションの一覧を取得
    sessions = list_sessions(base_url, headers)
    print(f"Current Sessions: (count: {len(sessions.get('sessions', []))})\n", sessions)

    # 新しいセッションでコードを実行
    result = execute_code(
        base_url,
        headers,
        exec_id="my-session-001",
        code="print('Hello, Azure Container Apps Sessions')"
    )
    print("Execution Result:\n", result)

    # 新しいセッションでコードを実行
    result = execute_code(
        base_url,
        headers,
        exec_id="my-session-002",
        code="x = 100; print(f'x = {x}')"
    )
    print("Execution Result:\n", result)

    # 実行後の動的セッションの一覧を取得
    sessions = list_sessions(base_url, headers)
    print(f"Current Sessions: (count: {len(sessions.get('sessions', []))})\n", sessions)

if __name__ == "__main__":
    main()
