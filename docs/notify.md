# Notify Hub

HomeLab-NOC-v2 のサブプロジェクトとして動作するイベント集約サービスである．
FastAPI + SQLite で構成され，Uptime Kuma やバックアップスクリプトなどからのイベントを受信・保存し，Web ダッシュボードで履歴を閲覧できる．
ntfy を設定すると，重要度の高いイベントだけを外部通知へ送信できる．

> **備考:** DB 内には通知送信履歴用の `notifications` と，将来の設定保存用の `settings` が存在する．

## 起動方法

```bash
# 初回のみ
./scripts/setup.sh

# .env を編集して NOTIFY_API_TOKEN を設定
nano .env

# 起動
./scripts/start.sh
```

Notify Hub は `docker compose up -d` で他のサービスと一緒に起動する．

### アクセス

```
http://<RaspberryPi-IP>:8090
```

## 設定項目（.env）

| 変数 | デフォルト | 説明 |
|------|-----------|------|
| `NOTIFY_PORT` | `8090` | Notify Hub のポート |
| `NOTIFY_API_TOKEN` | — | API 認証トークン（必須．初期値から変更すること） |
| `NOTIFY_OUTBOUND_ENABLED` | `true` | 外部通知を試行するかどうか |
| `NOTIFY_SEVERITIES` | `critical,error` | 外部通知対象の severity。カンマ区切り |
| `NOTIFY_DEDUP_WINDOW_SECONDS` | `900` | 同じ `dedup_key` の再通知を抑制する秒数。`0` で無効 |
| `NOTIFY_NTFY_URL` | — | ntfy の投稿 URL。空なら外部通知しない |
| `NOTIFY_NTFY_TOKEN` | — | ntfy 認証トークン。不要な場合は空 |
| `NOTIFY_HTTP_TIMEOUT_SECONDS` | `5` | 外部通知 HTTP タイムアウト秒数 |

### ntfy 通知の有効化

`.env` に `NOTIFY_NTFY_URL` を設定すると，`NOTIFY_SEVERITIES` に含まれるイベントだけが ntfy へ送信される．

```bash
NOTIFY_OUTBOUND_ENABLED=true
NOTIFY_SEVERITIES=critical,error
NOTIFY_DEDUP_WINDOW_SECONDS=900
NOTIFY_NTFY_URL=https://ntfy.sh/your-private-topic
NOTIFY_NTFY_TOKEN=
```

認証つき ntfy を使う場合は，`NOTIFY_NTFY_TOKEN` に Bearer token を設定する．

外部通知に失敗しても，イベント保存自体は成功する．送信結果はイベント一覧の `Notify Status` と DB の `notifications` テーブルに保存される．

主なステータス:

- `sent` — 外部通知の送信に成功
- `failed` — 外部通知に失敗
- `deduplicated` — 同じ `dedup_key` の通知が直近に送信済みのため抑制
- `unconfigured` — 通知対象 severity だが `NOTIFY_NTFY_URL` が未設定
- `disabled` — `NOTIFY_OUTBOUND_ENABLED=false`
- `not_applicable` — 通知対象ではない severity

## API リファレンス

### GET /health

Uptime Kuma で監視するためのヘルスチェックエンドポイントである．

```json
{"status": "ok", "service": "homelab-notify"}
```

### POST /api/events

イベントを受信して SQLite に保存する．
`X-Notify-Token` ヘッダーが必須である．

`severity` は `info`，`warning`，`error`，`critical` のいずれかである．
それ以外の値を送ると 422 Unprocessable Entity が返る．

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
    "target": "<RaspberryPi-IP>:53"
  }
}
```

**レスポンス例:**

```json
{"status": "stored", "event_id": 123, "notified": true}
```

### GET /api/events

保存済みイベントを JSON で返す．

クエリパラメータ:
- `limit` — 件数上限（デフォルト 100）
- `source` — フィルタ（例: `uptime-kuma`，`backup`）
- `severity` — フィルタ（例: `critical`，`error`）

### POST /api/test-notification

テストイベントを作成する．`X-Notify-Token` ヘッダーが必須である．

## Uptime Kuma Webhook 連携

Uptime Kuma の監視結果を Notify Hub に Webhook で送信し，イベントとして記録する仕組みである．
これにより，サービスの障害・復旧イベントを Notify Hub のダッシュボードで一覧確認できる．

> **詳細設定手順**: 初心者向けの詳しい設定ステップは，[Uptime Kuma Webhook連携 設定手順](uptime-kuma-webhook-setup.md) を参照すること．

### 設定手順 (1) Notify Hub 自身の監視

まず，Uptime Kuma に Notify Hub 自体の監視 (HTTP) を追加することを推奨する．
- **監視URL例**: `http://<RaspberryPi-IP>:8090/health`
- **Method**: GET

### 設定手順 (2) Webhook 通知の作成

次に，Uptime Kuma の「通知」設定から **Webhook** を追加し，以下の通り設定する．

- **URL**:
  - Docker Compose 内から Notify Hub へ送る場合: `http://notify:8090/api/events`
  - LAN IP 経由で送る場合: `http://<RaspberryPi-IP>:8090/api/events`
- **Method**: `POST`
- **Content-Type**: `application/json`
- **Custom Headers**:
  ```
  X-Notify-Token: <NOTIFY_API_TOKEN の値>
  ```
  ※ `.env` の `NOTIFY_API_TOKEN` と一致させること．

> **注意:** ルータのポート開放は絶対に行わないこと．

### Webhook JSON テンプレート（固定値版・推奨）

まずは変数展開に依存しない**固定値版**の JSON でテスト送信を行い，通信が成功することを確認すること．
（Uptime Kuma のテンプレート変数はバージョン差があり，最初から変数版を使うと切り分けが難しいためである）

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

固定値版が HTTP 201 で成功してから，「変数版」へ進む流れを推奨する．

### Webhook JSON テンプレート（変数版）

> **【重要】実運用では [`docs/uptime-kuma-webhook-setup.md`](uptime-kuma-webhook-setup.md) の「9. 最終運用用JSON」を使用すること．**
> あちらが，この環境で動作確認済みの UP/DOWN 切り替え対応 JSON である．

以下の `monitorJSON.name` / `monitorJSON.url` を使う例は，Uptime Kuma のバージョンによっては展開されない場合がある別例として残しておく．

> **【注意】** `{{ }}` は Uptime Kuma のテンプレート変数である．
> 実際の変数名や送信される JSON の構造は，**Uptime Kuma のバージョンや設定画面の UI によって異なる場合が多い**．
> 設定後は**必ず「Test」ボタンからテスト通知を送信し，意図した JSON が届いているか実機で確認すること**．

**変数版 monitor_down (critical) 例（バージョン依存あり）:**

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

**変数版 monitor_up (info) 例（バージョン依存あり）:**

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

Uptime Kuma の「Test」ボタンを押した際は，以下を確認すること．

- [ ] Notify Hub 側のレスポンスが HTTP 201 になることを確認する
- [ ] もし 401 なら `X-Notify-Token` が間違っている
- [ ] もし 422 なら JSON body，`source`，`severity`，必須項目のいずれかが不正
- [ ] もし 500 なら Notify Hub のログを確認する
- [ ] Test 後に `http://<RaspberryPi-IP>:8090/events` を開き，`source=uptime-kuma` のイベントが増えていることを確認する
- [ ] 必要なら以下で確認する：
      `curl -s "http://localhost:8090/api/events?source=uptime-kuma" | python3 -m json.tool`

## イベント設計

Notify Hub に記録する主なイベントの設計である．

| モニター対象 | source | event_type | severity | 方針 |
|-------------|--------|-----------|----------|------|
| Pi-hole DNS down | `uptime-kuma` | `monitor_down` | `critical` | 将来の通知対象 |
| Pi-hole DNS up | `uptime-kuma` | `monitor_up` | `info` | 記録のみ |
| Portal down | `uptime-kuma` | `monitor_down` | `warning` | 記録のみ |
| NetAlertX down | `uptime-kuma` | `monitor_down` | `warning` | 記録のみ |
| Notify Hub down | `uptime-kuma` | `monitor_down` | `warning` | Uptime Kuma 側で検知．Notify Hub 自身には送れない可能性がある |

> **備考:** Notify Hub 自身の障害は，Uptime Kuma が `/health` の応答失敗を検知する．
> その通知を Notify Hub に Webhook で送っても受信できない場合がある．
> Notify Hub の死活は Uptime Kuma のダッシュボードで直接確認すること．

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

Windows 上での開発後，以下の手順でラズパイ上で動作確認を行うこと．

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

- **インターネットに公開しないこと**
- ルータのポート開放は行わないこと
- `NOTIFY_API_TOKEN` は初期値から必ず変更すること
- 公開 ntfy topic を使う場合は，推測されにくい topic 名にすること
- `.env`，`data/` は Git 管理に含めないこと

## トラブルシューティング

### Notify Hub が起動しない

```bash
docker compose logs notify
```

### 401 Unauthorized が返る

**原因:**
`X-Notify-Token` ヘッダーの値と `.env` の `NOTIFY_API_TOKEN` が一致していない．

**対処法:**
Uptime Kuma の Webhook ヘッダを見直すこと．

### 422 Unprocessable Entity が返る

**原因:**
JSON 形式は届いているが，Notify Hub の入力バリデーションに失敗している．

**よくある原因:**
- `source` が `uptime-kuma`，`backup`，`manual`，`system` 以外
- `severity` が `info`，`warning`，`error`，`critical` 以外
- `title` が空
- JSON として壊れている

**対処法:**
- まず「固定値版」の Webhook テンプレートでテスト送信を試すこと．
- `docker compose logs --tail=100 notify` で詳細なバリデーションエラーを確認すること．

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
