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

> **詳細設定手順**: 初心者向けの詳しい設定ステップは、[Uptime Kuma Webhook連携 設定手順](uptime-kuma-webhook-setup.md) を参照してください。

### 設定手順 (1) Notify Hub 自身の監視

まず、Uptime Kuma に Notify Hub 自体の監視 (HTTP) を追加することをおすすめします。
- **監視URL例**: `http://192.168.11.11:8090/health`
- **Method**: GET

### 設定手順 (2) Webhook 通知の作成

次に、Uptime Kuma の「通知」設定から **Webhook** を追加し、以下の通り設定します。

- **URL**: 
  - Docker Compose 内から Notify Hub へ送る場合: `http://notify:8090/api/events`
  - LAN IP経由で送る場合: `http://192.168.11.11:8090/api/events`
- **Method**: `POST`
- **Content-Type**: `application/json`
- **Custom Headers**:
  ```
  X-Notify-Token: <NOTIFY_API_TOKEN の値>
  ```
  ※ `.env` の `NOTIFY_API_TOKEN` と一致させてください。

> **注意:** ルータのポート開放は絶対にしないでください。

### Webhook JSON テンプレート（固定値版・推奨）

まずは変数展開に依存しない**固定値版**の JSON でテスト送信を行い、通信が成功することを確認してください。
（Uptime Kuma のテンプレート変数はバージョン差があり、最初から変数版を使うと切り分けが難しいためです）

**固定値版 monitor_down 例:**

```json
{
  "source": "uptime-kuma",
  "event_type": "monitor_down",
  "severity": "critical",
  "title": "Uptime Kuma test monitor is DOWN",
  "message": "This is a fixed test payload from Uptime Kuma.",
  "dedup_key": "uptime:test-monitor:down",
  "metadata": {
    "monitor_name": "Uptime Kuma test monitor",
    "test": true
  }
}
```

固定値版が HTTP 201 で成功してから、以下の「変数版」へ進む流れをおすすめします。

### Webhook JSON テンプレート（変数版）

以下のテンプレートは Uptime Kuma の変数を活用する例です。

> **【重要】Webhookテンプレート変数についての注意**
> 上記の `{{ }}` は Uptime Kuma のテンプレート変数です。
> 実際の変数名や送信される JSON の構造は、**Uptime Kuma のバージョンや設定画面のUIによって異なる場合が多々あります**。
> そのため、設定後は**必ず Uptime Kuma 側の「Test」ボタンからテスト通知を送信し、意図した JSON が送られているか（および Notify Hub 側で HTTP 201 や 422 などの応答がどうなるか）を実機で確認してください**。

**変数版 monitor_down (critical) 例:**

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

**変数版 monitor_up (info) 例:**

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

### Test 通知の確認チェックリスト

Uptime Kuma の「Test」ボタンを押した際は、以下を確認してください。

- [ ] Notify Hub 側のレスポンスが HTTP 201 になることを確認する
- [ ] もし 401 なら `X-Notify-Token` が間違っている
- [ ] もし 422 なら JSON body，`source`，`severity`，必須項目のいずれかが不正
- [ ] もし 500 なら Notify Hub のログを確認する
- [ ] Test 後に `http://192.168.11.11:8090/events` を開き、`source=uptime-kuma` のイベントが増えていることを確認する
- [ ] 必要なら以下で確認する：
      `curl -s "http://localhost:8090/api/events?source=uptime-kuma" | python3 -m json.tool`

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

# Uptime Kuma のイベント一覧を表示
./scripts/notify-show-uptime-events.sh

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

**原因:**
`X-Notify-Token` ヘッダーの値と `.env` の `NOTIFY_API_TOKEN` が一致していません。

**対処法:**
Uptime Kuma の Webhook ヘッダを見直してください。

### 422 Unprocessable Entity が返る

**原因:**
JSON形式は届いていますが、Notify Hub の入力バリデーションに失敗しています。

**よくある原因:**
- `source` が `uptime-kuma`, `backup`, `manual`, `system` 以外
- `severity` が `info`, `warning`, `error`, `critical` 以外
- `title` が空
- JSON として壊れている

**対処法:**
- まず「固定値版」の Webhook テンプレートでテスト送信を試してください。
- `docker compose logs --tail=100 notify` で詳細なバリデーションエラーを確認してください。

### 500 Internal Server Error (データベースエラー等)

**原因候補:**
- `data/notify` の権限問題 (例: `sqlite3.OperationalError: attempt to write a readonly database`)
- SQLite DB への書き込み失敗

**対処法:**
1. ログを確認: `docker compose logs --tail=100 notify`
2. 権限を確認: `ls -ln data/notify`
3. 権限を修正 (必要な場合):
   ```bash
   sudo chown -R 20212:20212 data/notify
   sudo chmod -R u+rwX,g+rwX data/notify
   ```
