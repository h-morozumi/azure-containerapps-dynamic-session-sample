# Azure Container Apps 動的セッション × Azure OpenAI ハンズオン (GPT Code Interpreter)

このハンズオンでは、Azure Container Apps の動的セッションを **Azure OpenAI の Function Calling によるコード実行ツール** として活用する方法を学びます。GPT モデルが必要に応じて Python コードを生成し、動的セッションのサンドボックス環境で安全に実行する仕組みを体験します。

## 💡 このサンプルの概要

Azure OpenAI の **Function Calling** を使って、GPT モデルに「Python コード実行」ツールを与えます。GPT がユーザーの質問に答えるためにコードの実行が必要と判断すると、動的セッションにコードを送信して実行し、その結果を使って回答を生成します。

```
ユーザー → Azure OpenAI (GPT) → [Function Calling] → Dynamic Sessions → [実行結果] → GPT → 回答
```

## 📋 目次

1. [前提条件](#-前提条件)
2. [Step 1: Azure OpenAI リソースの準備](#step-1-azure-openai-リソースの準備約5分)
3. [Step 2: セッションプールの管理エンドポイントを取得](#step-2-セッションプールの管理エンドポイントを取得約1分)
4. [Step 3: 環境変数の設定](#step-3-環境変数の設定約2分)
5. [Step 4: プロジェクトのセットアップ](#step-4-プロジェクトのセットアップ約2分)
6. [Step 5: サンプルの実行](#step-5-サンプルの実行約5分)
7. [動作の仕組み](#-動作の仕組み)
8. [クリーンアップ](#-クリーンアップ)

**⏱️ 所要時間**: 約15分（セッションプール作成済みの場合）

## 🔧 前提条件

- **ルート README の Step 1〜3 が完了していること**（セッションプール作成、ロール割り当て済み）
- Azure サブスクリプションを保有していること
- Azure CLI がインストールされていること

## 📚 参考URL

- [Azure OpenAI Service の Function Calling | Microsoft Learn](https://learn.microsoft.com/ja-jp/azure/ai-services/openai/how-to/function-calling)
- [Azure Container Apps Sessions のドキュメント | Microsoft Learn](https://learn.microsoft.com/ja-jp/azure/container-apps/sessions)
- [Azure OpenAI Service の概要 | Microsoft Learn](https://learn.microsoft.com/ja-jp/azure/ai-services/openai/overview)

---

## Step 1: Azure OpenAI リソースの準備（約5分）

> **💡 既に Azure OpenAI リソースをお持ちの場合**: GPT-4o モデルがデプロイされていれば、このステップはスキップして Step 2 に進んでください。

### 1.1 環境変数を設定

ルート README で設定した変数に加え、以下を設定します：

```bash
OPENAI_NAME="openai-sessions-demo"
OPENAI_LOCATION="eastus2"
```

> **📝 注意**: Azure OpenAI の利用可能リージョンは限られています。`eastus2`、`swedencentral`、`westus3` などが一般的に利用可能です。

### 1.2 Azure OpenAI リソースを作成

```bash
az cognitiveservices account create \
  --name $OPENAI_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $OPENAI_LOCATION \
  --kind OpenAI \
  --sku S0
```

**✅ 期待される結果**: `"provisioningState": "Succeeded"` が表示されること

### 1.3 GPT-4o モデルをデプロイ

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

### 1.4 エンドポイントと API キーを取得

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

## Step 2: セッションプールの管理エンドポイントを取得（約1分）

ルート README で作成したセッションプールの管理エンドポイントを取得します：

```bash
POOL_ENDPOINT=$(az containerapp sessionpool show \
  --name $SESSION_POOL_NAME \
  --resource-group $RESOURCE_GROUP \
  --query properties.poolManagementEndpoint -o tsv)
echo "Pool Endpoint: $POOL_ENDPOINT"
```

**✅ 期待される結果**: `https://xxxx.dynamicsessions.io` のような URL が表示されること

---

## Step 3: 環境変数の設定（約2分）

### 3.1 gpt-code-interpreter ディレクトリに移動

```bash
cd gpt-code-interpreter
```

### 3.2 .env ファイルを作成

```bash
cat <<EOF > .env
POOL_ENDPOINT=$POOL_ENDPOINT
AZURE_OPENAI_ENDPOINT=$AZURE_OPENAI_ENDPOINT
AZURE_OPENAI_API_KEY=$AZURE_OPENAI_API_KEY
AZURE_OPENAI_MODEL=gpt-4o
EOF
```

### 3.3 設定を確認

```bash
cat .env
```

**✅ 期待される結果**: 4つの環境変数がすべて設定されていること

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

**✅ 期待される結果**: GPT がコードを生成し、動的セッションで実行され、結果に基づいた回答が表示されること

### 実行例

以下のような流れで処理が進みます：

```
🚀 セッション ID: gpt-demo-a1b2c3d4
🔗 Azure OpenAI モデル: gpt-4o

============================================================
📝 ユーザー: 2の20乗を計算してください
============================================================

🔧 GPT がコードを生成しました:
  result = 2 ** 20
  print(f"2の20乗 = {result}")

📊 実行結果: 2の20乗 = 1048576

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
- `matplotlibでsin関数のグラフを描画するコードを実行してください`

> **💡 ヒント**: GPT は質問の内容に応じて、Python コードの実行が必要かどうかを自動的に判断します。単純な質問にはコード実行なしで回答し、計算やデータ処理が必要な場合にのみコードを実行します。

---

## 🔍 動作の仕組み

このサンプルは以下の流れで動作します：

```
1. ユーザーが質問を入力
       ↓
2. Azure OpenAI (GPT-4o) が質問を分析
       ↓
3. コード実行が必要？
   ├─ Yes → GPT が Python コードを生成
   │         ↓
   │    Dynamic Sessions REST API にコードを送信
   │         ↓
   │    サンドボックスでコードを実行
   │         ↓
   │    実行結果を GPT に返却
   │         ↓
   │    GPT が結果を元に回答を生成
   │
   └─ No → GPT が直接回答
```

### ツール定義（Function Calling）

GPT には以下のツールが定義されています：

```json
{
  "type": "function",
  "function": {
    "name": "execute_python_code",
    "description": "クラウド上の安全なサンドボックスで Python コードを実行します",
    "parameters": {
      "type": "object",
      "properties": {
        "code": {
          "type": "string",
          "description": "実行する Python コード"
        }
      },
      "required": ["code"]
    }
  }
}
```

GPT がこのツールを呼び出すと、`main.py` が Dynamic Sessions REST API にコードを送信して実行結果を取得します。

### Function Calling × Dynamic Sessions の利点

- **ツールの提供**: Dynamic Sessions が「Python コード実行」ツールを GPT に提供
- **LLM の判断**: GPT がいつコード実行が必要かを自動判断
- **安全な実行**: コードはクラウド上のサンドボックスで隔離実行（ローカル環境に影響なし）
- **結果の活用**: 実行結果を元に GPT が自然言語で最終回答を生成

---

## 🧹 クリーンアップ

> **⚠️ 注意**: ルート README のクリーンアップ（`az group delete`）を実行すると、このハンズオンで作成した Azure OpenAI リソースも含めて削除されます。

Azure OpenAI リソースのみを削除する場合：

```bash
az cognitiveservices account delete \
  --name $OPENAI_NAME \
  --resource-group $RESOURCE_GROUP
```

すべてのリソースを削除する場合は、ルート README のクリーンアップ手順を参照してください。

---

## 🎉 おめでとうございます！

動的セッションを AI のコード実行ツールとして活用するハンズオンを完了しました。

### 学んだこと

- ✅ Azure OpenAI リソースの作成とモデルのデプロイ
- ✅ 動的セッションを Function Calling のツールとして定義
- ✅ GPT によるコード生成と動的セッションでの実行
- ✅ Function Calling × Dynamic Sessions による AI コード実行の連携

### 次のステップ

- [Azure Container Apps Sessions のドキュメント](https://learn.microsoft.com/ja-jp/azure/container-apps/sessions)
- [Azure OpenAI Service の Function Calling](https://learn.microsoft.com/ja-jp/azure/ai-services/openai/how-to/function-calling)
