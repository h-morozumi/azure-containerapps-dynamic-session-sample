# Azure Container Apps 動的セッション × Azure OpenAI Responses API + MCP ハンズオン

このハンズオンでは、Azure OpenAI の **Responses API** と **MCP (Model Context Protocol)** を組み合わせ、動的セッションをコード実行ツールとして活用する方法を学びます。Responses API が MCP サーバーと直接通信するため、ツール呼び出しのコードを自分で書く必要がありません。

## 💡 このサンプルの概要

Azure OpenAI の **Responses API** は、MCP サーバーをネイティブにサポートしています。MCP エンドポイントを指定するだけで、API がツールの検出・呼び出し・結果の取得をすべてサーバーサイドで処理します。

```
ユーザー → Azure OpenAI (Responses API) ←── MCP ──→ Dynamic Sessions → 回答
```

### `gpt-code-interpreter` との違い

| 項目 | gpt-code-interpreter | gpt-mcp-interpreter (本サンプル) |
|------|---------------------|--------------------------------|
| API | Chat Completions + Function Calling | **Responses API** + MCP |
| コード実行の仕組み | 自前でREST API呼び出しを実装 | **API がMCPサーバーに直接通信** |
| ツール定義 | 自分で関数を定義 | **MCP サーバーから自動検出** |
| 認証 | Bearer トークン（Azure AD） | **API キー**（x-ms-apikey） |
| 依存パッケージ | openai, httpx, azure-identity | **openai のみ** |
| コード量 | ツール呼び出しループの実装が必要 | **約半分**（API が自動処理） |

## 📋 目次

1. [前提条件](#-前提条件)
2. [Step 1: MCP エンドポイントと API キーの確認](#step-1-mcp-エンドポイントと-api-キーの確認約1分)
3. [Step 2: Azure OpenAI リソースの準備](#step-2-azure-openai-リソースの準備約5分)
4. [Step 3: 環境変数の設定](#step-3-環境変数の設定約2分)
5. [Step 4: プロジェクトのセットアップ](#step-4-プロジェクトのセットアップ約2分)
6. [Step 5: サンプルの実行](#step-5-サンプルの実行約5分)
7. [動作の仕組み](#-動作の仕組み)
8. [クリーンアップ](#-クリーンアップ)

**⏱️ 所要時間**: 約15分（MCP セッションプール・Azure OpenAI リソース作成済みの場合）

## 🔧 前提条件

- **`dynamic-sessions-mcp` ハンズオンの Step 1〜2 が完了していること**（MCP 対応セッションプール作成、エンドポイントと API キー取得済み）
- Azure OpenAI リソースと GPT-4o モデルがデプロイ済みであること（未作成の場合は Step 2 で作成します）
- Azure CLI がインストールされていること

## 📚 参考URL

- [Azure OpenAI Service の Responses API | Microsoft Learn](https://learn.microsoft.com/ja-jp/azure/ai-services/openai/how-to/responses)
- [MCP servers on Azure Container Apps overview | Microsoft Learn](https://learn.microsoft.com/en-us/azure/container-apps/mcp-overview)
- [MCP 公式サイト](https://modelcontextprotocol.io/)

---

## Step 1: MCP エンドポイントと API キーの確認（約1分）

`dynamic-sessions-mcp` ハンズオンで取得した MCP エンドポイントと API キーを使用します。

まだ取得していない場合は、以下のコマンドで取得してください：

```bash
# MCP エンドポイント
MCP_ENDPOINT=$(az rest --method GET \
    --uri "https://management.azure.com/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.App/sessionPools/$MCP_SESSION_POOL_NAME" \
    --uri-parameters api-version=2025-02-02-preview \
    --query "properties.mcpServerSettings.mcpServerEndpoint" -o tsv)
echo "MCP Endpoint: $MCP_ENDPOINT"

# API キー
API_KEY=$(az rest --method POST \
    --uri "https://management.azure.com/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.App/sessionPools/$MCP_SESSION_POOL_NAME/fetchMCPServerCredentials" \
    --uri-parameters api-version=2025-02-02-preview \
    --query "apiKey" -o tsv)
echo "API Key: ${API_KEY:0:8}..."
```

**✅ 期待される結果**: MCP エンドポイント URL と API キーが表示されること

---

## Step 2: Azure OpenAI リソースの準備（約5分）

> **💡 既に Azure OpenAI リソースをお持ちの場合**: GPT-4o モデルがデプロイされていれば、このステップはスキップして Step 3 に進んでください。`gpt-code-interpreter` ハンズオンで作成済みの場合も同様です。

### 2.1 環境変数を設定

```bash
OPENAI_NAME="openai-sessions-demo"
OPENAI_LOCATION="eastus2"
```

> **📝 注意**: Azure OpenAI の利用可能リージョンは限られています。`eastus2`、`swedencentral`、`westus3` などが一般的に利用可能です。

### 2.2 Azure OpenAI リソースを作成

```bash
az cognitiveservices account create \
  --name $OPENAI_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $OPENAI_LOCATION \
  --kind OpenAI \
  --sku S0
```

**✅ 期待される結果**: `"provisioningState": "Succeeded"` が表示されること

### 2.3 GPT-4o モデルをデプロイ

```bash
az cognitiveservices account deployment create \
  --name $OPENAI_NAME \
  --resource-group $RESOURCE_GROUP \
  --deployment-name gpt-4o \
  --model-name gpt-4o \
  --model-version "2024-11-20" \
  --model-format OpenAI \
  --sku-capacity 10 \
  --sku-name GlobalStandard
```

**✅ 期待される結果**: デプロイが正常に作成されること

> **⚠️ エラーが出た場合**: `--model-version` を変更してみてください。利用可能なバージョンは以下のコマンドで確認できます：
>
> ```bash
> az cognitiveservices account list-models \
>   --name $OPENAI_NAME \
>   --resource-group $RESOURCE_GROUP \
>   --query "[?name=='gpt-4o'].{name:name, version:version}" -o table
> ```

### 2.4 エンドポイントと API キーを取得

```bash
AZURE_OPENAI_ENDPOINT=$(az cognitiveservices account show \
  --name $OPENAI_NAME \
  --resource-group $RESOURCE_GROUP \
  --query properties.endpoint -o tsv)
echo "Endpoint: $AZURE_OPENAI_ENDPOINT"

AZURE_OPENAI_API_KEY=$(az cognitiveservices account keys list \
  --name $OPENAI_NAME \
  --resource-group $RESOURCE_GROUP \
  --query key1 -o tsv)
echo "API Key: ${AZURE_OPENAI_API_KEY:0:8}..."
```

**✅ 期待される結果**: エンドポイント URL と API キーが表示されること

---

## Step 3: 環境変数の設定（約2分）

### 3.1 gpt-mcp-interpreter ディレクトリに移動

```bash
cd gpt-mcp-interpreter
```

### 3.2 .env ファイルを作成

```bash
cat <<EOF > .env
MCP_ENDPOINT=$MCP_ENDPOINT
MCP_API_KEY=$API_KEY
AZURE_OPENAI_ENDPOINT=$AZURE_OPENAI_ENDPOINT
AZURE_OPENAI_API_KEY=$AZURE_OPENAI_API_KEY
AZURE_OPENAI_MODEL=gpt-4o
EOF
```

### 3.3 設定を確認

```bash
cat .env
```

**✅ 期待される結果**: 5つの環境変数がすべて設定されていること

---

## Step 4: プロジェクトのセットアップ（約2分）

### 4.1 依存関係をインストール

```bash
uv sync
```

**✅ 期待される結果**: パッケージが正常にインストールされること

---

## Step 5: サンプルの実行（約5分）

### 5.1 サンプルを実行

```bash
uv run main.py
```

**✅ 期待される結果**: GPT が MCP 経由でツールを自動検出し、コードを実行して回答が表示されること

### 実行例

以下のような流れで処理が進みます：

```
🚀 Azure OpenAI Responses API + MCP サンプル
🔗 Azure OpenAI モデル: gpt-4o
🌐 MCP エンドポイント: https://xxxx.dynamicsessions.io/...

============================================================
📝 ユーザー: 2の20乗を計算してください
============================================================

🔍 MCP ツール検出: launchPythonEnvironment, runPythonCodeInRemoteEnvironment
🔧 MCP ツール呼び出し: launchPythonEnvironment
   サーバー: aca-python-sessions
🔧 MCP ツール呼び出し: runPythonCodeInRemoteEnvironment
   サーバー: aca-python-sessions
   引数: {"environmentId": "...", "pythonCode": "result = 2 ** 20\nprint(f\"2の20乗 = {result}\")"}

🤖 GPT: 2の20乗は **1,048,576** です。
```

### 5.2 対話モードで実行（オプション）

自分で質問を入力して試すこともできます：

```bash
uv run main.py --interactive
```

対話モードでは、以下のような質問を試してみてください：

- `フィボナッチ数列の最初の20項を表示してください`
- `今日の日付から100日後は何月何日ですか？`
- `1から1000までの数で、3と5の両方で割り切れる数の合計を求めてください`
- `pandasを使って簡単なデータ分析のサンプルを実行してください`

> **💡 ヒント**: Responses API が MCP サーバーからツール一覧を自動検出するため、ツール定義を自分で書く必要がありません。MCP サーバー側でツールが追加されれば、コード変更なしで利用できます。

---

## 🔍 動作の仕組み

### Responses API + MCP のアーキテクチャ

```
1. ユーザーが質問を入力
       ↓
2. Azure OpenAI (Responses API) にリクエスト送信
   ※ MCP サーバーの URL と API キーを指定
       ↓
3. Responses API が MCP サーバーからツール一覧を取得（tools/list）
       ↓
4. GPT がツール呼び出しを決定
       ↓
5. Responses API が MCP サーバーにツール呼び出しを実行（tools/call）
   ├─ launchPythonEnvironment → 環境 ID を取得
   └─ runPythonCodeInRemoteEnvironment → コードを実行
       ↓
6. 実行結果を元に GPT が回答を生成
       ↓
7. 最終回答をクライアントに返却
```

### MCP ツール定義（main.py）

Responses API に渡す MCP ツール定義は非常にシンプルです：

```python
{
    "type": "mcp",
    "server_label": "aca-python-sessions",
    "server_url": "<MCP_ENDPOINT>",
    "headers": {
        "x-ms-apikey": "<API_KEY>"
    },
    "require_approval": "never"
}
```

この定義だけで、Responses API が以下をすべて自動処理します：
1. MCP サーバーに接続してツール一覧を取得
2. GPT の判断に基づいてツールを呼び出し
3. 実行結果を GPT にフィードバック

### Function Calling との違い

| 処理 | Function Calling (gpt-code-interpreter) | Responses API + MCP (本サンプル) |
|------|----------------------------------------|--------------------------------|
| ツール検出 | 手動で定義 | MCP サーバーから自動検出 |
| ツール呼び出し | クライアントが REST API を呼ぶ | API サーバーが MCP 経由で実行 |
| 結果の返却 | クライアントが手動で返す | API サーバーが自動で返す |
| ツール呼び出しループ | 自前で while ループを実装 | API が内部で処理 |

---

## 🧹 クリーンアップ

> **⚠️ 注意**: ルート README のクリーンアップ（`az group delete`）を実行すると、Azure OpenAI リソースと MCP セッションプールも含めて削除されます。

MCP セッションプールのみを削除する場合は `dynamic-sessions-mcp` のクリーンアップ手順を参照してください。

Azure OpenAI リソースのみを削除する場合：

```bash
az cognitiveservices account delete \
  --name $OPENAI_NAME \
  --resource-group $RESOURCE_GROUP
```

すべてのリソースを削除する場合は、ルート README のクリーンアップ手順を参照してください。

---

## 🎉 おめでとうございます！

Azure OpenAI Responses API + MCP で動的セッションを活用するハンズオンを完了しました。

### 学んだこと

- ✅ Responses API での MCP ツール定義
- ✅ MCP サーバーからのツール自動検出
- ✅ Responses API によるサーバーサイド MCP ツール呼び出し
- ✅ Function Calling との違いの理解

### 3つのハンズオンの比較

| ハンズオン | コード実行方式 | 特徴 |
|-----------|---------------|------|
| `code-interpreter` | REST API 直接呼び出し | シンプル、AI なし |
| `gpt-code-interpreter` | Function Calling + REST API | GPT がコード生成、自前でツール呼び出し |
| `gpt-mcp-interpreter` | **Responses API + MCP** | **GPT がコード生成、API が自動でツール呼び出し** |

### 次のステップ

- [Azure OpenAI Service の Responses API](https://learn.microsoft.com/ja-jp/azure/ai-services/openai/how-to/responses)
- [MCP servers on Azure Container Apps overview](https://learn.microsoft.com/en-us/azure/container-apps/mcp-overview)
- [MCP 公式サイト](https://modelcontextprotocol.io/)
