# Azure Container Apps 動的セッション ハンズオン

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/h-morozumi/azure-containerapps-dynamic-session-sample)
[![Open in VS Code Online](https://img.shields.io/badge/Open%20in-VS%20Code%20Online-blue?logo=visualstudiocode)](https://vscode.dev/github/h-morozumi/azure-containerapps-dynamic-session-sample)

> **💡 ヒント**: Fork せずに Codespaces で開いてもハンズオンは問題なく実行できます。Codespaces の利用は**開いたユーザー自身のアカウント**に課金されます（GitHub 無料枠: 120コア時間/月）。このハンズオンは約30分なので無料枠で十分です。
>
> **📝 Fork した場合**: 上記ボタンのURLを自分のリポジトリに変更するか、GitHub リポジトリページの「Code」→「Codespaces」から直接開いてください。

このハンズオンでは、[Azure Container Apps の動的セッション](https://learn.microsoft.com/ja-jp/azure/container-apps/sessions) を使用して、クラウド上で Python コードを実行する方法を学びます。

## 📋 目次

1. [前提条件](#-前提条件)
2. [Step 1: 環境のセットアップ](#step-1-環境のセットアップ約5分)
3. [Step 2: セッションプールの作成](#step-2-セッションプールの作成約3分)
4. [Step 3: ロールの割り当て](#step-3-ロールの割り当て約2分)
5. [Step 4: Python コードの実行](#step-4-python-コードの実行約10分)
6. [Step 5: REST API を使用した実行（オプション）](#step-5-rest-api-を使用した実行オプション)
7. [Step 6: セッションの管理](#step-6-セッションの管理)
8. [クリーンアップ](#-クリーンアップ)

**⏱️ 所要時間**: 約30分

## 🔧 前提条件

- Azure サブスクリプションを保有していること
- Azure CLI がインストールされていること

## 📚 参考URL

- [チュートリアル: Azure Container Apps を使用してセッション プールでシェル コマンドを実行する (プレビュー) | Microsoft Learn](https://learn.microsoft.com/ja-jp/azure/container-apps/sessions-tutorial-shell) 
- [az containerapp sessionpool | Microsoft Learn](https://learn.microsoft.com/en-us/cli/azure/containerapp/sessionpool?view=azure-cli-latest)

---

## Step 1: 環境のセットアップ（約5分）

### 1.1 Azure CLI を最新バージョンに更新

```bash
az upgrade
```

### 1.2 バージョンを確認

```bash
az version
```

**✅ 期待される結果**: `azure-cli` のバージョンが `2.60.0` 以上であること

### 1.3 Microsoft.App リソースプロバイダーを登録

```bash
az provider register --namespace Microsoft.App
```

### 1.4 Azure Container Apps CLI 拡張機能をインストール

```bash
az extension add --name containerapp --allow-preview true --upgrade
```

バージョンを確認します：

```bash
az version
```

**✅ 期待される結果**: `extensions` に `containerapp` が表示されること

```json
{
    "extensions": {
        "containerapp": "1.x.x"
    }
}
```

### 1.5 Azure にログイン

```bash
az login
```

> **💡 Codespaces / DevContainer で実行する場合**: ブラウザが開けない環境ではデバイスコードフローを使用してください。
>
> ```bash
> az login --use-device-code
> ```
>
> 表示されるコードを控え、ホストマシンのブラウザで https://microsoft.com/devicelogin を開いてコードを入力するとログインできます。

### 1.6 環境変数を設定

このハンズオンで使用する変数を設定します：

```bash
SUBSCRIPTION_ID=$(az account show --query id --output tsv)
RESOURCE_GROUP="rg-containerapps-sessions"
SESSION_POOL_NAME="my-session-pool"
LOCATION="eastus"
```

### 1.7 サブスクリプションを設定

```bash
az account set -s $SUBSCRIPTION_ID
```

### 1.8 リソースグループを作成

```bash
az group create --name $RESOURCE_GROUP --location $LOCATION
```

**✅ 期待される結果**: `"provisioningState": "Succeeded"` が表示されること

---

## Step 2: セッションプールの作成（約3分）

### 2.1 セッションプールを作成

```bash
az containerapp sessionpool create \
  --name $SESSION_POOL_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --container-type PythonLTS \
  --max-sessions 100 \
  --cooldown-period 300 \
  --network-status EgressEnabled
```

> **💡 パラメータの説明**:
> - `--container-type PythonLTS`: Python 環境を使用
> - `--max-sessions 100`: 最大同時セッション数
> - `--cooldown-period 300`: セッションが非アクティブ後に削除されるまでの秒数
> - `--network-status EgressEnabled`: インターネットへのアクセスを許可

**✅ 期待される結果**: `"provisioningState": "Succeeded"` が表示されること（作成に1-2分かかります）

### 2.2 セッションプールの状態を確認

```bash
az containerapp sessionpool show \
  --name $SESSION_POOL_NAME \
  --resource-group $RESOURCE_GROUP \
  --query "{name:name, state:properties.provisioningState, type:properties.containerType}"
```

**✅ 期待される結果**:

```json
{
  "name": "my-session-pool",
  "state": "Succeeded",
  "type": "PythonLTS"
}
```

---

## Step 3: ロールの割り当て（約2分）

セッションプールでコードを実行するには、**Azure ContainerApps Session Executor** ロールが必要です。

### 3.1 自分のオブジェクト ID を取得

```bash
USER_OBJECT_ID=$(az ad signed-in-user show --query id -o tsv)
echo "User Object ID: $USER_OBJECT_ID"
```

### 3.2 セッションプールのリソース ID を取得

```bash
POOL_ID=$(az containerapp sessionpool show \
  --name $SESSION_POOL_NAME \
  --resource-group $RESOURCE_GROUP \
  --query id -o tsv)
echo "Pool ID: $POOL_ID"
```

### 3.3 ロールを割り当て

```bash
az role assignment create \
  --role "Azure ContainerApps Session Executor" \
  --assignee-object-id "$USER_OBJECT_ID" \
  --assignee-principal-type User \
  --scope "$POOL_ID"
```

**✅ 期待される結果**: `"roleDefinitionName": "Azure ContainerApps Session Executor"` が表示されること

> ⚠️ **注意**: ロールの割り当てが反映されるまで **1〜5分** かかる場合があります。次のステップでエラーが出た場合は、少し待ってから再試行してください。

---

## Step 4: Python コードの実行（約10分）

### 4.1 Hello World を実行

```bash
az containerapp session code-interpreter execute \
  --name $SESSION_POOL_NAME \
  --resource-group $RESOURCE_GROUP \
  --code "print('Hello, Azure Container Apps Sessions')" \
  --identifier my-session-001
```

**✅ 期待される結果**:

```json
{
  "result": {
    "stdout": "Hello, Azure Container Apps Sessions\n",
    "stderr": "",
    "executionTimeInMilliseconds": xx
  },
  "status": "Succeeded"
}
```

> ❌ **401 エラーが出た場合**: ロールの割り当てがまだ反映されていません。1-2分待ってから再試行してください。

### 4.2 Python バージョンを確認

```bash
az containerapp session code-interpreter execute \
  --name $SESSION_POOL_NAME \
  --resource-group $RESOURCE_GROUP \
  --code "import sys; print(f'Python version: {sys.version}')" \
  --identifier my-session-001
```

**✅ 期待される結果**: Python 3.12.x が表示されること

### 4.3 数学計算を実行

```bash
az containerapp session code-interpreter execute \
  --name $SESSION_POOL_NAME \
  --resource-group $RESOURCE_GROUP \
  --code "
import math
radius = 5
area = math.pi * radius ** 2
print(f'半径 {radius} の円の面積: {area:.2f}')
" \
  --identifier my-session-001
```

**✅ 期待される結果**: `半径 5 の円の面積: 78.54` が表示されること

### 4.4 pandas を使ったデータ分析

```bash
az containerapp session code-interpreter execute \
  --name $SESSION_POOL_NAME \
  --resource-group $RESOURCE_GROUP \
  --code "
import pandas as pd
data = {
    '名前': ['田中', '鈴木', '佐藤'],
    '年齢': [25, 30, 35],
    'スコア': [85, 92, 78]
}
df = pd.DataFrame(data)
print(df)
print(f'\n平均スコア: {df[\"スコア\"].mean():.1f}')
" \
  --identifier my-session-001
```

**✅ 期待される結果**: DataFrame と平均スコア `85.0` が表示されること

### 4.5 セッションの状態保持を確認

同じ `--identifier` を使うと、セッションの状態（変数など）が保持されます。

**ステップ1**: 変数を設定

```bash
az containerapp session code-interpreter execute \
  --name $SESSION_POOL_NAME \
  --resource-group $RESOURCE_GROUP \
  --code "x = 100; print(f'x = {x}')" \
  --identifier state-test
```

**ステップ2**: 同じセッションで変数を参照

```bash
az containerapp session code-interpreter execute \
  --name $SESSION_POOL_NAME \
  --resource-group $RESOURCE_GROUP \
  --code "x += 50; print(f'x = {x}')" \
  --identifier state-test
```

**✅ 期待される結果**: `x = 150` が表示されること（前回の値 100 に 50 が加算された）

> **💡 ポイント**: 異なる `--identifier` を使用すると、新しいセッションが作成されます。

---

## Step 5: REST API を使用した実行（オプション）

Azure CLI の代わりに REST API を直接呼び出すこともできます。

### 5.1 認証トークンを取得

```bash
ACCESS_TOKEN=$(az account get-access-token --resource https://dynamicsessions.io --query accessToken -o tsv)
```

### 5.2 セッションプールの管理エンドポイントを取得

```bash
POOL_ENDPOINT=$(az containerapp sessionpool show \
  --name $SESSION_POOL_NAME \
  --resource-group $RESOURCE_GROUP \
  --query properties.poolManagementEndpoint -o tsv)
echo "Endpoint: $POOL_ENDPOINT"
```

### 5.3 API を呼び出してコードを実行

```bash
EXEC_ID="api-test-001"
API_VERSION="2025-10-02-preview"
URL="${POOL_ENDPOINT}/executions?identifier=${EXEC_ID}&api-version=${API_VERSION}"

curl --request POST \
  --url "$URL" \
  --header "Authorization: Bearer $ACCESS_TOKEN" \
  --header 'content-type: application/json' \
  --data '{
    "codeInputType": "inline",
    "executionType": "synchronous",
    "code": "print(\"Hello from REST API\")",
    "timeoutInSeconds": 60
  }'
```

**✅ 期待される結果**:

```json
{
  "identifier": "api-test-001",
  "status": "Succeeded",
  "result": {
    "stdout": "Hello from REST API\n"
  }
}
```

---

## Step 6: セッションの管理

### 6.1 アクティブなセッション一覧を取得

**Azure CLI を使用する場合:**

```bash
az rest --method get \
  --url "${POOL_ENDPOINT}/listSessions?api-version=2025-10-02-preview" \
  --resource https://dynamicsessions.io
```

**curl を使用する場合:**

```bash
curl --request GET \
  --url "${POOL_ENDPOINT}/listSessions?api-version=2025-10-02-preview" \
  --header "Authorization: Bearer $ACCESS_TOKEN"
```

**✅ 期待される結果**:

```json
{
  "sessions": [
    {
      "identifier": "my-session-001",
      "createdAt": "2026-01-30T06:16:17.1402335Z",
      "lastAccessedAt": "2026-01-30T06:16:17.1402335Z",
      "expireAt": "2026-01-30T06:21:17.1400485Z"
    }
  ]
}
```

> **💡 注意**: セッションは `cooldown-period`（デフォルト300秒）経過後に自動的に削除されます。

### 6.2 セッションプールの設定を変更

最大セッション数を変更する例：

```bash
az containerapp sessionpool update \
  --name $SESSION_POOL_NAME \
  --resource-group $RESOURCE_GROUP \
  --max-sessions 50
```

---

## 🧹 クリーンアップ

ハンズオンが完了したら、作成したリソースを削除してコストを節約しましょう。

```bash
az group delete --resource-group $RESOURCE_GROUP --yes --no-wait
```

> **💡 ヒント**: `--no-wait` オプションを使用すると、削除処理がバックグラウンドで実行されます。

---

## 🎉 おめでとうございます！

Azure Container Apps 動的セッションのハンズオンを完了しました。

### 学んだこと

- ✅ セッションプールの作成と管理
- ✅ Azure CLI を使用した Python コードの実行
- ✅ REST API を使用したコード実行
- ✅ セッションの状態保持
- ✅ アクティブセッションの一覧取得

### 次のステップ

- [Azure Container Apps Sessions のドキュメント](https://learn.microsoft.com/ja-jp/azure/container-apps/sessions)
- [Code interpreter sessions in Azure Container Apps](https://learn.microsoft.com/en-us/azure/container-apps/sessions-code-interpreter)

## 📂 その他のサンプル

| サンプル | 説明 |
|---------|------|
| [code-interpreter](./code-interpreter/) | Python で Dynamic Sessions REST API を呼び出すサンプル |
| [gpt-code-interpreter](./gpt-code-interpreter/) | Azure OpenAI の Function Calling で Dynamic Sessions をコード実行ツールとして利用するハンズオン |
| [dynamic-sessions-mcp](./dynamic-sessions-mcp/) | Dynamic Sessions を MCP サーバーとして利用するハンズオン |
| [gpt-mcp-interpreter](./gpt-mcp-interpreter/) | Azure OpenAI の Responses API + MCP で Dynamic Sessions をコード実行ツールとして利用するハンズオン |
