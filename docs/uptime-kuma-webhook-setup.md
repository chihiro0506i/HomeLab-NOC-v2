# Uptime Kuma Webhook連携 設定ガイド

## 1. このドキュメントの目的

このドキュメントは、Uptime Kuma の監視結果（UP/DOWN イベント）を Notify Hub に記録するための設定手順を解説します。

- これはスマホ通知などの外部送信を設定するものではなく、**まずは HomeLab 内の Notify Hub (`/events`) にイベント履歴を記録するための設定**です。
- **ルータのポート開放は不要**です。インターネットに公開する必要はありません。絶対に行わないでください。
- Uptime Kuma と Notify Hub は同じ Docker Compose ネットワーク内で動作しているため、Webhook URL にはコンテナ名を使った `http://notify:8090/api/events` を使用します。
- 記録されたイベントの履歴をブラウザから確認するための URL は `http://192.168.11.11:8090/events` です。

## 2. 全体の通信の流れ

連携の全体像は以下の通りです。

```text
Uptime Kuma
  ↓ Webhook POST
Notify Hub /api/events
  ↓ SQLite 保存
Notify Hub /events
  ↓
ブラウザで履歴確認
```

設定において、以下の **2つの URL の違い** を混同しないように注意してください。

- **監視URL**
  Uptime Kuma が「そのサービスが生きているか」を定期的に見に行くための URL です。
  例： `http://notify:8090/health`
- **Webhook URL**
  Uptime Kuma が「サービスの UP/DOWN の状態変化が起きた」というイベントを Notify Hub に送信するための URL です。
  例： `http://notify:8090/api/events`

## 3. 事前確認

設定を進める前に、Raspberry Pi 側で Notify Hub と Uptime Kuma が正常に稼働しているか確認します。
ターミナルで以下を実行してください。

```bash
cd ~/projects/HomeLab-NOC-v2
git status
docker compose ps
./scripts/notify-status.sh
```

**期待結果:**
- `homelab-notify` と `homelab-uptime-kuma` のステータスが `Up` になっていること
- `./scripts/notify-status.sh` の実行結果が `{"status":"ok","service":"homelab-notify"}` を返すこと

次に、Webhook 認証に必要なトークンを確認します。

```bash
grep NOTIFY_API_TOKEN .env
```
※ **注意:** トークンは秘密情報です。GitHub やスクリーンショットなどで公開しないよう注意してください。

## 4. Uptime KumaでNotify Hub自身を監視する手順

まずは、Uptime Kuma 自身が Notify Hub の死活を監視できるように設定します。（ここではまだ Webhook 通知は設定しません）

1. ブラウザで Uptime Kuma の管理画面を開きます。
   URL: `http://192.168.11.11:3001`
2. 左上の **「監視の追加 (Add New Monitor)」** をクリックします。
3. 以下の通りに入力します。
   - **監視タイプ (Monitor Type)**: `HTTP(s)`
   - **表示名 (Friendly Name)**: `Notify Hub`
   - **URL**: `http://192.168.11.11:8090/health`
   - **監視間隔 (Heartbeat Interval)**: `60` 秒（任意）
4. 画面下の **「保存 (Save)」** をクリックします。
5. ダッシュボードに戻り、ステータスが **UP (緑色)** になることを確認してください。

## 5. Uptime KumaでWebhook通知を作成する手順

次に、イベントが発生した際に Notify Hub へ送信するための Webhook 設定を作成します。

1. 右上のアカウントアイコンから **「設定 (Settings)」** > **「通知 (Notifications)」** を開きます。
2. **「通知のセットアップ (Setup Notification)」** をクリックします。
3. 以下の通りに入力します。

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
- `<NOTIFY_API_TOKENの値>` の部分は、手順3で確認した `.env` ファイル内の値に置き換えてください。
- `Content-Type` を追加ヘッダーに明示することが必須です。
- Post URL は Docker の名前解決を利用する `http://notify:8090/api/events` を優先して使用してください。（もし Docker 内の名前解決に失敗する場合のみ、IP アドレス指定の `http://192.168.11.11:8090/api/events` を試してください）

## 6. 固定値JSONで疎通テストする手順

Uptime Kuma のテンプレート変数による問題と、通信・認証による問題を切り分けるため、まずは変数を一切使わない**固定値 JSON** でテストを行います。

先ほど作成した Webhook 通知の設定画面で、**「カスタムbody (Custom Body)」** の入力欄に以下の JSON をそのまま貼り付けます。

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

貼り付けたら、画面下部にある **「テスト (Test)」** ボタンを押します。

**成功確認:**
- Uptime Kuma 側の画面右上にエラーが出ず、成功のメッセージが出ること。
- ブラウザで `http://192.168.11.11:8090/events` を開き、「Uptime Kuma test monitor is DOWN」というイベントが追加されていること。
- または、ラズパイのターミナルで以下を実行し、イベントが記録されていることを確認します。
  ```bash
  curl -s "http://localhost:8090/api/events?source=uptime-kuma" | python3 -m json.tool
  ```

ここでイベントが確認できれば、Uptime Kuma から Notify Hub への「通信」「認証」「データベースへの保存」はすべて正常に動作しています。

## 7. 変数版JSONでテストする手順

固定値でのテストが成功したら、Uptime Kuma が持つ変数を利用した JSON に切り替えます。
まずは安全のため、`severity` を `info` に固定した変数確認用 JSON を使用します。

**カスタムbody** を以下の JSON に書き換えてください。

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
これらの変数が、現在使用している Uptime Kuma のバージョンでどのように展開されるかを確認します。

再度 **「テスト (Test)」** ボタンを押し、Notify Hub の `/events` 画面を確認してください。
> **注意:** 通知設定画面からテストボタンを押した場合、対象のモニターが特定できないため、変数部分が `Monitor Name not available` や `⚠️ Test` のようなダミー値として展開されることがあります。これは異常ではありません。

## 8. 実監視イベントでUP/DOWNを確認する手順

変数がどのように展開されるかを確認できたら、次は実際の「UP」および「DOWN」の状態変化をシミュレーションします。

1. Uptime Kuma のダッシュボードに戻り、新しいモニターを作成します。
   - **監視タイプ**: `HTTP(s)`
   - **表示名**: `Webhook Dummy Down Test`
   - **URL**: `http://notify:8090/health`
   - **通知 (Notifications)**: 作成した「Notify Hub Webhook」をオンにする
2. 保存し、ステータスが **UP** になることを確認します。
   （※新規作成時など、設定直後に UP のイベントが送信される場合があります）
3. 意図的にエラーを起こすため、このモニターを編集し **URL** を以下のように存在しないパスに変更して保存します。
   `http://notify:8090/force-down-test`
4. Uptime Kuma が 404 エラーを検知し、ステータスが **DOWN** になるのを待ちます。（Notify Hub 自体が壊れる操作ではなく、安全なテストです）
5. `http://192.168.11.11:8090/events` を開き、以下のようなイベントが表示されることを確認します。
   例: `Webhook Dummy Down Test - 🔴 Down`
6. 確認できたら、モニターの URL を `http://notify:8090/health` に戻し、今度は UP への復旧イベントが記録されることを確認してください。

## 9. 最終運用用JSON

実機での変数展開が確認できたら、最後に「ステータスに応じて event_type と severity を自動で切り替える」本番運用用の JSON を設定します。
（現在実機で動作確認が取れている基本形です）

**カスタムbody** を以下に変更し、Webhook 設定を保存してください。

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
- `status` の文字列表記に "Down" が含まれる場合: `event_type` を `monitor_down`、`severity` を `critical` とする。
- `status` の文字列表記に "Up" が含まれる場合: `event_type` を `monitor_up`、`severity` を `info` とする。
- それ以外の場合: `event_type` を `monitor_event`、`severity` を `warning` とする。

> **注意:** Uptime Kuma のバージョンによって `status` 変数に格納される文字列表記が変わる可能性があります。設定後は、手順 8 と同じようにダミーモニターを使って意図通りに UP/DOWN が判定されるか必ず実機で確認してください。

## 10. 既存モニターにWebhookを有効化するときの注意

Webhook の設定が完了したら、監視対象の各モニターに Webhook を紐付ける必要があります。

- Webhook 通知の設定を作成しただけでは、既存のモニターには自動で紐付きません。
- **各モニターの編集画面を開き、「通知 (Notifications)」の項目で Notify Hub Webhook をオンにして保存** する必要があります。
- Webhook をオンにしても、**実際にイベントが送信されるのは対象の UP/DOWN の「状態変化」が起きた時**です。
- したがって、現在 UP のまま安定稼働している監視対象に Webhook をオンにしても、すぐには Notify Hub のイベント一覧には追加されません。

## 11. トラブルシューティング

### /events 画面にイベントが出ない
- 対象のモニター編集画面で、Notify Hub Webhook が「オン」になっているか確認してください。
- 変更後に「保存」を押したか確認してください。
- 対象モニターで実際に UP/DOWN の状態変化が起きているか（Uptime Kuma のダッシュボード上で）確認してください。
- ターミナルで `docker compose logs --tail=100 notify` を実行し、受信エラーが出ていないか確認してください。

### 401 Unauthorized が返る
- `X-Notify-Token` の値が、`.env` ファイルの `NOTIFY_API_TOKEN` と一致していません。
- 追加ヘッダーの JSON 形式自体が `{ ... }` として正しくない（壊れている）可能性があります。

### 422 Unprocessable Entity が返る
- 送信された JSON の形式が壊れています。
- または、JSON は届いていますが Notify Hub のバリデーション（入力規則）に失敗しています。
  - `source` が `uptime-kuma`, `backup`, `manual`, `system` 以外になっていないか
  - `severity` が `info`, `warning`, `error`, `critical` 以外になっていないか
  - `title` が空になっていないか
- カスタム body が単なるテキストとして送られている場合があります。追加ヘッダーに `"Content-Type": "application/json"` が含まれているか確認してください。

### 500 Internal Server Error が返る
- SQLite データベースへの書き込み権限がない可能性があります。
- ターミナルで `docker compose logs --tail=100 notify` を実行してください。
- もし `sqlite3.OperationalError: attempt to write a readonly database` が出ている場合は、以下のコマンドで権限を修正してください。
  ```bash
  ls -ln data/notify
  sudo chown -R 20212:20212 data/notify
  ```

### Post URL `http://notify:8090/api/events` で届かない
- Uptime Kuma と Notify Hub が同じ Docker Compose ネットワーク内にいない可能性があります。
- ターミナルで `docker compose ps` を実行し、両方が正常に起動しているか確認してください。
- 原因がわからない場合の代替策として、IP を直接指定する `http://192.168.11.11:8090/api/events` に変更して届くか試してください。

## 12. 設定はどこに保存されるか

プロジェクトのデータ管理方針について理解しておきましょう。

- Uptime Kuma の設定（GUI で作成したモニターや Webhook 等）は `data/uptime-kuma/` に保存されます。
- Notify Hub のイベント履歴（データベース）は `data/notify/notify.db` に保存されます。
- トークンなどが書かれた `.env` はローカルの設定および秘密情報です。
- **これらはすべて Git リポジトリには登録（コミット）されません（Git の管理対象外です）。**
- Git に登録されるのは、`docker-compose.yml`、`scripts/` ディレクトリ、`services/notify/` ディレクトリ、ドキュメント (`docs/` や `README.md`) などの「コードと説明」のみです。

**【Git に入れないもの】**
- `.env`
- `data/`
- `data/uptime-kuma/`
- `data/notify/notify.db`
- `secrets/`
- `backups/`
