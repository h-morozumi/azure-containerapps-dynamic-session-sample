# Python サンプル: Azure Container Apps Dynamic Sessions

このサンプルでは、Python を使用して Azure Container Apps Dynamic Sessions の REST API を呼び出し、クラウド上で Python コードを実行します。

## 📋 前提条件

- [ルートの README](../README.md) の **Step 1〜3** が完了していること
  - セッションプールが作成済み
  - ロールが割り当て済み
- Azure CLI でログイン済み（`az login`）

> **💡 ヒント**: このプロジェクトは DevContainer で開くことを推奨します。`uv`（高速な Python パッケージマネージャー）が事前にインストールされています。

## 🚀 クイックスタート

### Step 1: ディレクトリに移動

```bash
cd code-interpreter
```

### Step 2: 依存関係をインストール

```bash
uv sync
```

**✅ 期待される結果**: `.venv` ディレクトリが作成され、依存パッケージがインストールされます。

### Step 3: 環境変数を設定

`.env.example` をコピーして `.env` を作成します：

```bash
cp .env.example .env
```

`.env` ファイルを編集して、`POOL_ENDPOINT` を設定します：

```bash
# セッションプールのエンドポイントを取得
az containerapp sessionpool show \
  --name my-session-pool \
  --resource-group rg-containerapps-sessions \
  --query properties.poolManagementEndpoint -o tsv
```

取得した値を `.env` の `POOL_ENDPOINT` に設定してください。

### Step 4: サンプルを実行

```bash
uv run main.py
```

**✅ 期待される結果**:

```
Current Sessions: (count: 0)
 {'sessions': []}
Execution Result:
 {'identifier': 'my-session-001', 'status': 'Succeeded', 'result': {'stdout': 'Hello, Azure Container Apps Sessions\n', ...}}
Current Sessions: (count: 1)
 {'sessions': [{'identifier': 'my-session-001', ...}]}
...
```

## 📁 ファイル構成

| ファイル | 説明 |
|---------|------|
| `main.py` | メインスクリプト - セッション一覧取得・コード実行 |
| `pyproject.toml` | プロジェクト設定・依存関係 |
| `.env.example` | 環境変数のテンプレート |
| `.env` | 実際の環境変数（git管理外） |

## 🔧 主な関数

### `get_headers()`
Azure DefaultAzureCredential を使用して認証トークンを取得し、HTTP ヘッダーを返します。

### `list_sessions(base_url, headers)`
アクティブなセッションの一覧を取得します。

### `execute_code(base_url, headers, exec_id, code, timeout)`
指定したセッションでPythonコードを実行します。

## 📝 依存パッケージ

- `azure-identity` - Azure 認証
- `httpx` - HTTP クライアント
- `python-dotenv` - 環境変数の読み込み

## ⚠️ トラブルシューティング

### 401 Unauthorized エラー

ロールの割り当てがまだ反映されていない可能性があります。数分待ってから再試行してください。

```bash
# ロールの割り当てを確認
az role assignment list \
  --scope $(az containerapp sessionpool show --name my-session-pool --resource-group rg-containerapps-sessions --query id -o tsv) \
  --output table
```

### POOL_ENDPOINT が見つからない

`.env` ファイルが正しく作成されているか確認してください：

```bash
cat .env
```
