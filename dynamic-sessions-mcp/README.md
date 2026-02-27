# Azure Container Apps 動的セッション MCP ハンズオン

このハンズオンでは、Azure Container Apps の動的セッションを **MCP (Model Context Protocol) サーバー** として利用する方法を学びます。プラットフォーム管理の MCP サーバーを有効にしたセッションプールを作成し、Streamable HTTP 経由でリモート Python コード実行を体験します。

## 📖 MCP (Model Context Protocol) とは？

**MCP (Model Context Protocol)** は、LLM（大規模言語モデル）と外部のツールやデータソースを接続するための **オープンな標準プロトコル** です。Anthropic が 2024 年に提唱し、急速に普及が進んでいます。

### MCP が解決する課題

従来、AI ツールが外部のサービスと連携するには、サービスごとに個別の実装（REST API クライアント、認証処理、レスポンスのパースなど）が必要でした。MCP はこれを **共通のプロトコル** で標準化します。

```
従来:  AI ツール ──(個別実装)──→ サービスA
       AI ツール ──(個別実装)──→ サービスB
       AI ツール ──(個別実装)──→ サービスC

MCP:   AI ツール ──(MCP)──→ MCP サーバーA
       AI ツール ──(MCP)──→ MCP サーバーB
       AI ツール ──(MCP)──→ MCP サーバーC
```

### MCP の構成要素

| 要素 | 役割 |
|------|------|
| **MCP ホスト** | AI ツール側（GitHub Copilot、Claude Desktop など） |
| **MCP クライアント** | ホスト内で動作し、MCP サーバーと通信するコンポーネント |
| **MCP サーバー** | 外部ツール・データソースを MCP プロトコルで提供するサーバー |

### このハンズオンでの MCP

Azure Container Apps の動的セッションは **プラットフォーム管理の MCP サーバー** を提供します。自分で MCP サーバーのコードを書く必要はなく、ARM テンプレートで MCP を有効にするだけで、MCP 対応のクライアント（GitHub Copilot など）からすぐに接続できます。

> **🔗 参考**: [MCP 公式サイト](https://modelcontextprotocol.io/) | [MCP 仕様](https://spec.modelcontextprotocol.io/)

## 💡 このハンズオンで体験すること

通常の動的セッションは REST API でコードを実行しますが、MCP 対応のセッションプールでは **Streamable HTTP** トランスポート上で **JSON-RPC 2.0** メッセージをやり取りしてコードを実行できます。これにより、GitHub Copilot や MCP 対応の AI ツールから直接接続できるようになります。

プラットフォームが提供するビルトインツール：

| ツール | 説明 |
|--------|------|
| `launchPythonEnvironment` | 新しい環境を作成し `environmentId` を返す |
| `runPythonCodeInRemoteEnvironment` | 既存の環境で Python コードを実行する |

## 📋 目次

1. [前提条件](#-前提条件)
2. [Step 1: MCP 対応セッションプールの作成](#step-1-mcp-対応セッションプールの作成約3分)
3. [Step 2: MCP エンドポイントと API キーの取得](#step-2-mcp-エンドポイントと-api-キーの取得約2分)
4. [Step 3: MCP サーバーの初期化とコード実行](#step-3-mcp-サーバーの初期化とコード実行約5分)
5. [Step 4: GitHub Copilot との連携（オプション）](#step-4-github-copilot-との連携オプション約5分)
6. [クリーンアップ](#-クリーンアップ)

**⏱️ 所要時間**: 約15分

## 🔧 前提条件

- **ルート README の Step 1（環境のセットアップ）が完了していること**
- Azure サブスクリプションを保有していること
- Azure CLI がインストールされていること
- `curl`、`jq` が利用可能であること（DevContainer / Codespaces では導入済み）

## 📚 参考URL

- [Tutorial: Use MCP with dynamic sessions (Python) | Microsoft Learn](https://learn.microsoft.com/en-us/azure/container-apps/sessions-tutorial-python-mcp)
- [MCP servers on Azure Container Apps overview | Microsoft Learn](https://learn.microsoft.com/en-us/azure/container-apps/mcp-overview)

---

## Step 1: MCP 対応セッションプールの作成（約3分）

MCP サーバーを有効にするには、ARM テンプレートでのデプロイが必要です（Azure CLI の `az containerapp sessionpool create` では `mcpServerSettings` を設定できません）。

> **📝 注意**: ルート README で作成したセッションプール（`my-session-pool`）とは別に、MCP 対応の新しいセッションプールを作成します。

### 1.1 環境変数を設定

ルート README で設定した変数に加え、MCP 用のセッションプール名を設定します：

```bash
MCP_SESSION_POOL_NAME="my-session-pool-mcp"
```

### 1.2 ARM テンプレートを確認

このプロジェクトにはデプロイ用の ARM テンプレートが含まれています：

```bash
cat dynamic-sessions-mcp/deploy.json
```

テンプレートのポイント：

- `containerType: "PythonLTS"` — Python ランタイムを使用
- `mcpServerSettings.isMCPServerEnabled: true` — プラットフォーム管理の MCP エンドポイントを有効化
- `coolDownPeriodInSeconds: 300` — 5分間の非アクティブ後にセッションを破棄

### 1.3 ARM テンプレートをデプロイ

```bash
az deployment group create \
    --resource-group $RESOURCE_GROUP \
    --template-file dynamic-sessions-mcp/deploy.json \
    --parameters name=$MCP_SESSION_POOL_NAME location=$LOCATION
```

**✅ 期待される結果**: `"provisioningState": "Succeeded"` が表示されること（作成に1-2分かかります）

### 1.4 ロールを割り当て

MCP セッションプールにも **Azure ContainerApps Session Executor** ロールが必要です：

```bash
MCP_POOL_ID=$(az containerapp sessionpool show \
    --name $MCP_SESSION_POOL_NAME \
    --resource-group $RESOURCE_GROUP \
    --query id -o tsv)

USER_OBJECT_ID=$(az ad signed-in-user show --query id -o tsv)

az role assignment create \
    --role "Azure ContainerApps Session Executor" \
    --assignee-object-id "$USER_OBJECT_ID" \
    --assignee-principal-type User \
    --scope "$MCP_POOL_ID"
```

**✅ 期待される結果**: `"roleDefinitionName": "Azure ContainerApps Session Executor"` が表示されること

---

## Step 2: MCP エンドポイントと API キーの取得（約2分）

MCP サーバーは通常の Dynamic Sessions API とは異なる認証方式を使います。Bearer トークンではなく **API キー** (`x-ms-apikey` ヘッダー) で認証します。

### 2.1 MCP エンドポイントを取得

```bash
MCP_ENDPOINT=$(az rest --method GET \
    --uri "https://management.azure.com/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.App/sessionPools/$MCP_SESSION_POOL_NAME" \
    --uri-parameters api-version=2025-02-02-preview \
    --query "properties.mcpServerSettings.mcpServerEndpoint" -o tsv)
echo "MCP Endpoint: $MCP_ENDPOINT"
```

**✅ 期待される結果**: `https://xxxx.dynamicsessions.io/...` のような URL が表示されること

### 2.2 API キーを取得

```bash
API_KEY=$(az rest --method POST \
    --uri "https://management.azure.com/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.App/sessionPools/$MCP_SESSION_POOL_NAME/fetchMCPServerCredentials" \
    --uri-parameters api-version=2025-02-02-preview \
    --query "apiKey" -o tsv)
echo "API Key: ${API_KEY:0:8}..."
```

**✅ 期待される結果**: API キーの先頭8文字が表示されること

> **⚠️ 注意**: API キーはシークレットとして扱ってください。ソースコードにコミットしたり、外部に共有しないでください。

---

## Step 3: MCP サーバーの初期化とコード実行（約5分）

MCP サーバーとの通信は **Streamable HTTP** トランスポート上で **JSON-RPC 2.0** メッセージをやり取りします。`curl` で HTTP POST リクエストを送信し、JSON-RPC 形式のリクエスト/レスポンスで MCP ツールを呼び出します。

### 3.1 MCP サーバーを初期化

`initialize` リクエストで MCP 接続を確立します：

```bash
curl -sS -X POST "$MCP_ENDPOINT" \
    -H "Content-Type: application/json" \
    -H "x-ms-apikey: $API_KEY" \
    -d '{ "jsonrpc": "2.0", "id": "1", "method": "initialize" }' | jq .
```

**✅ 期待される結果**:

```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "result": {
    "protocolVersion": "2025-03-26",
    "serverInfo": {
      "name": "Microsoft Container Apps MCP Server",
      ...
    },
    "capabilities": {
      "tools": { "call": true, "list": true }
    }
  }
}
```

### 3.2 利用可能なツール一覧を確認

```bash
curl -sS -X POST "$MCP_ENDPOINT" \
    -H "Content-Type: application/json" \
    -H "x-ms-apikey: $API_KEY" \
    -d '{ "jsonrpc": "2.0", "id": "2", "method": "tools/list" }' | jq '.result.tools[].name'
```

**✅ 期待される結果**: `launchPythonEnvironment`、`runPythonCodeInRemoteEnvironment` が表示されること

### 3.3 Python 環境を起動

`launchPythonEnvironment` ツールで新しい環境を作成します：

```bash
ENVIRONMENT_RESPONSE=$(curl -sS -X POST "$MCP_ENDPOINT" \
    -H "Content-Type: application/json" \
    -H "x-ms-apikey: $API_KEY" \
    -d '{ "jsonrpc": "2.0", "id": "3", "method": "tools/call", "params": { "name": "launchPythonEnvironment", "arguments": {} } }')

echo "$ENVIRONMENT_RESPONSE" | jq .
```

レスポンスから `environmentId` を取得します：

```bash
ENVIRONMENT_ID=$(echo "$ENVIRONMENT_RESPONSE" | jq -r '.result.structuredContent.environmentId')
echo "Environment ID: $ENVIRONMENT_ID"
```

**✅ 期待される結果**: 環境 ID（UUID）が表示されること

> **💡 ポイント**: `launchPythonEnvironment` は環境 ID を生成するだけで、実際のコンテナは最初のコマンド実行時に「遅延割り当て」されます。

### 3.4 Python コードを実行

取得した `environmentId` を使って Python コードを実行します：

```bash
curl -sS -X POST "$MCP_ENDPOINT" \
    -H "Content-Type: application/json" \
    -H "x-ms-apikey: $API_KEY" \
    -d '{
        "jsonrpc": "2.0",
        "id": "4",
        "method": "tools/call",
        "params": {
            "name": "runPythonCodeInRemoteEnvironment",
            "arguments": {
                "environmentId": "'"$ENVIRONMENT_ID"'",
                "pythonCode": "import sys; print(f\"Python {sys.version}\")"
            }
        }
    }' | jq .
```

**✅ 期待される結果**: `stdout` に Python バージョンが表示されること

### 3.5 より複雑なコードを実行

```bash
curl -sS -X POST "$MCP_ENDPOINT" \
    -H "Content-Type: application/json" \
    -H "x-ms-apikey: $API_KEY" \
    -d '{
        "jsonrpc": "2.0",
        "id": "5",
        "method": "tools/call",
        "params": {
            "name": "runPythonCodeInRemoteEnvironment",
            "arguments": {
                "environmentId": "'"$ENVIRONMENT_ID"'",
                "pythonCode": "import math\nresults = {n: math.factorial(n) for n in range(1, 11)}\nfor k, v in results.items():\n    print(f\"{k}! = {v}\")"
            }
        }
    }' | jq .
```

**✅ 期待される結果**: 1! から 10! までの階乗が表示されること

---

## Step 4: GitHub Copilot との連携（オプション、約5分）

MCP サーバーを GitHub Copilot に接続して、自然言語でコード実行環境を操作できます。

### 4.1 MCP 設定ファイルを作成

プロジェクトルートに `.vscode/mcp.json` を作成します：

```bash
mkdir -p .vscode
cat <<EOF > .vscode/mcp.json
{
    "servers": {
        "aca-python-sessions": {
            "type": "http",
            "url": "$MCP_ENDPOINT",
            "headers": {
                "x-ms-apikey": "$API_KEY"
            }
        }
    }
}
EOF
```

> **⚠️ 注意**: `.vscode/mcp.json` には API キーが含まれます。`.gitignore` に追加して、ソースコードにコミットしないようにしてください。

### 4.2 MCP サーバーを起動

`.vscode/mcp.json` を作成しただけでは MCP サーバーは接続されません。以下の手順で起動してください：

1. VS Code で `.vscode/mcp.json` ファイルを開く
2. `"aca-python-sessions"` の上に表示される **「Start」ボタン**（▶）をクリックして MCP サーバーを起動する
3. ステータスが「Running」になったことを確認する

> **💡 ポイント**: `mcp.json` を開くと、各サーバー定義の上にインラインで「Start」ボタンが表示されます。これをクリックしないと Copilot Chat からツールを利用できません。

### 4.3 Copilot Chat で確認

1. VS Code で **Copilot Chat** を **Agent モード** で開く
2. ツールリストに `aca-python-sessions` が表示されていることを確認

### 4.4 試してみる

Copilot Chat で以下のようなプロンプトを試してみてください：

- `Python環境を起動して、フィボナッチ数列の最初の20項を計算してください`
- `Pythonスクリプトを実行して、https://api.github.com のレスポンスヘッダーを表示してください`
- `pandasをインポートして、簡単なデータ分析のサンプルを実行してください`

> **💡 ポイント**: Copilot が自動的に `launchPythonEnvironment` → `runPythonCodeInRemoteEnvironment` のツール呼び出しを行い、結果を元に回答を生成します。

---

## 🧹 クリーンアップ

MCP 用セッションプールのみを削除する場合：

```bash
az containerapp sessionpool delete \
    --name $MCP_SESSION_POOL_NAME \
    --resource-group $RESOURCE_GROUP \
    --yes
```

すべてのリソース（ルートハンズオンで作成したものも含む）を削除する場合は、ルート README のクリーンアップ手順を参照してください：

```bash
az group delete --resource-group $RESOURCE_GROUP --yes --no-wait
```

---

## 🎉 おめでとうございます！

動的セッションを MCP サーバーとして利用するハンズオンを完了しました。

### 学んだこと

- ✅ ARM テンプレートで MCP 対応セッションプールを作成
- ✅ MCP エンドポイントと API キーの取得
- ✅ Streamable HTTP + JSON-RPC 2.0 による MCP サーバーの初期化とツール呼び出し
- ✅ リモート環境での Python コード実行
- ✅ GitHub Copilot との MCP 連携

### 通常の Dynamic Sessions との違い

| 項目 | 通常の Dynamic Sessions | MCP 対応 |
|------|------------------------|----------|
| 認証 | Bearer トークン | API キー (`x-ms-apikey`) |
| プロトコル | REST API | Streamable HTTP + JSON-RPC 2.0 (MCP) |
| 作成方法 | Azure CLI | ARM テンプレート |
| ツール連携 | 独自実装が必要 | MCP 対応ツール（Copilot 等）と直接接続可能 |

### 次のステップ

- [MCP servers on Azure Container Apps overview](https://learn.microsoft.com/en-us/azure/container-apps/mcp-overview)
- [Secure MCP servers on Container Apps](https://learn.microsoft.com/en-us/azure/container-apps/mcp-authentication)
- [Azure Container Apps Sessions のドキュメント](https://learn.microsoft.com/ja-jp/azure/container-apps/sessions)
