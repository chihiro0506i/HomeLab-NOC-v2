# homelab-noc v2

Raspberry Pi 5 を，自宅ネットワークの「小さな監視センター」として使うための Docker Compose プロジェクトです．

このプロジェクトは，Pi-hole，Unbound，NetAlertX，Uptime Kuma，Portal をまとめて起動します．最初から家全体の DNS を変更するのではなく，まずはラズパイ上で画面を確認し，次に自分の端末だけ Pi-hole を試し，最後に必要なら家全体へ広げる，という安全な段階導入を前提にしています．

## 何を作るプロジェクトか

このプロジェクトで作るものは，次のようなホームラボです．

```text
Raspberry Pi 5
  ├─ Portal      : 管理画面への入口
  ├─ Pi-hole     : DNS広告・トラッカーブロック
  ├─ Unbound     : Pi-hole用のローカル再帰DNS
  ├─ NetAlertX   : LAN内端末の検出・一覧化
  └─ Uptime Kuma : サービス死活監視
```

DNS の流れは，基本的に次のようになります．

```text
PC / iPhone / iPad
  ↓ DNS問い合わせ
Pi-hole
  ↓ 許可された問い合わせだけ転送
Unbound
  ↓ 必要に応じてDNS階層へ問い合わせ
インターネット上の権威DNSサーバ群
```

Unbound を使っても，インターネット上の名前を解決する以上，完全に外部通信ゼロにはなりません．ただし，Google DNS や Cloudflare DNS などの特定の外部DNS事業者に問い合わせ履歴をまとめて渡す構成ではなくなります．

## 最初に大事な注意

このプロジェクトは，起動するだけなら家全体のインターネット設定を勝手に変えません．危なくなりやすいのは，次のような操作をしたときです．

```text
危険な操作
・ルータのDNS設定をいきなりラズパイに向ける
・ルータで 53，8080，8081，20211，3001 番ポートを外部公開する
・自分が管理していないネットワークで NetAlertX を動かす
・.env や data/ を GitHub に公開する
・初期パスワードのまま使う
```

特に，DNSサーバや管理画面をインターネットに直接公開してはいけません．自宅LAN内だけで使ってください．外出先から見たい場合は，ポート開放ではなく Tailscale や WireGuard などの VPN を使う方針にしてください．

## 必要なもの

```text
ハードウェア
・Raspberry Pi 5
・安定した電源
・microSD または SSD / NVMe
・有線LAN推奨

ソフトウェア
・Raspberry Pi OS 64-bit
・Docker
・Docker Compose Plugin
```

Docker が未導入の場合は，まず公式手順に従って Docker を導入してください．このプロジェクトの `scripts/setup.sh` は Docker の存在確認はしますが，勝手に Docker をインストールする設計にはしていません．

## 使い方

ラズパイにディレクトリを置きます．

```bash
cd homelab-noc-v2
```

初期セットアップを実行します．

```bash
./scripts/setup.sh
```

`.env` を編集します．特に `PIHOLE_PASSWORD` は必ず変更してください．

```bash
nano .env
```

起動前チェックを実行します．

```bash
./scripts/preflight.sh
```

起動します．

```bash
./scripts/start.sh
```

起動後，ラズパイのIPアドレスが `192.168.1.50` なら，ブラウザで次にアクセスします．

```text
Portal      : http://192.168.1.50:8080
Pi-hole     : http://192.168.1.50:8081/admin
NetAlertX   : http://192.168.1.50:20211
Uptime Kuma : http://192.168.1.50:3001
```

ラズパイのIPアドレスは，次で確認できます．

```bash
hostname -I
```

## 安全な導入順序

最初は，家全体のDNSを変更しないでください．次の順番で進めます．

```text
Phase 1: 起動確認
  ・Portal，Pi-hole，NetAlertX，Uptime Kuma が開けるか確認する
  ・ルータや端末のDNS設定はまだ変えない

Phase 2: ローカル監視
  ・Uptime Kuma で Portal や Pi-hole のURLを監視する
  ・NetAlertX で自宅LAN内の端末を確認する
  ・外部通知はまだ設定しない

Phase 3: 自分の端末だけ Pi-hole を試す
  ・Windows PC だけ DNS をラズパイIPへ向ける
  ・Pi-hole の Query Log を確認する
  ・問題があれば Windows の DNS 設定を自動に戻す

Phase 4: 必要なら家全体へ広げる
  ・ルータの DHCP で DNS としてラズパイIPを配布する
  ・ラズパイ停止時に名前解決できなくなる可能性を理解してから行う
```

## 主なコマンド

```bash
./scripts/setup.sh          # 初期ディレクトリ作成と .env 作成
./scripts/preflight.sh      # ポート競合や設定ミスの確認
./scripts/start.sh          # 起動
./scripts/stop.sh           # 停止
./scripts/restart.sh        # 再起動
./scripts/status.sh         # 状態確認
./scripts/logs.sh           # ログ確認
./scripts/show-urls.sh      # アクセスURL表示
./scripts/check-dns.sh      # Pi-hole / Unbound のDNS動作確認
./scripts/backup.sh         # 設定とデータのバックアップ
./scripts/update.sh         # イメージ更新と再起動
./scripts/offline-export.sh # Dockerイメージを tar.gz に保存
./scripts/offline-import.sh # 保存済みDockerイメージを読み込み
```

## フォルダ構成

```text
homelab-noc-v2/
├── docker-compose.yml
├── .env.example
├── .gitignore
├── LICENSE
├── README.md
├── portal/
├── services/
│   └── unbound/
├── configs/
│   └── unbound/
├── scripts/
├── docs/
├── data/
├── backups/
└── images/
```

`data/`，`backups/`，`images/`，`.env` は GitHub に公開しないでください．

## OSSについて

このプロジェクトは，複数のOSSを組み合わせるテンプレートです．Pi-hole，NetAlertX，Uptime Kuma などの本体コードをこのzip内に同梱しているわけではありません．初回起動時に Docker が各イメージを取得します．

このテンプレート部分，つまり `docker-compose.yml`，`portal/`，`scripts/`，`docs/` は MIT License としています．ただし，各OSS本体にはそれぞれのライセンスがあります．詳しくは `docs/references.md` を確認してください．

## 動作確認について

家庭用ルータとの組み合わせまでは環境依存があるため，必ず `./scripts/preflight.sh` から始めてください．
