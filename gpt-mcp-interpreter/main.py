"""
Azure Container Apps 動的セッション × Azure OpenAI Responses API + MCP サンプル

Azure OpenAI の Responses API と MCP (Model Context Protocol) を組み合わせ、
動的セッションをコード実行ツールとして活用するサンプルです。
Responses API が MCP サーバーと直接通信し、GPT モデルが必要に応じて
Python コード実行を自動的に行います。
"""

import os
import sys

from dotenv import load_dotenv
from openai import AzureOpenAI


def create_mcp_tool(mcp_endpoint: str, api_key: str) -> dict:
    """MCP ツール定義を作成する"""
    return {
        "type": "mcp",
        "server_label": "aca-python-sessions",
        "server_url": mcp_endpoint,
        "headers": {
            "x-ms-apikey": api_key,
        },
        "require_approval": "never",
    }


SYSTEM_PROMPT = (
    "あなたは優秀なアシスタントです。ユーザーの質問に答えるために、"
    "必要に応じて MCP サーバー経由で Python コードを実行できます。"
    "計算やデータ処理が必要な場合は、まず launchPythonEnvironment で環境を起動し、"
    "次に runPythonCodeInRemoteEnvironment でコードを実行してください。"
    "コードの実行結果は必ず print() で出力するようにしてください。"
)


def chat_with_mcp(
    client: AzureOpenAI,
    model: str,
    mcp_tool: dict,
    user_message: str,
) -> str:
    """Responses API で MCP ツールを使ってメッセージを処理する"""
    print(f"\n{'='*60}")
    print(f"📝 ユーザー: {user_message}")
    print(f"{'='*60}")

    response = client.responses.create(
        model=model,
        instructions=SYSTEM_PROMPT,
        tools=[mcp_tool],
        input=user_message,
    )

    # レスポンスの出力を表示
    final_text = ""
    for item in response.output:
        if item.type == "mcp_list_tools":
            tool_names = [t.name for t in item.tools]
            print(f"\n🔍 MCP ツール検出: {', '.join(tool_names)}")
        elif item.type == "mcp_call":
            print(f"\n🔧 MCP ツール呼び出し: {item.name}")
            print(f"   サーバー: {item.server_label}")
            if hasattr(item, "arguments") and item.arguments:
                args_preview = item.arguments[:200]
                print(f"   引数: {args_preview}{'...' if len(item.arguments) > 200 else ''}")
        elif item.type == "message":
            for content in item.content:
                if content.type == "output_text":
                    print(f"\n🤖 GPT: {content.text}")
                    final_text += content.text

    return final_text


def run_demo(
    client: AzureOpenAI,
    model: str,
    mcp_tool: dict,
):
    """デモ用の質問を実行する"""
    examples = [
        "2の20乗を計算してください",
        "1から100までの素数をすべて表示してください",
        "pandasを使って、日本の主要5都市（東京、大阪、名古屋、札幌、福岡）の人口データを作成し、人口の多い順にソートして表示してください",
    ]

    for example in examples:
        chat_with_mcp(
            client=client,
            model=model,
            mcp_tool=mcp_tool,
            user_message=example,
        )


def run_interactive(
    client: AzureOpenAI,
    model: str,
    mcp_tool: dict,
):
    """対話モードで実行する"""
    print("\n💬 対話モードを開始します。'quit' または 'exit' で終了します。")
    print("   質問を入力してください。GPT が MCP 経由でコードを実行して回答します。\n")

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

        chat_with_mcp(
            client=client,
            model=model,
            mcp_tool=mcp_tool,
            user_message=user_input,
        )


def main():
    # .env ファイルを読み込み
    load_dotenv()

    # 環境変数の取得
    mcp_endpoint = os.getenv("MCP_ENDPOINT")
    mcp_api_key = os.getenv("MCP_API_KEY")
    azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_openai_key = os.getenv("AZURE_OPENAI_API_KEY")
    azure_openai_model = os.getenv("AZURE_OPENAI_MODEL", "gpt-4o")

    # 必須環境変数のチェック
    if not mcp_endpoint:
        print("❌ MCP_ENDPOINT が設定されていません。.env ファイルを確認してください。")
        sys.exit(1)
    if not mcp_api_key:
        print("❌ MCP_API_KEY が設定されていません。.env ファイルを確認してください。")
        sys.exit(1)
    if not azure_openai_endpoint:
        print("❌ AZURE_OPENAI_ENDPOINT が設定されていません。.env ファイルを確認してください。")
        sys.exit(1)
    if not azure_openai_key:
        print("❌ AZURE_OPENAI_API_KEY が設定されていません。.env ファイルを確認してください。")
        sys.exit(1)

    # Azure OpenAI クライアントの初期化（Responses API 対応バージョン）
    client = AzureOpenAI(
        azure_endpoint=azure_openai_endpoint,
        api_key=azure_openai_key,
        api_version="2025-04-01-preview",
    )

    # MCP ツール定義を作成
    mcp_tool = create_mcp_tool(mcp_endpoint, mcp_api_key)

    print(f"🚀 Azure OpenAI Responses API + MCP サンプル")
    print(f"🔗 Azure OpenAI モデル: {azure_openai_model}")
    print(f"🌐 MCP エンドポイント: {mcp_endpoint[:60]}...")

    # コマンドライン引数で対話モードを判定
    interactive = "--interactive" in sys.argv or "-i" in sys.argv

    if interactive:
        run_interactive(
            client=client,
            model=azure_openai_model,
            mcp_tool=mcp_tool,
        )
    else:
        run_demo(
            client=client,
            model=azure_openai_model,
            mcp_tool=mcp_tool,
        )

    print(f"\n{'='*60}")
    print("✅ 完了！")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
