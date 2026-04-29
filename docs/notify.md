# Notify Hub

HomeLab-NOC-v2 のサブプロジェクトとして動作する通知集約サービスです。
FastAPI + SQLite で構成され、Uptime Kuma やバックアップスクリプトなどからのイベントを受信・保存し、Web ダッシュボードで履歴を閲覧できます。

## 起動方法

```bash
# 初回のみ
./scripts/setup.sh

# .env を編集して NOTIFY_API_TOKEN を設定
nano .env

# 起動
./scripts/start.sh
```

Notify Hub は `docker compose up -d` で他のサービスと一緒に起動します。

### アクセス

```
http://<RaspberryPi-IP>:8090
```

## 設定項目（.env）

| 変数 | デフォルト | 説明 |
|------|-----------|------|
| `NOTIFY_PORT` | `8090` | Notify Hub のポート |
| `NOTIFY_API_TOKEN` | — | API 認証トークン（必須、変更してください） |
| `NOTIFY_ENABLE_EXTERNAL_SEND` | `false` | 外部通知（ntfy）を有効にするか |
| `NOTIFY_DEDUP_WINDOW_SECONDS` | `600` | 重複通知抑制の窓（秒） |
| `NTFY_URL` | — | ntfy サーバ URL |
| `NTFY_TOPIC` | — | ntfy トピック |
| `NTFY_TOKEN` | — | ntfy 認証トークン |
| `SLURM_ENABLED` | `false` | Slurm 監視を有効にするか |
| `SLURM_HOST` | — | Slurm サーバのホスト名 |
| `SLURM_USER` | — | SSH ユーザ名 |
| `SLURM_PORT` | `22` | SSH ポート |
| `SLURM_POLL_INTERVAL_ACTIVE` | `60` | ジョブ実行中のポーリング間隔（秒） |
| `SLURM_POLL_INTERVAL_IDLE` | `300` | ジョブなし時のポーリング間隔（秒） |

## API リファレンス

### GET /health

Uptime Kuma で監視するためのヘルスチェックです。

```json
{"status": "ok", "service": "homelab-notify"}
```

### POST /api/events

イベントを受信して SQLite に保存します。
`X-Notify-Token` ヘッダーが必須です。

**リクエスト例:**

```json
{
  "source": "uptime-kuma",
  "event_type": "monitor_down",
  "severity": "critical",
  "title": "Pi-hole DNS is down",
  "message": "Uptime Kuma detected Pi-hole DNS failure.",
  "dedup_key": "uptime:pihole_dns:down",
  "metadata": {
    "monitor_name": "Pi-hole DNS",
    "url": "192.168.11.11:53"
  }
}
```

**レスポンス例:**

```json
{"status": "stored", "event_id": 123, "notified": false}
```

### GET /api/events

保存済みイベントを JSON で返します。

クエリパラメータ:
- `limit` — 件数上限（デフォルト 100）
- `source` — フィルタ（例: `uptime-kuma`, `slurm`）
- `severity` — フィルタ（例: `critical`, `error`）

### GET /api/slurm/jobs

Slurm ジョブ履歴を JSON で返します。`SLURM_ENABLED=false` のときは空配列を返します。

### POST /api/test-notification

テストイベントを作成します。`X-Notify-Token` ヘッダーが必須です。

## Uptime Kuma Webhook 連携

Uptime Kuma から Notify Hub へ Webhook でイベントを送る方法です。

### Uptime Kuma 側の設定

1. Uptime Kuma の「通知」設定で **Webhook** を追加
2. URL: `http://homelab-notify:8090/api/events`（Docker ネットワーク内）
   - Docker 外から送る場合: `http://<RaspberryPi-IP>:8090/api/events`
3. Method: `POST`
4. Content-Type: `application/json`
5. Custom Headers に追加:
   ```
   X-Notify-Token: <NOTIFY_API_TOKEN の値>
   ```

### Uptime Kuma が送る JSON テンプレート

Uptime Kuma のカスタム Webhook body に以下のテンプレートを設定してください。

**Monitor Down (critical):**

```json
{
  "source": "uptime-kuma",
  "event_type": "monitor_down",
  "severity": "critical",
  "title": "{{ monitorJSON.name }} is DOWN",
  "message": "{{ msg }}",
  "dedup_key": "uptime:{{ monitorJSON.name }}:down",
  "metadata": {
    "monitor_name": "{{ monitorJSON.name }}",
    "url": "{{ monitorJSON.url }}"
  }
}
```

**Monitor Up (info):**

```json
{
  "source": "uptime-kuma",
  "event_type": "monitor_up",
  "severity": "info",
  "title": "{{ monitorJSON.name }} is UP",
  "message": "{{ msg }}",
  "dedup_key": "uptime:{{ monitorJSON.name }}:up",
  "metadata": {
    "monitor_name": "{{ monitorJSON.name }}",
    "url": "{{ monitorJSON.url }}"
  }
}
```

> **注意:** Uptime Kuma の Webhook テンプレート記法は Uptime Kuma のバージョンにより異なる場合があります。
> 上記の `{{ }}` プレースホルダーは Uptime Kuma のテンプレート変数です。
> 設定前に Uptime Kuma のドキュメントを確認してください。

### 推奨 severity 設定

| モニター対象 | Down 時の severity |
|-------------|-------------------|
| Pi-hole DNS | `critical` |
| Portal | `warning` |
| NetAlertX | `warning` |
| Notify Hub /health | `warning` |

## スクリプト

```bash
# テストイベント送信
./scripts/notify-test-event.sh

# ヘルスチェック
./scripts/notify-status.sh

# ログ確認
./scripts/notify-logs.sh
```

## セキュリティ

- **インターネットに公開しないでください**
- ルータのポート開放は行わないでください
- `NOTIFY_API_TOKEN` は初期値から必ず変更してください
- `.env`、`data/`、`secrets/` は Git 管理に含めないでください
- SSH 秘密鍵はコンテナイメージに COPY せず、volume mount（read-only）で渡してください

## トラブルシューティング

### Notify Hub が起動しない

```bash
docker compose logs notify
```

### 401 Unauthorized が返る

`X-Notify-Token` ヘッダーの値と `.env` の `NOTIFY_API_TOKEN` が一致しているか確認してください。

### データベースエラー

`data/notify/` ディレクトリが存在し、書き込み可能か確認してください。

```bash
ls -la data/notify/
```
