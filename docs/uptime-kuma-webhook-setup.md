# Uptime Kuma Webhook連携 設定ガイド

## 1. このドキュメントの目的

このドキュメントは，Uptime Kuma の監視結果（UP/DOWN イベント）を Notify Hub に記録するための設定手順を解説する．

> **前提事項:** 本ドキュメントでは，説明のために Raspberry Pi の IP アドレスを `<あなたのラズベリーパイのIPv4アドレス>` という形式で記載している．コマンドや URL に出てくるこの文字列は，実際のラズパイの IPv4 アドレス（`hostname -I` で確認可能）に置き換えて読むこと．

- これはスマホ通知などの外部送信を設定するものではなく，**まずは HomeLab 内の Notify Hub (`/events`) にイベント履歴を記録するための設定**である．
- **ルータのポート開放は不要**である．インターネットに公開する必要はない．絶対に行わないこと．
- Uptime Kuma と Notify Hub は同じ Docker Compose ネットワーク内で動作しているため，Webhook URL にはコンテナ名を使った `http://notify:8090/api/events` を使用する．
- 記録されたイベントの履歴をブラウザから確認するための URL は `http://<あなたのラズベリーパイのIPv4>:8090/events` である．
- 本番運用用の Webhook body は `configs/uptime-kuma/notify-hub-production.json` にも保存している．Uptime Kuma の画面へ貼り付けるときはこのファイルをコピー元にしてよい．

## 2. 全体の通信の流れ

連携の全体像は以下の通りである．

```text
Uptime Kuma
  ↓ Webhook POST
Notify Hub /api/events
  ↓ SQLite 保存
Notify Hub /events
  ↓
ブラウザで履歴確認
```

設定において，以下の **2つの URL の違い** を混同しないように注意すること．

- **監視URL**
  Uptime Kuma が「そのサービスが生きているか」を定期的に見に行くための URL である．
  例： `http://notify:8090/health`
- **Webhook URL**
  Uptime Kuma が「サービスの UP/DOWN の状態変化が起きた」というイベントを Notify Hub に送信するための URL である．
  例： `http://notify:8090/api/events`

## 3. 事前確認

設定を進める前に，Raspberry Pi 側で Notify Hub と Uptime Kuma が正常に稼働しているか確認する．
ターミナルで以下を実行すること．

```bash
cd ~/projects/HomeLab-NOC-v2
git status
docker compose ps
./scripts/notify-status.sh
```

**期待結果:**
- `homelab-notify` と `homelab-uptime-kuma` のステータスが `Up` になっていること
- `./scripts/notify-status.sh` の実行結果が `{"status":"ok","service":"homelab-notify"}` を返すこと

次に，Webhook 認証に必要なトークンを確認する．

```bash
grep NOTIFY_API_TOKEN .env
```
※ **注意:** トークンは秘密情報である．GitHub やスクリーンショットなどで公開しないよう注意すること．

## 4. Uptime KumaでNotify Hub自身を監視する手順

まずは，Uptime Kuma 自身が Notify Hub の死活を監視できるように設定する．（ここではまだ Webhook 通知は設定しない）

1. ブラウザで Uptime Kuma の管理画面を開く．
   URL: `http://<あなたのラズベリーパイのIPv4>:3001`
2. 左上の **「監視の追加 (Add New Monitor)」** をクリックする．
3. 以下の通りに入力する．
   - **監視タイプ (Monitor Type)**: `HTTP(s)`
   - **表示名 (Friendly Name)**: `Notify Hub`
   - **URL**: `http://<あなたのラズベリーパイのIPv4>:8090/health`
   - **監視間隔 (Heartbeat Interval)**: `60` 秒（任意）
4. 画面下の **「保存 (Save)」** をクリックする．
5. ダッシュボードに戻り，ステータスが **UP (緑色)** になることを確認すること．

## 5. Uptime KumaでWebhook通知を作成する手順

次に，イベントが発生した際に Notify Hub へ送信するための Webhook 設定を作成する．

1. 右上のアカウントアイコンから **「設定 (Settings)」** > **「通知 (Notifications)」** を開く．
2. **「通知のセットアップ (Setup Notification)」** をクリックする．
3. 以下の通りに入力する．

   - **通知タイプ (Notification Type)**: `Webhook`
   - **名前 (Friendly Name)**: `Notify Hub Webhook`
   - **Post URL**: `http://notify:8090/api/events`
   - **HTTPメソッド**: `POST`
   - **リクエストボディ (Request Body)**: `カスタムbody (Custom Body)`
   - **追加ヘッダー (Additional Headers)**: オンにする
   - **追加ヘッダーのJSON**:
     ```json
     {
       "Content-Type": "application/json",
       "X-Notify-Token": "<NOTIFY_API_TOKENの値>"
     }
     ```

**【注意点】**
- `<NOTIFY_API_TOKENの値>` の部分は，手順3で確認した `.env` ファイル内の値に置き換えること．
- `Content-Type` を追加ヘッダーに明示することが必須である．
- Post URL は Docker の名前解決を利用する `http://notify:8090/api/events` を優先して使用すること．（もし Docker 内の名前解決に失敗する場合のみ，IP アドレス指定の `http://<あなたのラズベリーパイのIPv4アドレス>:8090/api/events` を試すこと）

## 6. 固定値JSONで疎通テストする手順

Uptime Kuma のテンプレート変数による問題と，通信・認証による問題を切り分けるため，まずは変数を一切使わない**固定値 JSON** でテストを行う．

同じ内容は `configs/uptime-kuma/notify-hub-fixed-test.json` にも保存している．

先ほど作成した Webhook 通知の設定画面で，**「カスタムbody (Custom Body)」** の入力欄に以下の JSON をそのまま貼り付ける．

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

貼り付けたら，画面下部にある **「テスト (Test)」** ボタンを押す．

**成功確認:**
- Uptime Kuma 側の画面右上にエラーが出ず，成功のメッセージが出ること．
- ブラウザで `http://<あなたのラズベリーパイのIPv4>:8090/events` を開き，「Uptime Kuma test monitor is DOWN」というイベントが追加されていること．
- または，ラズパイのターミナルで以下を実行し，イベントが記録されていることを確認する．
  ```bash
  curl -s "http://localhost:8090/api/events?source=uptime-kuma" | python3 -m json.tool
  ```

ここでイベントが確認できれば，Uptime Kuma から Notify Hub への「通信」「認証」「データベースへの保存」はすべて正常に動作している．

## 7. 変数版JSONでテストする手順

固定値でのテストが成功したら，Uptime Kuma が持つ変数を利用した JSON に切り替える．
まずは安全のため，`severity` を `info` に固定した変数確認用 JSON を使用する．

**カスタムbody** を以下の JSON に書き換えること．
同じ内容は `configs/uptime-kuma/notify-hub-variable-check.json` にも保存している．

```json
{
  "source": "uptime-kuma",
  "event_type": "monitor_event",
  "severity": "info",
  "title": "{{ name }} - {{ status }}",
  "message": "{{ msg }}",
  "dedup_key": "uptime:{{ name }}:{{ status }}",
  "metadata": {
    "monitor_name": "{{ name }}",
    "status": "{{ status }}",
    "target": "{{ hostnameOrURL }}"
  }
}
```

**目的:**
- `{{ name }}`
- `{{ status }}`
- `{{ msg }}`
- `{{ hostnameOrURL }}`
これらの変数が，現在使用している Uptime Kuma のバージョンでどのように展開されるかを確認する．

再度 **「テスト (Test)」** ボタンを押し，Notify Hub の `/events` 画面を確認すること．
> **注意:** 通知設定画面からテストボタンを押した場合，対象のモニターが特定できないため，変数部分が `Monitor Name not available` や `⚠️ Test` のようなダミー値として展開されることがある．これは異常ではない．

## 8. 実監視イベントでUP/DOWNを確認する手順

変数がどのように展開されるかを確認できたら，次は実際の「UP」および「DOWN」の状態変化をシミュレーションする．

1. Uptime Kuma のダッシュボードに戻り，新しいモニターを作成する．
   - **監視タイプ**: `HTTP(s)`
   - **表示名**: `Webhook Dummy Down Test`
   - **URL**: `http://notify:8090/health`
   - **通知 (Notifications)**: 作成した「Notify Hub Webhook」をオンにする
2. 保存し，ステータスが **UP** になることを確認する．
   （※新規作成時など，設定直後に UP のイベントが送信される場合がある）
3. 意図的にエラーを起こすため，このモニターを編集し **URL** を以下のように存在しないパスに変更して保存する．
   `http://notify:8090/force-down-test`
4. Uptime Kuma が 404 エラーを検知し，ステータスが **DOWN** になるのを待つ．（Notify Hub 自体が壊れる操作ではなく，安全なテストである）
5. `http://<あなたのラズベリーパイのIPv4>:8090/events` を開き，以下のようなイベントが表示されることを確認する．
   例: `Webhook Dummy Down Test - 🔴 Down`
6. 確認できたら，モニターの URL を `http://notify:8090/health` に戻し，今度は UP への復旧イベントが記録されることを確認すること．

## 9. 最終運用用JSON

実機での変数展開が確認できたら，最後に「ステータスに応じて event_type と severity を自動で切り替える」本番運用用の JSON を設定する．
（この環境において動作確認済みの基本形である．Uptime Kuma のバージョンによって挙動が変わる可能性があるため注意すること）

**カスタムbody** を以下に変更し，Webhook 設定を保存すること．
同じ内容は `configs/uptime-kuma/notify-hub-production.json` にも保存している．

```json
{
  "source": "uptime-kuma",
  "event_type": "{% if status contains 'Down' %}monitor_down{% elsif status contains 'Up' %}monitor_up{% else %}monitor_event{% endif %}",
  "severity": "{% if status contains 'Down' %}critical{% elsif status contains 'Up' %}info{% else %}warning{% endif %}",
  "title": "{{ name }} - {{ status }}",
  "message": "{{ msg }}",
  "dedup_key": "uptime:{{ name }}:{{ status }}",
  "metadata": {
    "monitor_name": "{{ name }}",
    "status": "{{ status }}",
    "target": "{{ hostnameOrURL }}"
  }
}
```

**JSON の意味:**
- `status` の文字列表記に "Down" が含まれる場合: `event_type` を `monitor_down`，`severity` を `critical` とする．
- `status` の文字列表記に "Up" が含まれる場合: `event_type` を `monitor_up`，`severity` を `info` とする．
- それ以外の場合: `event_type` を `monitor_event`，`severity` を `warning` とする．

> **注意:** Uptime Kuma のバージョンによって `status` 変数に格納される文字列表記が変わる可能性がある．設定後は，手順 8 と同じようにダミーモニターを使って意図通りに UP/DOWN が判定されるか必ず実機で確認すること．

## 10. 既存モニターにWebhookを有効化するときの注意

### 推奨する初期モニター

最初は以下の監視対象だけに絞ると切り分けしやすい．

| 表示名 | 監視タイプ | 監視先 | DOWN時 severity | 備考 |
|--------|------------|--------|-----------------|------|
| Notify Hub | HTTP(s) | `http://notify:8090/health` | `critical` | Notify Hub 自身が落ちると webhook を受けられない場合がある |
| Portal | HTTP(s) | `http://portal/` | `critical` | 利用入口の監視 |
| Pi-hole Web | HTTP(s) | `http://pihole/admin` | `critical` | Pi-hole 管理画面の監視 |
| Pi-hole DNS | DNS | `pihole` または `<ラズパイIP>` | `critical` | DNS を家全体へ配る前に必ず確認 |
| Uptime Kuma | HTTP(s) | `http://uptime-kuma:3001` | `warning` | Uptime Kuma 自身の異常は Notify Hub へ送れない場合がある |

外部通知は Notify Hub 側の `NOTIFY_SEVERITIES` で制御する．初期値は `critical,error` なので，DOWN は ntfy 通知，UP は履歴記録のみになる．

Webhook の設定が完了したら，監視対象の各モニターに Webhook を紐付ける必要がある．

- Webhook 通知の設定を作成しただけでは，既存のモニターには自動で紐付かない．
- **各モニターの編集画面を開き，「通知 (Notifications)」の項目で Notify Hub Webhook をオンにして保存** する必要がある．
- Webhook をオンにしても，**実際にイベントが送信されるのは対象の UP/DOWN の「状態変化」が起きた時**である．
- したがって，現在 UP のまま安定稼働している監視対象に Webhook をオンにしても，すぐには Notify Hub のイベント一覧には追加されない．

## 11. トラブルシューティング

### /events 画面にイベントが出ない
- 対象のモニター編集画面で，Notify Hub Webhook が「オン」になっているか確認すること．
- 変更後に「保存」を押したか確認すること．
- 対象モニターで実際に UP/DOWN の状態変化が起きているか（Uptime Kuma のダッシュボード上で）確認すること．
- ターミナルで `docker compose logs --tail=100 notify` を実行し，受信エラーが出ていないか確認すること．

### 401 Unauthorized が返る
- `X-Notify-Token` の値が，`.env` ファイルの `NOTIFY_API_TOKEN` と一致していない．
- 追加ヘッダーの JSON 形式自体が `{ ... }` として正しくない（壊れている）可能性がある．

### 422 Unprocessable Entity が返る
- 送信された JSON の形式が壊れている．
- または，JSON は届いているが， Notify Hub のバリデーション（入力規則）に失敗している．
  - `source` が `uptime-kuma`, `backup`, `manual`, `system` 以外になっていないか
  - `severity` が `info`, `warning`, `error`, `critical` 以外になっていないか
  - `title` が空になっていないか
- カスタム body が単なるテキストとして送られている場合がある．追加ヘッダーに `"Content-Type": "application/json"` が含まれているか確認すること．

### 500 Internal Server Error が返る
- SQLite データベースへの書き込み権限がない可能性がある．
- ターミナルで `docker compose logs --tail=100 notify` を実行すること．
- もし `sqlite3.OperationalError: attempt to write a readonly database` が出ている場合は，以下のコマンドで権限を修正すること．
  ```bash
  ls -ln data/notify
  sudo chown -R 20212:20212 data/notify
  ```

### Post URL `http://notify:8090/api/events` で届かない
- Uptime Kuma と Notify Hub が同じ Docker Compose ネットワーク内にいない可能性がある．
- ターミナルで `docker compose ps` を実行し，両方が正常に起動しているか確認すること．
- 原因がわからない場合の代替策として，IP を直接指定する `http://<あなたのラズベリーパイのIPv4>:8090/api/events` に変更して届くか試すこと．

## 12. 設定はどこに保存されるか

プロジェクトのデータ管理方針について理解しておくこと．

- Uptime Kuma の設定（GUI で作成したモニターや Webhook 等）は `data/uptime-kuma/` に保存される．
- Notify Hub のイベント履歴（データベース）は `data/notify/notify.db` に保存される．
- トークンなどが書かれた `.env` はローカルの設定および秘密情報である．
- **これらはすべて Git リポジトリには登録（コミット）されない（Git の管理対象外である）．**
- Git に登録されるのは，`docker-compose.yml`，`scripts/` ディレクトリ，`services/notify/` ディレクトリ，ドキュメント (`docs/` や `README.md`) などの「コードと説明」のみである．

**【Git に入れないもの】**
- `.env`
- `data/`
- `data/uptime-kuma/`
- `data/notify/notify.db`
- `secrets/`
- `backups/`
