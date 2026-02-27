"""
Azure Container Apps 動的セッション × Azure OpenAI サンプル (GPT Code Interpreter)

Azure OpenAI の Function Calling を使い、動的セッションを
コード実行ツールとして活用するサンプルです。
GPT モデルが必要に応じて Python コードを生成し、
動的セッションのサンドボックス環境で安全に実行します。
"""

import json
import os
import sys
import uuid

import httpx
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
from openai import AzureOpenAI


def get_session_headers() -> dict:
    """Dynamic Sessions 用の認証ヘッダーを取得する"""
    credential = DefaultAzureCredential()
    token = credential.get_token("https://dynamicsessions.io/.default")
    return {
        "Authorization": f"Bearer {token.token}",
        "Content-Type": "application/json",
    }


def execute_code_in_session(pool_endpoint: str, code: str, session_id: str) -> str:
    """Dynamic Sessions でコードを実行する"""
    headers = get_session_headers()
    url = f"{pool_endpoint}/executions?identifier={session_id}&api-version=2025-10-02-preview"
    payload = {
        "codeInputType": "inline",
        "executionType": "synchronous",
        "code": code,
        "timeoutInSeconds": 60,
    }
    with httpx.Client() as client:
        print(f"   🌐 Dynamic Sessions API 呼び出し中...")
        print(f"      POST {url[:80]}...")
        response = client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()

    status = result.get("status", "Unknown")
    exec_time = result.get("result", {}).get("executionTimeInMilliseconds", "N/A")
    print(f"   ✅ Dynamic Sessions 実行完了 (ステータス: {status}, 実行時間: {exec_time}ms)")

    stdout = result.get("result", {}).get("stdout", "")
    stderr = result.get("result", {}).get("stderr", "")
    execution_result = result.get("result", {}).get("executionResult", "")

    output_parts = []
    if stdout:
        output_parts.append(stdout)
    if execution_result:
        output_parts.append(str(execution_result))
    if stderr:
        output_parts.append(f"[stderr]: {stderr}")

    return "\n".join(output_parts).strip() if output_parts else "(実行完了・出力なし)"


# Azure OpenAI に登録するツール定義（Function Calling）
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "execute_python_code",
            "description": (
                "クラウド上の安全なサンドボックスで Python コードを実行します。"
                "計算、データ分析、グラフ作成などに使用できます。"
                "pandas, numpy, matplotlib, scipy などの主要ライブラリが利用可能です。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "実行する Python コード",
                    }
                },
                "required": ["code"],
            },
        },
    }
]

SYSTEM_PROMPT = (
    "あなたは優秀なアシスタントです。ユーザーの質問に答えるために、"
    "必要に応じて Python コードを実行できます。"
    "計算やデータ処理が必要な場合は、execute_python_code ツールを使用してください。"
    "コードの実行結果は必ず print() で出力するようにしてください。"
)


def chat_with_code_execution(
    client: AzureOpenAI,
    model: str,
    pool_endpoint: str,
    user_message: str,
    session_id: str,
) -> str:
    """Azure OpenAI にメッセージを送信し、必要に応じてコードを実行する"""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    print(f"\n{'='*60}")
    print(f"📝 ユーザー: {user_message}")
    print(f"{'='*60}")

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
    )

    assistant_message = response.choices[0].message

    # ツール呼び出しがある場合、実行して結果を返す（複数回のツール呼び出しに対応）
    while assistant_message.tool_calls:
        messages.append(assistant_message)

        for tool_call in assistant_message.tool_calls:
            function_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)

            if function_name == "execute_python_code":
                code = arguments["code"]
                print(f"\n🔧 GPT が Function Calling でコード実行を要求しました:")
                print(f"   関数名: {function_name}")
                print(f"```python\n{code}\n```")

                try:
                    result = execute_code_in_session(
                        pool_endpoint, code, session_id
                    )
                    print(f"\n📊 実行結果:\n{result}")
                except Exception as e:
                    result = f"エラーが発生しました: {e}"
                    print(f"\n❌ {result}")

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    }
                )

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
        )
        assistant_message = response.choices[0].message

    final_answer = assistant_message.content
    print(f"\n🤖 GPT: {final_answer}")
    return final_answer


def run_demo(
    client: AzureOpenAI,
    model: str,
    pool_endpoint: str,
    session_id: str,
):
    """デモ用の質問を実行する"""
    examples = [
        "2の20乗を計算してください",
        "1から100までの素数をすべて表示してください",
        "pandasを使って、日本の主要5都市（東京、大阪、名古屋、札幌、福岡）の人口データを作成し、人口の多い順にソートして表示してください",
    ]

    for example in examples:
        chat_with_code_execution(
            client=client,
            model=model,
            pool_endpoint=pool_endpoint,
            user_message=example,
            session_id=session_id,
        )


def run_interactive(
    client: AzureOpenAI,
    model: str,
    pool_endpoint: str,
    session_id: str,
):
    """対話モードで実行する"""
    print("\n💬 対話モードを開始します。'quit' または 'exit' で終了します。")
    print("   質問を入力してください。GPT が必要に応じてコードを実行して回答します。\n")

    while True:
        try:
            user_input = input("あなた: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n👋 終了します。")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("\n👋 終了します。")
            break

        chat_with_code_execution(
            client=client,
            model=model,
            pool_endpoint=pool_endpoint,
            user_message=user_input,
            session_id=session_id,
        )


def main():
    # .env ファイルを読み込み
    load_dotenv()

    # 環境変数の取得
    pool_endpoint = os.getenv("POOL_ENDPOINT")
    azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_openai_key = os.getenv("AZURE_OPENAI_API_KEY")
    azure_openai_model = os.getenv("AZURE_OPENAI_MODEL", "gpt-4o")

    # 必須環境変数のチェック
    if not pool_endpoint:
        print("❌ POOL_ENDPOINT が設定されていません。.env ファイルを確認してください。")
        sys.exit(1)
    if not azure_openai_endpoint:
        print("❌ AZURE_OPENAI_ENDPOINT が設定されていません。.env ファイルを確認してください。")
        sys.exit(1)
    if not azure_openai_key:
        print("❌ AZURE_OPENAI_API_KEY が設定されていません。.env ファイルを確認してください。")
        sys.exit(1)

    # Azure OpenAI クライアントの初期化
    client = AzureOpenAI(
        azure_endpoint=azure_openai_endpoint,
        api_key=azure_openai_key,
        api_version="2024-12-01-preview",
    )

    # セッション ID を生成
    session_id = f"gpt-demo-{uuid.uuid4().hex[:8]}"

    print(f"🚀 セッション ID: {session_id}")
    print(f"🔗 Azure OpenAI モデル: {azure_openai_model}")
    print(f"🏊 セッションプール: {pool_endpoint[:60]}...")

    # コマンドライン引数で対話モードを判定
    interactive = "--interactive" in sys.argv or "-i" in sys.argv

    if interactive:
        run_interactive(
            client=client,
            model=azure_openai_model,
            pool_endpoint=pool_endpoint,
            session_id=session_id,
        )
    else:
        run_demo(
            client=client,
            model=azure_openai_model,
            pool_endpoint=pool_endpoint,
            session_id=session_id,
        )

    print(f"\n{'='*60}")
    print("✅ 完了！")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
