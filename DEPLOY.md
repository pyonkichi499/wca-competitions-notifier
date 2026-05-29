# WCA関東大会通知Bot - Cloud Runデプロイガイド

このドキュメントでは、WCA関東大会通知BotをGoogle Cloud Runにデプロイする手順を説明します。

## 目次

1. [前提条件](#1-前提条件)
2. [GCPプロジェクト設定](#2-gcpプロジェクト設定)
3. [Cloud Runデプロイ](#3-cloud-runデプロイ)
4. [Cloud Storage設定](#4-cloud-storage設定)
5. [Secret Manager設定](#5-secret-manager設定)
6. [Cloud Scheduler設定](#6-cloud-scheduler設定)
7. [動作確認](#7-動作確認)

---

## 1. 前提条件

### 必要なツール

- **Google Cloud SDK (gcloud)**: [インストール手順](https://cloud.google.com/sdk/docs/install)
- **Docker**: [インストール手順](https://docs.docker.com/get-docker/)（ローカルビルドの場合）
- **Python 3.11+**: ローカル開発用
- **rye**: パッケージ管理

### 必要なアカウント

- **Google Cloud Platform アカウント**: 課金が有効であること
- **Twitter Developer アカウント**: API認証情報が必要（Free プランで可）

### Twitter API 認証情報

Twitter Developer Portal (https://developer.twitter.com/) で以下の認証情報を取得:

- API Key
- API Secret
- Access Token
- Access Token Secret

---

## 2. GCPプロジェクト設定

### 2.1 gcloud CLIの初期化

```bash
# Google Cloudにログイン
gcloud auth login

# プロジェクト一覧を確認
gcloud projects list
```

### 2.2 新規プロジェクト作成（既存プロジェクトを使用する場合はスキップ）

```bash
# プロジェクト作成
gcloud projects create wca-kanto-notifier --name="WCA Kanto Notifier"

# プロジェクトを選択
gcloud config set project wca-kanto-notifier
```

### 2.3 課金の有効化

```bash
# 課金アカウント一覧を確認
gcloud billing accounts list

# 課金をプロジェクトにリンク
gcloud billing projects link wca-kanto-notifier --billing-account=BILLING_ACCOUNT_ID
```

### 2.4 必要なAPIの有効化

```bash
# 必要なAPIを一括有効化
gcloud services enable \
  run.googleapis.com \
  storage.googleapis.com \
  secretmanager.googleapis.com \
  cloudscheduler.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com
```

### 2.5 リージョンの設定

```bash
# デフォルトリージョンを設定（東京リージョン推奨）
gcloud config set run/region asia-northeast1
gcloud config set compute/region asia-northeast1
```

---

## 3. Cloud Runデプロイ

### 3.1 Dockerfileの作成

プロジェクトルートに`Dockerfile`を作成:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 依存関係ファイルをコピー
COPY pyproject.toml ./

# pipでインストール（ryeは使わない）
RUN pip install --no-cache-dir .

# アプリケーションコードをコピー
COPY src/ ./src/

# ポート設定
ENV PORT=8080
EXPOSE 8080

# アプリケーション起動
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### 3.2 .dockerignoreの作成

```text
.git
.gitignore
.env
.env.*
*.pyc
__pycache__
.pytest_cache
.ruff_cache
data/
*.md
tests/
scripts/
.venv/
```

### 3.3 Artifact Registryリポジトリの作成

```bash
# Dockerリポジトリを作成
gcloud artifacts repositories create wca-notifier \
  --repository-format=docker \
  --location=asia-northeast1 \
  --description="WCA Kanto Notifier Docker images"

# 認証設定
gcloud auth configure-docker asia-northeast1-docker.pkg.dev
```

### 3.4 Cloud Buildでビルド＆デプロイ

```bash
# ソースコードから直接Cloud Runにデプロイ
gcloud run deploy wca-kanto-notifier \
  --source . \
  --region asia-northeast1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 256Mi \
  --timeout 60s \
  --max-instances 1 \
  --set-env-vars "ENV=production"
```

または、Artifact Registry経由でデプロイ:

```bash
# イメージをビルド
gcloud builds submit --tag asia-northeast1-docker.pkg.dev/wca-kanto-notifier/wca-notifier/app:latest

# Cloud Runにデプロイ
gcloud run deploy wca-kanto-notifier \
  --image asia-northeast1-docker.pkg.dev/wca-kanto-notifier/wca-notifier/app:latest \
  --region asia-northeast1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 256Mi \
  --timeout 60s \
  --max-instances 1 \
  --set-env-vars "ENV=production"
```

### 3.5 サービスURLの確認

```bash
# デプロイしたサービスの情報を確認
gcloud run services describe wca-kanto-notifier --region asia-northeast1

# URLだけ取得
gcloud run services describe wca-kanto-notifier \
  --region asia-northeast1 \
  --format="value(status.url)"
```

---

## 4. Cloud Storage設定

### 4.1 バケットの作成

```bash
# バケット名はグローバルで一意である必要がある
# プロジェクトIDを含めると一意になりやすい
BUCKET_NAME="wca-kanto-notifier-state"

# バケット作成（東京リージョン）
gcloud storage buckets create gs://${BUCKET_NAME} \
  --location=asia-northeast1 \
  --uniform-bucket-level-access
```

### 4.2 Cloud Runサービスアカウントに権限付与

```bash
# プロジェクト番号を取得
PROJECT_NUMBER=$(gcloud projects describe $(gcloud config get-value project) --format="value(projectNumber)")

# Cloud Runのデフォルトサービスアカウント
SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

# Cloud Storageへの読み書き権限を付与
gcloud storage buckets add-iam-policy-binding gs://${BUCKET_NAME} \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/storage.objectUser"
```

### 4.3 環境変数の更新

```bash
# GCSバケット名を環境変数に追加
gcloud run services update wca-kanto-notifier \
  --region asia-northeast1 \
  --set-env-vars "ENV=production,GCS_BUCKET_NAME=${BUCKET_NAME}"
```

---

## 5. Secret Manager設定

### 5.1 シークレットの作成

```bash
# Twitter API認証情報をシークレットとして保存
echo -n "YOUR_TWITTER_API_KEY" | \
  gcloud secrets create twitter-api-key --data-file=-

echo -n "YOUR_TWITTER_API_SECRET" | \
  gcloud secrets create twitter-api-secret --data-file=-

echo -n "YOUR_TWITTER_ACCESS_TOKEN" | \
  gcloud secrets create twitter-access-token --data-file=-

echo -n "YOUR_TWITTER_ACCESS_TOKEN_SECRET" | \
  gcloud secrets create twitter-access-token-secret --data-file=-
```

### 5.2 シークレットへのアクセス権限付与

```bash
# プロジェクト番号を取得
PROJECT_NUMBER=$(gcloud projects describe $(gcloud config get-value project) --format="value(projectNumber)")

# Cloud Runのデフォルトサービスアカウント
SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

# 各シークレットへのアクセス権限を付与
for SECRET in twitter-api-key twitter-api-secret twitter-access-token twitter-access-token-secret; do
  gcloud secrets add-iam-policy-binding ${SECRET} \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/secretmanager.secretAccessor"
done
```

### 5.3 Cloud Runにシークレットをマウント

```bash
# シークレットを環境変数としてCloud Runに設定
gcloud run services update wca-kanto-notifier \
  --region asia-northeast1 \
  --update-secrets=TWITTER_API_KEY=twitter-api-key:latest \
  --update-secrets=TWITTER_API_SECRET=twitter-api-secret:latest \
  --update-secrets=TWITTER_ACCESS_TOKEN=twitter-access-token:latest \
  --update-secrets=TWITTER_ACCESS_TOKEN_SECRET=twitter-access-token-secret:latest
```

---

## 6. Cloud Scheduler設定

### 6.1 サービスアカウントの作成（認証用）

```bash
# Scheduler用のサービスアカウントを作成
gcloud iam service-accounts create scheduler-invoker \
  --display-name="Cloud Scheduler Invoker"

PROJECT_ID=$(gcloud config get-value project)

# Cloud Run起動権限を付与
gcloud run services add-iam-policy-binding wca-kanto-notifier \
  --region asia-northeast1 \
  --member="serviceAccount:scheduler-invoker@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/run.invoker"
```

### 6.2 Cloud Schedulerジョブの作成

```bash
# Cloud RunサービスのURLを取得
SERVICE_URL=$(gcloud run services describe wca-kanto-notifier \
  --region asia-northeast1 \
  --format="value(status.url)")

PROJECT_ID=$(gcloud config get-value project)

# 毎日朝9時（日本時間）に実行するスケジューラを作成
gcloud scheduler jobs create http wca-kanto-notifier-daily \
  --location asia-northeast1 \
  --schedule "0 9 * * *" \
  --time-zone "Asia/Tokyo" \
  --uri "${SERVICE_URL}/notify" \
  --http-method POST \
  --oidc-service-account-email "scheduler-invoker@${PROJECT_ID}.iam.gserviceaccount.com" \
  --oidc-token-audience "${SERVICE_URL}"
```

### 6.3 スケジューラの認証設定（allow-unauthenticatedを無効にする場合）

Cloud Runを認証必須に変更する場合:

```bash
# 認証なしアクセスを削除
gcloud run services remove-iam-policy-binding wca-kanto-notifier \
  --region asia-northeast1 \
  --member="allUsers" \
  --role="roles/run.invoker"
```

---

## 7. 動作確認

### 7.1 ヘルスチェック

```bash
# サービスURLを取得
SERVICE_URL=$(gcloud run services describe wca-kanto-notifier \
  --region asia-northeast1 \
  --format="value(status.url)")

# ヘルスチェック
curl ${SERVICE_URL}/
# 期待される応答: {"status":"ok","service":"WCA Kanto Notifier"}
```

### 7.2 大会一覧取得テスト

```bash
# 関東大会一覧を取得
curl ${SERVICE_URL}/competitions
```

### 7.3 DryRunモードでの通知テスト

```bash
# DryRunモードを有効にして再デプロイ
gcloud run services update wca-kanto-notifier \
  --region asia-northeast1 \
  --set-env-vars "DRY_RUN=true"

# 通知エンドポイントを実行
curl -X POST ${SERVICE_URL}/notify

# 本番モードに戻す
gcloud run services update wca-kanto-notifier \
  --region asia-northeast1 \
  --set-env-vars "DRY_RUN=false"
```

### 7.4 Cloud Schedulerの手動実行

```bash
# ジョブを手動実行
gcloud scheduler jobs run wca-kanto-notifier-daily --location asia-northeast1
```

### 7.5 ログの確認

```bash
# Cloud Runのログを確認
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=wca-kanto-notifier" \
  --limit 50 \
  --format "table(timestamp,textPayload)"

# または、Cloud Consoleで確認
echo "https://console.cloud.google.com/run/detail/asia-northeast1/wca-kanto-notifier/logs"
```

### 7.6 Cloud Storageの状態確認

```bash
BUCKET_NAME="wca-kanto-notifier-state"

# 状態ファイルの内容を確認
gcloud storage cat gs://${BUCKET_NAME}/notified_competitions.json
```

---

## トラブルシューティング

### よくある問題と解決方法

#### 1. Twitter投稿が失敗する

```bash
# ログでエラー内容を確認
gcloud logging read "resource.type=cloud_run_revision AND textPayload:Twitter" --limit 10

# シークレットが正しく設定されているか確認
gcloud run services describe wca-kanto-notifier \
  --region asia-northeast1 \
  --format="yaml(spec.template.spec.containers[0].env)"
```

#### 2. Cloud Storageにアクセスできない

```bash
# サービスアカウントの権限を確認
gcloud storage buckets get-iam-policy gs://${BUCKET_NAME}

# バケットが存在するか確認
gcloud storage buckets describe gs://${BUCKET_NAME}
```

#### 3. Cloud Schedulerが実行されない

```bash
# ジョブの状態を確認
gcloud scheduler jobs describe wca-kanto-notifier-daily --location asia-northeast1

# 実行履歴を確認（Cloud Console）
echo "https://console.cloud.google.com/cloudscheduler"
```

#### 4. 認証エラー（403 Forbidden）

```bash
# Cloud Runの呼び出し権限を確認
gcloud run services get-iam-policy wca-kanto-notifier --region asia-northeast1

# Scheduler用サービスアカウントに権限があるか確認
gcloud run services add-iam-policy-binding wca-kanto-notifier \
  --region asia-northeast1 \
  --member="serviceAccount:scheduler-invoker@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.invoker"
```

---

## コスト見積もり

このアプリケーションの運用コストは非常に低く抑えられます:

| サービス | 使用量 | 予想コスト/月 |
|---------|--------|--------------|
| Cloud Run | 1日1回実行、数秒/回 | 無料枠内 |
| Cloud Storage | 数KB | 無料枠内 |
| Cloud Scheduler | 3ジョブ以内 | 無料枠内 |
| Secret Manager | 4シークレット | 無料枠内 |

**合計: 基本的に無料（GCP無料枠内で運用可能）**

---

## 次のステップ

1. **エラー通知の設定**: Cloud MonitoringとCloud Alertingを使用してエラー発生時にメール/Slack通知
2. **CI/CDパイプライン**: GitHub Actionsとの連携で自動デプロイ
3. **カスタムドメイン**: 必要に応じてカスタムドメインを設定
