# TODO - WCA関東大会通知Bot

## プロジェクト概要

WCA（World Cube Association）の関東地方で開催される新規大会をTwitter/Xに自動投稿するBot。

**リポジトリ:** https://github.com/pyonkichi499/wca-competitions-notifier

---

## 現在の状態

### ディレクトリ構成
```
wca-competitions-notifier/
├── src/
│   ├── __init__.py
│   ├── config.py              # 設定・定数（KANTO_KEYWORDS, EVENT_NAMES等）
│   ├── logger.py              # ログ設定（Cloud Run対応JSON/ローカルtext）
│   ├── wca_client.py          # WCA API取得（非同期httpx）
│   ├── kanto_filter.py        # 関東フィルタリング
│   ├── tweet_formatter.py     # ツイート文面生成
│   ├── twitter_client.py      # Twitter投稿（tweepy）+ DryRunClient
│   ├── competition_tracker.py # 状態管理（LocalStorage/CloudStorage）
│   └── main.py                # FastAPIエントリーポイント
├── tests/                     # 単体テスト（70件）
├── scripts/
│   └── run_local.py           # ローカルテスト用スクリプト
├── data/                      # 状態ファイル保存先（gitignore）
├── pyproject.toml             # rye設定
├── .env.example               # 環境変数テンプレート
└── README.md
```

### 完了済み機能
- WCA非公式API（認証不要）から日本の大会取得
- 関東7都県のフィルタリング（Tokyo, Kanagawa, Chiba, Saitama, Ibaraki, Tochigi, Gunma）
- ツイート文面生成（日本語日付、種目名変換）
- Twitter投稿（tweepy）、DryRunモード
- 状態管理（通知済み大会をJSONで保存）
- FastAPI `/notify` エンドポイント
- ログ出力（Cloud Run: JSON構造化ログ / ローカル: テキスト）
- 単体テスト70件（pytest）

### 動作確認コマンド
```bash
# 依存関係インストール
rye sync
# または: pip install -e ".[dev]"

# ローカルテスト（DryRun、実際にはツイートしない）
rye run python scripts/run_local.py

# テスト実行
rye run pytest tests/ -v

# FastAPIサーバー起動
rye run uvicorn src.main:app --reload
# http://localhost:8000/docs でSwagger UI確認
# POST /notify でツイート処理実行（DRY_RUN=trueなら投稿しない）
```

---

## Phase 2: Cloud Runデプロイ

### 2-1. Dockerfile作成

**目的:** Cloud Runで動かすためのコンテナイメージを作成

**ファイル:** `Dockerfile`

```dockerfile
FROM python:3.11-slim as builder

WORKDIR /app
RUN pip install --no-cache-dir hatchling
COPY pyproject.toml .
COPY src/ src/
RUN pip wheel --no-deps --wheel-dir /wheels .

FROM python:3.11-slim

WORKDIR /app
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/*.whl && rm -rf /wheels

# 非rootユーザー
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

ENV PORT=8080
EXPOSE 8080

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

**確認コマンド:**
```bash
docker build -t wca-kanto-notifier .
docker run -p 8080:8080 -e DRY_RUN=true wca-kanto-notifier
curl http://localhost:8080/
curl -X POST http://localhost:8080/notify
```

### 2-2. GCPプロジェクト設定

**前提:** gcloud CLIインストール済み、GCPアカウント作成済み

```bash
# プロジェクト作成（または既存を使用）
gcloud projects create wca-kanto-notifier --name="WCA Kanto Notifier"
gcloud config set project wca-kanto-notifier

# 必要なAPIを有効化
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  cloudscheduler.googleapis.com \
  secretmanager.googleapis.com \
  storage.googleapis.com

# Artifact Registry作成（コンテナイメージ保存用）
gcloud artifacts repositories create wca-kanto-notifier \
  --repository-format=docker \
  --location=asia-northeast1
```

### 2-3. Cloud Runデプロイ

```bash
# イメージをビルド＆プッシュ
gcloud builds submit --tag asia-northeast1-docker.pkg.dev/PROJECT_ID/wca-kanto-notifier/app

# Cloud Runにデプロイ
gcloud run deploy wca-kanto-notifier \
  --image asia-northeast1-docker.pkg.dev/PROJECT_ID/wca-kanto-notifier/app \
  --region asia-northeast1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars "ENV=production,DRY_RUN=false"
```

### 2-4. Cloud Storage（状態管理）

**目的:** 通知済み大会リストを永続化（Cloud Runはステートレス）

```bash
# バケット作成
gsutil mb -l asia-northeast1 gs://wca-kanto-notifier-state

# Cloud Runサービスアカウントに権限付与
gcloud run services describe wca-kanto-notifier --region asia-northeast1 --format='value(spec.template.spec.serviceAccountName)'
# → 出力されたサービスアカウントに権限付与

gsutil iam ch serviceAccount:SERVICE_ACCOUNT@PROJECT_ID.iam.gserviceaccount.com:objectAdmin gs://wca-kanto-notifier-state
```

**環境変数追加:**
```bash
gcloud run services update wca-kanto-notifier \
  --region asia-northeast1 \
  --set-env-vars "GCS_BUCKET_NAME=wca-kanto-notifier-state"
```

### 2-5. Secret Manager（Twitter認証情報）

**目的:** Twitter API認証情報をセキュアに管理

```bash
# シークレット作成
echo -n "YOUR_API_KEY" | gcloud secrets create twitter-api-key --data-file=-
echo -n "YOUR_API_SECRET" | gcloud secrets create twitter-api-secret --data-file=-
echo -n "YOUR_ACCESS_TOKEN" | gcloud secrets create twitter-access-token --data-file=-
echo -n "YOUR_ACCESS_TOKEN_SECRET" | gcloud secrets create twitter-access-token-secret --data-file=-

# Cloud Runにマウント
gcloud run services update wca-kanto-notifier \
  --region asia-northeast1 \
  --set-secrets "TWITTER_API_KEY=twitter-api-key:latest" \
  --set-secrets "TWITTER_API_SECRET=twitter-api-secret:latest" \
  --set-secrets "TWITTER_ACCESS_TOKEN=twitter-access-token:latest" \
  --set-secrets "TWITTER_ACCESS_TOKEN_SECRET=twitter-access-token-secret:latest"
```

---

## Phase 3: 自動化

### 3-1. Cloud Scheduler

**目的:** 1日1回自動でCloud Runを呼び出す

```bash
# サービスアカウント作成（Cloud Scheduler用）
gcloud iam service-accounts create scheduler-invoker \
  --display-name="Cloud Scheduler Invoker"

# Cloud Run呼び出し権限を付与
gcloud run services add-iam-policy-binding wca-kanto-notifier \
  --region asia-northeast1 \
  --member="serviceAccount:scheduler-invoker@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.invoker"

# スケジュールジョブ作成（毎日9:00 JST）
gcloud scheduler jobs create http wca-kanto-notifier-daily \
  --location=asia-northeast1 \
  --schedule="0 9 * * *" \
  --time-zone="Asia/Tokyo" \
  --uri="https://wca-kanto-notifier-XXXXX.run.app/notify" \
  --http-method=POST \
  --oidc-service-account-email="scheduler-invoker@PROJECT_ID.iam.gserviceaccount.com"
```

### 3-2. モニタリング・アラート

**Cloud Loggingでエラー監視:**
```bash
# エラーログのフィルタ
resource.type="cloud_run_revision"
resource.labels.service_name="wca-kanto-notifier"
severity>=ERROR
```

**メール通知設定（Cloud Console）:**
1. Cloud Console → Monitoring → Alerting
2. ポリシー作成 → ログベースのアラート
3. 上記フィルタを設定
4. 通知チャンネル（メール）を設定

---

## CI/CD

### GitHub Actions

**ファイル:** `.github/workflows/test.yml`

```yaml
name: Test

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -e ".[dev]"

      - name: Lint with ruff
        run: ruff check src/ tests/

      - name: Run tests
        run: pytest tests/ -v --tb=short
```

**自動デプロイ（オプション）:** `.github/workflows/deploy.yml`

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Authenticate to Google Cloud
        uses: google-github-actions/auth@v2
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}

      - name: Deploy to Cloud Run
        uses: google-github-actions/deploy-cloudrun@v2
        with:
          service: wca-kanto-notifier
          region: asia-northeast1
          source: .
```

---

## 機能追加（Nice to have）

### 締切リマインダー

**概要:** 登録締切の数日前に再通知

**実装方針:**
1. WCA APIから`registration_close`を取得（要確認）
2. 状態管理に`reminded_competitions`を追加
3. 締切3日前などに再通知

### 複数地域対応

**概要:** 関東以外（関西、東海など）にも対応

**実装方針:**
1. `config.py`に地域ごとのキーワードを追加
2. 環境変数`TARGET_REGION`で切り替え
3. または複数Botとしてデプロイ

### Discord/LINE対応

**概要:** Twitter以外にも通知

**実装方針:**
1. `NotifierBase`抽象クラスを作成
2. `TwitterNotifier`, `DiscordNotifier`, `LineNotifier`を実装
3. 環境変数で有効/無効を切り替え

---

## 参考リンク

- [WCA非公式API](https://github.com/robiningelbrecht/wca-rest-api)
- [Twitter API v2 ドキュメント](https://developer.twitter.com/en/docs/twitter-api)
- [Cloud Run ドキュメント](https://cloud.google.com/run/docs)
- [Cloud Scheduler ドキュメント](https://cloud.google.com/scheduler/docs)
- [Secret Manager ドキュメント](https://cloud.google.com/secret-manager/docs)

---

## 優先度

1. **Dockerfile作成** - Cloud Runデプロイの前提
2. **GitHub Actions CI** - PRでテスト自動実行、品質担保
3. **Cloud Runデプロイ** - 本番環境構築
4. **Cloud Storage連携** - 状態の永続化
5. **Secret Manager** - セキュアな認証情報管理
6. **Cloud Scheduler** - 自動実行開始
7. **モニタリング** - 運用監視
