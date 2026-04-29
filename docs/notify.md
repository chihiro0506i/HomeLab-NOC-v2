# Notify Hub

HomeLab-NOC-v2 のサブプロジェクトとして動作するイベント集約サービスです。
FastAPI + SQLite で構成され、Uptime Kuma やバックアップスクリプトなどからのイベントを受信・保存し、Web ダッシュボードで履歴を閲覧できます。
※DB内には将来の通知送信・設定保存用として `notifications` や `settings` といった予約テーブルが存在しますが、現段階では「イベント記録基盤」としてのみ機能するため未使用です。

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

## API リファレンス

### GET /health

Uptime Kuma で監視するためのヘルスチェックです。

```json
{"status": "ok", "service": "homelab-notify"}
```

### POST /api/events

イベントを受信して SQLite に保存します。
`X-Notify-Token` ヘッダーが必須です。

`severity` は `info`, `warning`, `error`, `critical` のいずれかです。
それ以外の値を送ると 422 Unprocessable Entity が返ります。

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
    "target": "192.168.11.11:53"
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
- `source` — フィルタ（例: `uptime-kuma`, `backup`）
- `severity` — フィルタ（例: `critical`, `error`）

### POST /api/test-notification

テストイベントを作成します。`X-Notify-Token` ヘッダーが必須です。

## Uptime Kuma Webhook 連携

Uptime Kuma の監視結果を Notify Hub に Webhook で送信し、イベントとして記録する仕組みです。
これにより、サービスの障害・復旧イベントを Notify Hub のダッシュボードで一覧確認できます。

### 接続方法

- **Docker ネットワーク内**（推奨）: `http://notify:8090/api/events`
  - Uptime Kuma と Notify Hub が同じ Docker Compose で動いている場合、Compose サービス名 `notify` で通信できます。
- **LAN 内 Raspberry Pi IP 経由**: `http://<RaspberryPi-IP>:8090/api/events`

> **注意:** ルータのポート開放は行わないでください。Notify Hub はインターネットに公開しない前提です。

### Uptime Kuma 側の設定手順

1. Uptime Kuma の「通知」設定で **Webhook** を追加
2. URL: `http://notify:8090/api/events`
3. Method: `POST`
4. Content-Type: `application/json`
5. Custom Headers に追加:
   ```
   X-Notify-Token: <NOTIFY_API_TOKEN の値>
   ```
6. `X-Notify-Token` の値は `.env` の `NOTIFY_API_TOKEN` と一致させてください

### Webhook JSON テンプレート

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

> **【重要】Webhookテンプレート変数についての注意**
> 上記の `{{ }}` は Uptime Kuma のテンプレート変数です。
> 実際の変数名や送信される JSON の構造は、**Uptime Kuma のバージョンや設定画面のUIによって異なる場合が多々あります**。
> そのため、設定後は**必ず Uptime Kuma 側の「Test」ボタンからテスト通知を送信し、意図した JSON が送られているか（および Notify Hub 側で HTTP 201 や 422 などの応答がどうなるか）を実機で確認してください**。

## イベント設計

Notify Hub に記録する主なイベントの設計です。

| モニター対象 | source | event_type | severity | 方針 |
|-------------|--------|-----------|----------|------|
| Pi-hole DNS down | `uptime-kuma` | `monitor_down` | `critical` | 将来の通知対象 |
| Pi-hole DNS up | `uptime-kuma` | `monitor_up` | `info` | 記録のみ |
| Portal down | `uptime-kuma` | `monitor_down` | `warning` | 記録のみ |
| NetAlertX down | `uptime-kuma` | `monitor_down` | `warning` | 記録のみ |
| Notify Hub down | `uptime-kuma` | `monitor_down` | `warning` | Uptime Kuma 側で検知。Notify Hub 自身には送れない可能性がある |

> **備考:** Notify Hub 自身の障害は、Uptime Kuma が `/health` の応答失敗を検知しますが、
> その通知を Notify Hub に Webhook で送っても受信できない場合があります。
> Notify Hub の死活は Uptime Kuma のダッシュボードで直接確認してください。

## スクリプト

```bash
# 汎用テストイベント送信
./scripts/notify-test-event.sh

# Uptime Kuma 風 monitor_down イベント送信
./scripts/notify-test-uptime-down.sh

# Uptime Kuma 風 monitor_up イベント送信
./scripts/notify-test-uptime-up.sh

# ヘルスチェック
./scripts/notify-status.sh

# ログ確認
./scripts/notify-logs.sh
```

## Raspberry Pi 上での実機確認手順

Windows 上での開発後、以下の手順でラズパイ上で動作確認を行ってください。

```bash
# 1. リポジトリを最新化
cd ~/projects/HomeLab-NOC-v2
git pull

# 2. Compose 構文チェック
docker compose config > /tmp/compose-check.yml

# 3. Notify Hub を再ビルド・起動
docker compose up -d --build notify

# 4. ヘルスチェック
./scripts/notify-status.sh

# 5. テストイベント送信
./scripts/notify-test-event.sh
./scripts/notify-test-uptime-down.sh
./scripts/notify-test-uptime-up.sh

# 6. Web 画面確認
curl -i http://localhost:8090/
curl -i http://localhost:8090/events

# 7. API でイベント一覧確認
curl -s http://localhost:8090/api/events | python3 -m json.tool
```

**期待結果:**

- `notify-status.sh` が `{"status":"ok","service":"homelab-notify"}` を返す
- 各テストスクリプトが HTTP 201 で成功する
- `/` と `/events` が 200 OK を返す
- `/api/events` に `manual` と `uptime-kuma` の両方のイベントが表示される

## セキュリティ

- **インターネットに公開しないでください**
- ルータのポート開放は行わないでください
- `NOTIFY_API_TOKEN` は初期値から必ず変更してください
- `.env`、`data/` は Git 管理に含めないでください

## トラブルシューティング

### Notify Hub が起動しない

```bash
docker compose logs notify
```

### 401 Unauthorized が返る

`X-Notify-Token` ヘッダーの値と `.env` の `NOTIFY_API_TOKEN` が一致しているか確認してください。

### データベースエラー (attempt to write a readonly database)

`POST /api/events` が `HTTP 500` になり、`docker compose logs notify` で以下のエラーが出る場合：
`sqlite3.OperationalError: attempt to write a readonly database`

**原因:**
`data/notify/` の所有者が、コンテナ内の `notify` ユーザ (デフォルト UID/GID: `20212:20212`) と合っていないためです。

**対処法:**
`setup.sh` を再実行するか、以下のコマンドを手動で実行して権限を修正してください。

```bash
sudo chown -R 20212:20212 data/notify
sudo chmod -R u+rwX,g+rwX data/notify
```
